"""CLI for warehouse Google Maps enrichment.

Example:
    python enrich_google_maps.py --limit 500 --workers 10
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from config import BASE_DIR, ScraperConfig
from google_maps_enrichment import (
    EnrichmentRepository,
    ProxyRateLimiter,
    ThrottleController,
    format_summary,
    run_maps_worker,
    run_website_worker,
)
from captcha_handler import CaptchaHandler
from proxy_manager import ProxyManager


WORKSPACE_DIR = BASE_DIR.parent
DEFAULT_MIGRATION = WORKSPACE_DIR / "Lead Warehouse" / "postgres" / "003_google_maps_enrichment.sql"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich qualified no-website, yes-email leads from Google Maps."
    )
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--workers-per-proxy", type=int, default=3)
    parser.add_argument("--website-workers", type=int, default=30)
    parser.add_argument("--website-workers-per-proxy", type=int, default=3)
    parser.add_argument("--postgres-pool-size", type=int, default=25)
    parser.add_argument("--database", default="lead_warehouse")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--website-timeout", type=float, default=3.0)
    parser.add_argument("--website-max-attempts", type=int, default=1)
    parser.add_argument("--maps-rps-per-proxy", type=float, default=3.0)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=10, help="Batch claim size from database queue.")
    parser.add_argument("--hard-throttle-window", type=int, default=100)
    parser.add_argument("--hard-throttle-min-events", type=int, default=30)
    parser.add_argument("--monitor-interval", type=float, default=2.0)
    parser.add_argument("--hard-throttle-rate", type=float, default=0.35)
    parser.add_argument("--hard-throttle-consecutive", type=int, default=15)
    parser.add_argument("--review-api-key-env", default="GOOGLE_MAPS_API_KEY")
    parser.add_argument("--resume-run", type=uuid.UUID)
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="With --resume-run, put failed rows back into the queue.",
    )
    parser.add_argument(
        "--backfill-reviews",
        action="store_true",
        help="With --resume-run, requeue matched rows missing review metadata.",
    )
    parser.add_argument("--processes", type=int, default=1, help="Number of OS worker processes (default: 1).")
    parser.add_argument("--child-run", type=uuid.UUID, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--worker-offset", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--migration", type=Path, default=DEFAULT_MIGRATION)
    parser.add_argument("--no-migrate", action="store_true")
    return parser.parse_args()


def database_connection_kwargs(database: str) -> dict[str, Any]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "gmaps_scraper"),
        "password": os.getenv("POSTGRES_PASSWORD", "gmaps_scraper"),
        "dbname": database,
        "connect_timeout": 15,
        "application_name": "google_maps_enrichment",
    }


def apply_migration(connection_kwargs: dict[str, Any], migration: Path) -> None:
    if not migration.is_file():
        raise FileNotFoundError(f"Migration does not exist: {migration}")
    with psycopg.connect(**connection_kwargs) as connection:
        connection.execute(migration.read_text(encoding="utf-8"))

def format_progress_line(progress: dict[str, Any], total: int, elapsed: float) -> str:
    statuses = progress.get("statuses", {})
    matched = statuses.get("matched", 0)
    not_found = statuses.get("not_found", 0)
    failed = statuses.get("failed", 0)
    in_progress = statuses.get("in_progress", 0)
    queued = statuses.get("queued", 0)
    done = matched + not_found + failed
    pct = (done / total * 100) if total > 0 else 0.0
    rate = (done / elapsed) if elapsed > 0 else 0.0

    web_statuses = progress.get("website_statuses", {})
    no_web = web_statuses.get("not_listed_on_google", 0)
    live_web = web_statuses.get("live", 0)
    broken_web = sum(
        v for k, v in web_statuses.items()
        if k not in ("not_listed_on_google", "live", "business_not_found_on_google")
    )

    m, s = divmod(int(elapsed), 60)
    time_str = f"{m:02d}:{s:02d}"

    return (
        f"[{time_str}] {done:,}/{total:,} ({pct:5.1f}%) | "
        f"Rate: {rate:6.1f} leads/s | "
        f"Matched: {matched:,} | No-Web: {no_web:,} | Broken: {broken_web:,} | Live: {live_web:,} | "
        f"Flight: {in_progress:,} | Queue: {queued:,} | Failed: {failed:,}"
    )

def run_multi_process(
    args: argparse.Namespace,
    config: ScraperConfig,
    proxy_manager: ProxyManager,
    connection_kwargs: dict[str, Any],
    repository: EnrichmentRepository,
    run_id: uuid.UUID,
    review_provider: str,
    captcha_balance: float,
) -> int:
    n_procs = args.processes
    maps_per_proc = [args.workers // n_procs + (1 if i < args.workers % n_procs else 0) for i in range(n_procs)]
    web_per_proc = [args.website_workers // n_procs + (1 if i < args.website_workers % n_procs else 0) for i in range(n_procs)]
    pool_per_proc = max(10, args.postgres_pool_size // n_procs)
    rps_per_proc = max(0.5, args.maps_rps_per_proxy / n_procs)

    subprocesses = []
    child_outputs: list[list[str]] = [[] for _ in range(n_procs)]
    threads = []
    current_offset = 0

    env = os.environ.copy()

    for i in range(n_procs):
        cmd = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--child-run", str(run_id),
            "--worker-offset", str(current_offset),
            "--workers", str(maps_per_proc[i]),
            "--workers-per-proxy", str(args.workers_per_proxy),
            "--website-workers", str(web_per_proc[i]),
            "--website-workers-per-proxy", str(args.website_workers_per_proxy),
            "--postgres-pool-size", str(pool_per_proc),
            "--database", args.database,
            "--timeout", str(args.timeout),
            "--website-timeout", str(args.website_timeout),
            "--website-max-attempts", str(args.website_max_attempts),
            "--maps-rps-per-proxy", str(rps_per_proc),
            "--max-attempts", str(args.max_attempts),
            "--monitor-interval", str(args.monitor_interval),
            "--hard-throttle-window", str(args.hard_throttle_window),
            "--hard-throttle-min-events", str(args.hard_throttle_min_events),
            "--hard-throttle-rate", str(args.hard_throttle_rate),
            "--hard-throttle-consecutive", str(args.hard_throttle_consecutive),
            "--no-migrate",
            "--batch-size", str(args.batch_size),
        ]
        if args.review_api_key_env:
            cmd.extend(["--review-api-key-env", args.review_api_key_env])
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            cwd=str(Path(__file__).parent),
        )
        subprocesses.append(p)
        current_offset += maps_per_proc[i] + web_per_proc[i]

        log_dir = Path(__file__).resolve().parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        live_log_file = log_dir / "enrichment_live.log"

        def drain_output(proc=p, idx=i):
            for line in iter(proc.stdout.readline, ""):
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("child_result="):
                    child_outputs[idx].append(line_str)
                else:
                    with open(live_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now(timezone.utc).isoformat()} [proc-{idx}] {line_str}\n")
                    if "error" in line_str.lower() or "aborted" in line_str.lower() or "crashed" in line_str.lower():
                        print(f"[proc-{idx}] {line_str}", flush=True)
            proc.stdout.close()

        t = threading.Thread(target=drain_output, daemon=True)
        t.start()
        threads.append(t)

    last_monitor = 0.0
    start_time = time.monotonic()
    stopped_by_user = False
    stop_files = [
        Path("STOP"),
        Path(".stop"),
        Path(__file__).resolve().parent / "STOP",
        Path(__file__).resolve().parent / ".stop",
    ]

    try:
        while any(p.poll() is None for p in subprocesses):
            for sf in stop_files:
                if sf.exists():
                    stop_msg = f"[STOP TRIGGER] File '{sf.name}' detected! Gracefully stopping all processes..."
                    print(f"\n{stop_msg}", flush=True)
                    with open(live_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now(timezone.utc).isoformat()} {stop_msg}\n")
                    try:
                        sf.unlink()
                    except OSError:
                        pass
                    for p in subprocesses:
                        p.terminate()
                    for p in subprocesses:
                        p.wait()
                    stopped_by_user = True
                    break
            if stopped_by_user:
                break

            time.sleep(min(1.0, args.monitor_interval))
            now = time.monotonic()
            elapsed = now - start_time
            if now - last_monitor >= args.monitor_interval:
                progress = repository.progress(run_id)
                ticker = format_progress_line(progress, args.limit, elapsed)
                print(ticker, flush=True)
                with open(live_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now(timezone.utc).isoformat()} {ticker}\n")
                last_monitor = now
    except KeyboardInterrupt:
        print("master_interrupted=true terminating_child_processes=true", flush=True)
        for p in subprocesses:
            p.terminate()
        for p in subprocesses:
            p.wait()

    for t in threads:
        t.join(timeout=5.0)

    exit_codes = [p.poll() for p in subprocesses]
    print(f"child_exit_codes={exit_codes}", flush=True)

    all_maps_workers = []
    all_web_workers = []
    total_bytes_sent = 0
    total_bytes_received = 0

    for idx, output_lines in enumerate(child_outputs):
        for line in output_lines:
            if line.startswith("child_result="):
                try:
                    payload = json.loads(line[len("child_result="):])
                    total_bytes_sent += payload.get("bytes_sent", 0)
                    total_bytes_received += payload.get("bytes_received", 0)
                    all_maps_workers.extend(payload.get("maps_workers", []))
                    all_web_workers.extend(payload.get("website_workers", []))
                except Exception as e:
                    print(f"Error parsing child_result from proc {idx}: {e}", flush=True)

    total_bandwidth_bytes = total_bytes_sent + total_bytes_received
    bandwidth_summary = {
        "total_mb": round(total_bandwidth_bytes / (1024 * 1024), 2),
        "download_mb": round(total_bytes_received / (1024 * 1024), 2),
        "upload_mb": round(total_bytes_sent / (1024 * 1024), 2),
        "bytes_sent": total_bytes_sent,
        "bytes_received": total_bytes_received,
    }
    runtime = {
        "maps_workers": all_maps_workers,
        "website_workers": all_web_workers,
        "maps_worker_count": args.workers,
        "website_worker_count": args.website_workers,
        "maps_workers_per_proxy": args.workers_per_proxy,
        "website_workers_per_proxy": args.website_workers_per_proxy,
        "maps_rps_per_proxy": args.maps_rps_per_proxy,
        "website_timeout_seconds": args.website_timeout,
        "website_max_attempts": args.website_max_attempts,
        "postgres_pool_size": args.postgres_pool_size,
        "postgres_pool_stats": repository.pool_stats(),
        "proxy_routes": proxy_manager.total_proxies,
        "proxy_bandwidth": bandwidth_summary,
        "captcha_balance_at_start": captcha_balance,
        "processes": args.processes,
    }

    if any(code not in (0, None) for code in exit_codes):
        summary = repository.abort_run(
            run_id,
            f"child process failed with exit codes: {exit_codes}",
            {},
            runtime,
        )
        repository.close()
        print(format_summary(summary), flush=True)
        return 2

    summary = repository.complete_run(run_id, runtime)
    repository.close()
    print(format_summary(summary), flush=True)
    return 0

def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        raise SystemExit("--limit must be greater than zero")
    if args.processes < 1:
        raise SystemExit("--processes must be at least 1")
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.max_attempts <= 0:
        raise SystemExit("--max-attempts must be greater than zero")
    if args.workers_per_proxy <= 0:
        raise SystemExit("--workers-per-proxy must be greater than zero")
    if args.website_workers <= 0:
        raise SystemExit("--website-workers must be greater than zero")
    if args.website_workers_per_proxy <= 0:
        raise SystemExit("--website-workers-per-proxy must be greater than zero")
    if args.postgres_pool_size <= 0:
        raise SystemExit("--postgres-pool-size must be greater than zero")
    if args.website_timeout <= 0:
        raise SystemExit("--website-timeout must be greater than zero")
    if args.website_max_attempts <= 0:
        raise SystemExit("--website-max-attempts must be greater than zero")
    if args.maps_rps_per_proxy <= 0:
        raise SystemExit("--maps-rps-per-proxy must be greater than zero")
    if args.monitor_interval <= 0:
        raise SystemExit("--monitor-interval must be greater than zero")
    if not 0 < args.hard_throttle_rate <= 1:
        raise SystemExit("--hard-throttle-rate must be between zero and one")
    if args.hard_throttle_min_events > args.hard_throttle_window:
        raise SystemExit("--hard-throttle-min-events cannot exceed --hard-throttle-window")

    config = ScraperConfig()
    proxy_manager = ProxyManager(proxy_urls_file=config.proxy_urls_file)
    if proxy_manager.total_proxies == 0:
        raise SystemExit("No configured proxy routes; direct Google requests are forbidden")
    if not args.child_run:
        proxy_capacity = proxy_manager.total_proxies * args.workers_per_proxy
        if args.workers > proxy_capacity:
            raise SystemExit(
                f"--workers ({args.workers}) exceeds proxy capacity ({proxy_capacity}) at "
                f"{args.workers_per_proxy} workers per proxy"
            )
        website_proxy_capacity = proxy_manager.total_proxies * args.website_workers_per_proxy
        if args.website_workers > website_proxy_capacity:
            raise SystemExit(
                f"--website-workers ({args.website_workers}) exceeds proxy capacity "
                f"({website_proxy_capacity}) at {args.website_workers_per_proxy} workers per proxy"
            )
    captcha_preflight = CaptchaHandler(api_key=config.capsolver_api_key)
    if not captcha_preflight.enabled:
        raise SystemExit("CapSolver is not configured; CAPTCHA solving is required for this run")
    captcha_balance = captcha_preflight.check_balance() if not args.child_run else 1.0
    if not args.child_run and captcha_balance <= 0:
        raise SystemExit("CapSolver has no available balance; refusing an unprotected run")

    connection_kwargs = database_connection_kwargs(args.database)
    if not args.no_migrate and not args.child_run:
        apply_migration(connection_kwargs, args.migration)

    if not args.child_run:
        with psycopg.connect(**connection_kwargs) as capacity_connection:
            max_connections = int(capacity_connection.execute("show max_connections").fetchone()[0])
            existing_connections = int(
                capacity_connection.execute("select count(*) from pg_stat_activity").fetchone()[0]
            )
        projected_connections = existing_connections - 1 + args.postgres_pool_size + 2
        if projected_connections > max_connections - 3:
            raise SystemExit(
                "Worker configuration would leave fewer than three Postgres connections free: "
                f"projected={projected_connections} max={max_connections}"
            )

    api_key = os.getenv(args.review_api_key_env) if args.review_api_key_env else None
    review_provider = "maps_search_count_qv9_newest"
    if api_key:
        review_provider += "+places_api_legacy_fallback"
    repository = EnrichmentRepository(
        connection_kwargs,
        pool_size=args.postgres_pool_size,
    )
    if args.child_run:
        run_id = args.child_run
        enqueued = 0
    elif args.resume_run:
        run_id = args.resume_run
        enqueued = repository.prepare_resume(
            run_id,
            review_provider,
            retry_failed=args.retry_failed,
            backfill_reviews=args.backfill_reviews,
        )
    else:
        if args.retry_failed or args.backfill_reviews:
            raise SystemExit("--retry-failed and --backfill-reviews require --resume-run")
        run_id = repository.create_run(
            args.limit,
            args.workers,
            args.website_workers,
            review_provider,
        )
        enqueued = repository.enqueue(run_id, args.limit)
    if not args.child_run:
        print(
            f"run_id={run_id} enqueued={enqueued} processes={args.processes} maps_workers={args.workers} "
            f"website_workers={args.website_workers} "
            f"postgres_pool_size={args.postgres_pool_size} "
            f"proxy_routes={proxy_manager.total_proxies} "
            f"maps_workers_per_proxy={args.workers_per_proxy} "
            f"website_workers_per_proxy={args.website_workers_per_proxy} "
            f"maps_rps_per_proxy={args.maps_rps_per_proxy} captcha_enabled=true "
            f"review_provider={review_provider}",
            flush=True,
        )

    if not args.child_run and args.processes > 1:
        return run_multi_process(
            args=args,
            config=config,
            proxy_manager=proxy_manager,
            connection_kwargs=connection_kwargs,
            repository=repository,
            run_id=run_id,
            review_provider=review_provider,
            captcha_balance=captcha_balance,
        )

    throttle_controller = ThrottleController(
        window_size=args.hard_throttle_window,
        minimum_events=args.hard_throttle_min_events,
        rate_threshold=args.hard_throttle_rate,
        consecutive_limit=args.hard_throttle_consecutive,
    )
    maps_worker_stats = []
    website_worker_stats = []
    maps_done = threading.Event()
    rate_limiters: dict[int, ProxyRateLimiter] = {}
    total_workers = args.workers + args.website_workers
    with ThreadPoolExecutor(
        max_workers=total_workers,
        thread_name_prefix="gmaps-enrichment",
    ) as executor:
        future_kinds = {}
        map_futures = set()
        for local_idx in range(1, args.workers + 1):
            worker_number = args.worker_offset + local_idx
            route = proxy_manager.get_route_for_worker(worker_number)
            if route is None:
                raise RuntimeError(f"Worker {worker_number} has no proxy route")
            rate_limiter = rate_limiters.setdefault(
                id(route),
                ProxyRateLimiter(args.maps_rps_per_proxy),
            )
            future = executor.submit(
                run_maps_worker,
                repository,
                run_id,
                worker_number,
                route,
                api_key,
                config.capsolver_api_key,
                throttle_controller,
                rate_limiter,
                args.timeout,
                args.max_attempts,
                args.batch_size,
            )
            future_kinds[future] = ("maps", worker_number)
            map_futures.add(future)

        for local_idx in range(1, args.website_workers + 1):
            worker_number = args.worker_offset + args.workers + local_idx
            route = proxy_manager.get_route_for_worker(worker_number)
            if route is None:
                raise RuntimeError(f"Website worker {worker_number} has no proxy route")
            future = executor.submit(
                run_website_worker,
                repository,
                run_id,
                worker_number,
                route,
                maps_done,
                throttle_controller,
                args.website_timeout,
                args.website_max_attempts,
                args.batch_size,
            )
            future_kinds[future] = ("website", worker_number)

        pending = set(future_kinds)
        maps_pending = set(map_futures)
        last_monitor = 0.0
        start_time = time.monotonic()
        stop_files = [
            Path("STOP"),
            Path(".stop"),
            Path(__file__).resolve().parent / "STOP",
            Path(__file__).resolve().parent / ".stop",
        ]
        try:
            while pending:
                completed, pending = wait(
                    pending,
                    timeout=args.monitor_interval,
                    return_when=FIRST_COMPLETED,
                )
                for future in completed:
                    worker_kind, worker_number = future_kinds[future]
                    maps_pending.discard(future)
                    try:
                        stats = future.result()
                    except Exception as error:
                        throttle_controller.abort(
                            f"{worker_kind} worker {worker_number} crashed: "
                            f"{type(error).__name__}: {str(error)[:500]}"
                        )
                        print(
                            f"{worker_kind}_worker_error={type(error).__name__}: {error}",
                            flush=True,
                        )
                        continue
                    if worker_kind == "maps":
                        maps_worker_stats.append(stats)
                        print(
                            f"maps_worker={stats.worker_number} processed={stats.processed} "
                            f"matched={stats.matched} not_found={stats.not_found} "
                            f"failed={stats.failed} resets={stats.payload_session_resets} "
                            f"throttled={stats.throttled_searches}",
                            flush=True,
                        )
                    else:
                        website_worker_stats.append(stats)
                        print(
                            f"website_worker={stats.worker_number} processed={stats.processed} "
                            f"live={stats.live} errors={stats.errors} "
                            f"requeued={stats.requeued}",
                            flush=True,
                        )

                if not maps_pending:
                    maps_done.set()

                for sf in stop_files:
                    if sf.exists():
                        print(f"\n[STOP TRIGGER] File '{sf.name}' detected! Gracefully stopping workers...", flush=True)
                        throttle_controller.abort("stop file detected")
                        maps_done.set()
                        try:
                            sf.unlink()
                        except OSError:
                            pass
                        break

                now = time.monotonic()
                elapsed = now - start_time
                if not args.child_run and (now - last_monitor >= args.monitor_interval or not pending):
                    progress = repository.progress(run_id)
                    ticker = format_progress_line(progress, args.limit, elapsed)
                    print(ticker, flush=True)
                    last_monitor = now
        except KeyboardInterrupt:
            throttle_controller.abort("operator interrupted run")
            maps_done.set()
            print("operator_interrupt=true stopping_workers=true", flush=True)
            wait(pending)

    maps_workers_payload = [
        stats.__dict__ for stats in sorted(maps_worker_stats, key=lambda item: item.worker_number)
    ]
    website_workers_payload = [
        stats.__dict__
        for stats in sorted(website_worker_stats, key=lambda item: item.worker_number)
    ]
    throttle_snapshot = throttle_controller.snapshot()
    total_bytes_sent = sum(getattr(w, "bytes_sent", 0) for w in maps_worker_stats) + sum(
        getattr(w, "bytes_sent", 0) for w in website_worker_stats
    )
    total_bytes_received = sum(getattr(w, "bytes_received", 0) for w in maps_worker_stats) + sum(
        getattr(w, "bytes_received", 0) for w in website_worker_stats
    )
    total_bandwidth_bytes = total_bytes_sent + total_bytes_received
    bandwidth_summary = {
        "total_mb": round(total_bandwidth_bytes / (1024 * 1024), 2),
        "download_mb": round(total_bytes_received / (1024 * 1024), 2),
        "upload_mb": round(total_bytes_sent / (1024 * 1024), 2),
        "bytes_sent": total_bytes_sent,
        "bytes_received": total_bytes_received,
    }
    runtime = {
        "maps_workers": maps_workers_payload,
        "website_workers": website_workers_payload,
        "maps_worker_count": args.workers,
        "website_worker_count": args.website_workers,
        "maps_workers_per_proxy": args.workers_per_proxy,
        "website_workers_per_proxy": args.website_workers_per_proxy,
        "maps_rps_per_proxy": args.maps_rps_per_proxy,
        "website_timeout_seconds": args.website_timeout,
        "website_max_attempts": args.website_max_attempts,
        "postgres_pool_size": args.postgres_pool_size,
        "postgres_pool_stats": repository.pool_stats(),
        "proxy_routes": proxy_manager.total_proxies,
        "proxy_bandwidth": bandwidth_summary,
        "captcha_balance_at_start": captcha_balance,
        "throttle": throttle_snapshot,
    }
    if args.child_run:
        child_summary = {
            "bytes_sent": total_bytes_sent,
            "bytes_received": total_bytes_received,
            "maps_workers": maps_workers_payload,
            "website_workers": website_workers_payload,
        }
        print("child_result=" + json.dumps(child_summary, default=str), flush=True)
        repository.close()
        return 2 if throttle_controller.stop_requested else 0

    if throttle_controller.stop_requested:
        summary = repository.abort_run(
            run_id,
            throttle_controller.abort_reason or "run aborted",
            throttle_snapshot,
            runtime,
        )
        repository.close()
        print(format_summary(summary), flush=True)
        return 2

    summary = repository.complete_run(run_id, runtime)
    repository.close()
    print(format_summary(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
