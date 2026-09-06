"""High-throughput multi-proxy runner for Facebook activity enrichment.

Implements all 3 strategies:
1. Wire compression (gzip / deflate)
2. Streaming early-abort socket disconnect on creation_time
3. Two-tier mobile triage (m.facebook.com -> desktop canonical SSR)
"""

from __future__ import annotations

import os
import sys
import time
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

# Add package root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

from facebook_last_post.config import DatabaseConfig
from facebook_last_post.database import FacebookActivityStore
from facebook_last_post.extractor import FacebookTriageClient
from facebook_last_post.models import FetchStatus


def resolve_proxies(env_path: Path, ports: list[int]) -> list[tuple[int, str, str]]:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("STATIC_ISP_PROXY_URL="):
            val = line.split("=", 1)[1].strip()
            parsed = urlparse(val)
            user = parsed.username
            password = parsed.password
            host = parsed.hostname
            break
    else:
        raise ValueError(f"STATIC_ISP_PROXY_URL not found in {env_path}")

    routes = []
    for p in ports:
        url = f"http://{user}:{password}@{host}:{p}"
        label = f"proxy-{p}"
        routes.append((p, url, label))
    return routes

def main() -> int:
    env_file = Path("Google Maps Scraping/.env")
    proxies_file = Path("Proxies/proxies.env")
    target_ports = [8051, 8053, 8054, 8055]
    workers_per_route = 1
    max_attempts = 3
    lease_seconds = 180

    from dotenv import load_dotenv
    load_dotenv(env_file)

    routes = resolve_proxies(proxies_file, target_ports)
    print(f"Loaded {len(routes)} proxy routes: {[r[0] for r in routes]}")

    db_config = DatabaseConfig.from_environment(database="lead_warehouse")
    store = FacebookActivityStore(db_config.conninfo)

    with store.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) as cnt FROM facebook_enrichment.profile_activity WHERE state = 'pending'")
            pending_count = cur.fetchone()["cnt"]
            print(f"Total pending jobs in queue: {pending_count:,}")

    total_workers = len(routes) * workers_per_route
    print(f"Starting {total_workers} workers ({workers_per_route} per proxy route)...")

    stop_event = threading.Event()
    lock = threading.Lock()
    stats = {
        "claimed": 0,
        "succeeded": 0,
        "restricted": 0,
        "no_data": 0,
        "unavailable": 0,
        "failed": 0,
    }
    start_time = time.monotonic()
    last_tick = time.monotonic()

    def worker_loop(worker_idx: int, proxy_port: int, proxy_url: str, proxy_label: str) -> None:
        worker_id = f"{socket.gethostname()}:p{proxy_port}:w{worker_idx}"
        conn = store.connect()
        try:
            with FacebookTriageClient(
                proxy_url=proxy_url,
                route_name=proxy_label,
                timeout_seconds=12.0,
                max_document_bytes=1_800_000,
            ) as client:
                while not stop_event.is_set():
                    job = store.claim_job(
                        conn,
                        worker_id=worker_id,
                        lease_seconds=lease_seconds,
                        max_attempts=max_attempts,
                    )
                    if job is None:
                        # Queue exhausted
                        return

                    with lock:
                        stats["claimed"] += 1

                    result = client.fetch(job.normalized_url)
                    state = store.record_result(
                        conn,
                        worker_id=worker_id,
                        job=job,
                        result=result,
                        max_attempts=max_attempts,
                    )

                    with lock:
                        if state in stats:
                            stats[state] += 1
                        else:
                            stats["failed"] += 1

                        now = time.monotonic()
                        nonlocal last_tick
                        if now - last_tick >= 5.0 or (stats["claimed"] % 50 == 0):
                            last_tick = now
                            elapsed = now - start_time
                            rate = stats["claimed"] / elapsed if elapsed > 0 else 0
                            print(
                                f"[{elapsed:5.1f}s] Claimed: {stats['claimed']:4d}/1000 "
                                f"({rate:4.1f} jobs/s) | "
                                f"succeeded={stats['succeeded']} "
                                f"restricted={stats['restricted']} "
                                f"no_data={stats['no_data']} "
                                f"unavailable={stats['unavailable']} "
                                f"failed={stats['failed']}"
                            )

                    # If this proxy itself is rate-limited (canary failed), bow out of the run
                    if result.status is FetchStatus.RATE_LIMITED:
                        print(f"Worker {worker_id} on {proxy_label}: PROXY FLAGGED by Meta edge (canary failed). Bowing out of run permanently.")
                        return

                    # Enforce 0.3 req/sec pace per proxy (3.33s delay)
                    time.sleep(3.33)
        except Exception as exc:
            print(f"Worker {worker_id} crashed: {exc}")
        finally:
            conn.close()

    # Launch worker threads
    futures = []
    with ThreadPoolExecutor(max_workers=total_workers) as executor:
        worker_counter = 1
        for port, p_url, p_label in routes:
            for w_num in range(1, workers_per_route + 1):
                f = executor.submit(worker_loop, worker_counter, port, p_url, p_label)
                futures.append(f)
                worker_counter += 1

        for f in futures:
            f.result()

    total_elapsed = time.monotonic() - start_time
    print("\n" + "=" * 60)
    print(f"Run completed in {total_elapsed:.1f}s ({total_elapsed/60:.2f} minutes)")
    print(f"Final stats: {stats}")
    print("=" * 60)

    # Print database breakdown
    with store.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT state, count(*) as count
                FROM facebook_enrichment.profile_activity
                GROUP BY state
                ORDER BY count DESC
            """)
            print("\nDatabase States:")
            for row in cur.fetchall():
                print(f"  {row['state']:<15}: {row['count']}")

            cur.execute("""
                SELECT count(*) as cnt,
                       count(last_post_at) as with_post_date,
                       count(likes_count) as with_likes,
                       count(talking_about_count) as with_talking_about,
                       count(page_category) as with_category
                FROM facebook_enrichment.profile_activity
                WHERE state != 'pending'
            """)
            meta_stats = cur.fetchone()
            print("\nMetadata Enriched:")
            print(f"  Processed profiles   : {meta_stats['cnt']}")
            print(f"  With post timestamp  : {meta_stats['with_post_date']}")
            print(f"  With likes count     : {meta_stats['with_likes']}")
            print(f"  With talking-about   : {meta_stats['with_talking_about']}")
            print(f"  With page category   : {meta_stats['with_category']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
