"""Run a small, proxy-enforced concurrency benchmark of the direct Maps client."""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import DEFAULT_CONFIG
from proxy_manager import ProxyManager
from rpc_client import GoogleMapsRpcClient


TEST_JOBS = [
    ("plumber", 37.7749, -122.4194),
    ("dentist", 34.0522, -118.2437),
    ("auto repair shop", 30.2672, -97.7431),
    ("florist", 25.7617, -80.1918),
    ("roofing contractor", 39.7392, -104.9903),
    ("electrician", 41.8781, -87.6298),
    ("moving company", 40.7128, -74.0060),
    ("barber shop", 33.4484, -112.0740),
    ("catering service", 47.6062, -122.3321),
    ("nail salon", 42.3601, -71.0589),
]


def run_job(index: int, route: Any, job: tuple[str, float, float]) -> dict[str, Any]:
    keyword, lat, lng = job
    started = time.perf_counter()
    error = None
    leads = []
    client = None
    try:
        client = GoogleMapsRpcClient(proxy_url=route.raw_url, timeout=25.0)
        leads = client.scrape_viewport_all(keyword, lat, lng, max_results=20)
    except Exception as exc:
        error = str(exc)
    finally:
        if client is not None:
            client.close()
    elapsed = time.perf_counter() - started

    return {
        "job": index + 1,
        "keyword": keyword,
        "latitude": lat,
        "longitude": lng,
        "proxy": {"host": route.host, "port": route.port},
        "seconds": elapsed,
        "lead_count": len(leads),
        "with_place_id": sum(bool(lead.place_id) for lead in leads),
        "with_phone": sum(bool(lead.phone) for lead in leads),
        "with_address": sum(bool(lead.full_address) for lead in leads),
        "with_website": sum(bool(lead.website_raw) for lead in leads),
        "with_rating": sum(lead.rating is not None for lead in leads),
        "unique_place_ids": len({lead.place_id for lead in leads if lead.place_id}),
        "error": error,
        "sample_names": [lead.name for lead in leads[:3]],
    }


def main() -> None:
    proxy_manager = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    routes = [proxy_manager.get_route_for_worker(i + 1) for i in range(len(TEST_JOBS))]
    if any(route is None for route in routes):
        raise RuntimeError("Proxy enforcement failed: benchmark requires ten configured routes")

    wall_started = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=len(TEST_JOBS)) as executor:
        futures = {
            executor.submit(run_job, index, route, job): index
            for index, (route, job) in enumerate(zip(routes, TEST_JOBS))
        }
        for future in as_completed(futures):
            results.append(future.result())
    wall_seconds = time.perf_counter() - wall_started
    results.sort(key=lambda item: item["job"])

    summary = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "workers": len(TEST_JOBS),
        "wall_seconds": wall_seconds,
        "jobs_per_minute_burst": len(TEST_JOBS) * 60 / wall_seconds,
        "successful_jobs": sum(result["lead_count"] > 0 and not result["error"] for result in results),
        "total_leads": sum(result["lead_count"] for result in results),
        "results": results,
    }

    output_path = PROJECT_DIR / "experiments" / "direct_benchmark.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"successful_jobs={summary['successful_jobs']}/{len(TEST_JOBS)} "
        f"total_leads={summary['total_leads']} wall_seconds={wall_seconds:.3f} "
        f"burst_jobs_per_minute={summary['jobs_per_minute_burst']:.1f}"
    )
    for result in results:
        print(
            f"proxy={result['proxy']['port']} keyword={result['keyword']!r} "
            f"leads={result['lead_count']} seconds={result['seconds']:.3f} "
            f"phones={result['with_phone']} websites={result['with_website']} "
            f"error={result['error']!r}"
        )


if __name__ == "__main__":
    main()
