"""CLI for warehouse Google Maps enrichment.

Example:
    python enrich_google_maps.py --limit 500 --workers 10
"""

from __future__ import annotations

import argparse
import os
import threading
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
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
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--website-timeout", type=float, default=6.0)
    parser.add_argument("--website-max-attempts", type=int, default=2)
    parser.add_argument("--maps-rps-per-proxy", type=float, default=3.0)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--monitor-interval", type=float, default=15.0)
    parser.add_argument("--hard-throttle-window", type=int, default=100)
    parser.add_argument("--hard-throttle-min-events", type=int, default=30)
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


def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        raise SystemExit("--limit must be greater than zero")
    if args.workers < 2:
        raise SystemExit("--workers must be at least 2 for this multi-worker scraper")
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
    captcha_balance = captcha_preflight.check_balance()
    if captcha_balance <= 0:
        raise SystemExit("CapSolver has no available balance; refusing an unprotected run")

    connection_kwargs = database_connection_kwargs(args.database)
    if not args.no_migrate:
        apply_migration(connection_kwargs, args.migration)

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
    if args.resume_run:
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
    print(
        f"run_id={run_id} enqueued={enqueued} maps_workers={args.workers} "
        f"website_workers={args.website_workers} "
        f"postgres_pool_size={args.postgres_pool_size} "
        f"proxy_routes={proxy_manager.total_proxies} "
        f"maps_workers_per_proxy={args.workers_per_proxy} "
        f"website_workers_per_proxy={args.website_workers_per_proxy} "
        f"maps_rps_per_proxy={args.maps_rps_per_proxy} captcha_enabled=true "
        f"review_provider={review_provider}",
        flush=True,
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
        for worker_number in range(1, args.workers + 1):
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
            )
            future_kinds[future] = ("maps", worker_number)
            map_futures.add(future)

        for worker_number in range(1, args.website_workers + 1):
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
            )
            future_kinds[future] = ("website", worker_number)

        pending = set(future_kinds)
        maps_pending = set(map_futures)
        last_monitor = 0.0
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

                now = time.monotonic()
                if now - last_monitor >= args.monitor_interval or not pending:
                    progress = repository.progress(run_id)
                    print(
                        "progress="
                        + format_summary(
                            {
                                "statuses": progress["statuses"],
                                "website_statuses": progress["website_statuses"],
                                "website_check_states": progress["website_check_states"],
                                "throttle": throttle_controller.snapshot(),
                            }
                        ),
                        flush=True,
                    )
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
        "captcha_balance_at_start": captcha_balance,
        "throttle": throttle_snapshot,
    }
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
