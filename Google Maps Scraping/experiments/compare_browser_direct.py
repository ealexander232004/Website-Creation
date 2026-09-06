"""Compare direct-payload and asset-blocked browser results through proxies."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from browser_engine import BrowserEngine
from captcha_handler import CaptchaHandler
from config import DEFAULT_CONFIG, ScraperConfig
from models import SearchJob
from proxy_manager import ProxyManager
from rpc_client import GoogleMapsRpcClient


async def main() -> None:
    keyword = "plumber"
    lat = 37.7749
    lng = -122.4194

    proxy_manager = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    direct_route = proxy_manager.get_route_for_worker(9)
    browser_route = proxy_manager.get_route_for_worker(10)
    if direct_route is None or browser_route is None:
        raise RuntimeError("Proxy enforcement failed: two configured routes are required")

    direct_client = GoogleMapsRpcClient(direct_route.raw_url, timeout=25.0)
    direct_started = time.perf_counter()
    try:
        direct_leads = await asyncio.to_thread(
            direct_client.scrape_viewport_all, keyword, lat, lng, 20
        )
    finally:
        direct_client.close()
    direct_seconds = time.perf_counter() - direct_started

    browser_config = ScraperConfig(
        mode="browser",
        workers=1,
        max_results_per_query=20,
        detail_extraction=False,
        headless=True,
        page_timeout_seconds=45,
    )
    browser_engine = BrowserEngine(
        config=browser_config,
        proxy_manager=proxy_manager,
        captcha_handler=CaptchaHandler(api_key=browser_config.capsolver_api_key),
    )
    job = SearchJob(
        keyword=keyword,
        location_name="San Francisco direct comparison",
        latitude=lat,
        longitude=lng,
        zoom_level=14,
    )
    browser_started = time.perf_counter()
    try:
        await browser_engine.initialize()
        browser_leads = await browser_engine.execute_search_job(job, proxy_route=browser_route)
    finally:
        await browser_engine.close()
    browser_seconds = time.perf_counter() - browser_started

    direct_names = {lead.name.casefold(): lead.name for lead in direct_leads}
    browser_names = {lead.name.casefold(): lead.name for lead in browser_leads}
    overlap_keys = set(direct_names) & set(browser_names)

    summary = {
        "query": {"keyword": keyword, "latitude": lat, "longitude": lng},
        "direct": {
            "proxy": {"host": direct_route.host, "port": direct_route.port},
            "seconds": direct_seconds,
            "lead_count": len(direct_leads),
            "names": [lead.name for lead in direct_leads],
        },
        "browser": {
            "proxy": {"host": browser_route.host, "port": browser_route.port},
            "seconds": browser_seconds,
            "lead_count": len(browser_leads),
            "names": [lead.name for lead in browser_leads],
        },
        "overlap_count": len(overlap_keys),
        "overlap_names": sorted(direct_names[key] for key in overlap_keys),
        "direct_only_names": sorted(direct_names[key] for key in set(direct_names) - overlap_keys),
        "browser_only_names": sorted(browser_names[key] for key in set(browser_names) - overlap_keys),
    }
    output_path = Path(__file__).resolve().parent / "browser_direct_comparison.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"direct={len(direct_leads)} leads/{direct_seconds:.3f}s "
        f"browser={len(browser_leads)} leads/{browser_seconds:.3f}s "
        f"overlap={len(overlap_keys)}"
    )
    print(f"direct_only={summary['direct_only_names']}")
    print(f"browser_only={summary['browser_only_names']}")


if __name__ == "__main__":
    asyncio.run(main())
