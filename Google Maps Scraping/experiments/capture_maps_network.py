"""Capture Google Maps search data requests from one fully proxied browser session.

This is an investigation harness, not part of the campaign runner. It deliberately
uses one configured proxy for the browser's entire lifetime and avoids persisting
cookies, authorization headers, or proxy credentials.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import Request, Response, async_playwright

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import DEFAULT_CONFIG
from proxy_manager import ProxyManager


INTERESTING_PATHS = (
    "/maps/preview/",
    "/maps/rpc/",
    "/maps/_/",
    "batchexecute",
)


def is_interesting_request(request: Request) -> bool:
    """Keep only Maps documents and likely structured-data requests."""
    url = request.url
    if "google.com" not in url:
        return False
    if any(marker in url for marker in INTERESTING_PATHS):
        return True
    return "/maps/" in url and request.resource_type in {"document", "xhr", "fetch"}


def safe_filename(index: int, url: str) -> str:
    path_part = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1] or "response"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", path_part)[:48]
    return f"{index:03d}_{cleaned}.bin"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", default="plumber")
    parser.add_argument("--lat", type=float, default=37.7749)
    parser.add_argument("--lng", type=float, default=-122.4194)
    parser.add_argument("--zoom", type=int, default=14)
    parser.add_argument("--proxy-worker", type=int, default=1)
    parser.add_argument("--settle-seconds", type=float, default=12.0)
    args = parser.parse_args()

    artifact_dir = PROJECT_DIR / "experiments" / "artifacts" / datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    artifact_dir.mkdir(parents=True, exist_ok=False)

    proxy_manager = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    route = proxy_manager.get_route_for_worker(args.proxy_worker)
    if route is None:
        raise RuntimeError("Proxy enforcement failed: no configured proxy route is available")

    captures: list[dict[str, Any]] = []
    response_tasks: list[asyncio.Task[None]] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            proxy=route.to_playwright_dict(),
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        context = await browser.new_context(locale="en-US")

        # Verify that the browser itself—not merely the HTTP test client—uses the proxy.
        ip_page = await context.new_page()
        await ip_page.goto("https://api.ipify.org?format=json", wait_until="domcontentloaded", timeout=30_000)
        egress = json.loads(await ip_page.text_content("body") or "{}")
        await ip_page.close()
        if not egress.get("ip"):
            raise RuntimeError("Proxy verification failed: browser egress IP was not returned")

        page = await context.new_page()

        async def block_heavy_assets(route_handler: Any) -> None:
            if route_handler.request.resource_type in {"image", "font", "media"}:
                await route_handler.abort()
            else:
                await route_handler.continue_()

        await page.route("**/*", block_heavy_assets)

        def record_request(request: Request) -> None:
            if not is_interesting_request(request):
                return
            captures.append(
                {
                    "request": {
                        "method": request.method,
                        "resource_type": request.resource_type,
                        "url": request.url,
                        "post_data": request.post_data,
                    },
                    "response": None,
                }
            )

        async def record_response(response: Response) -> None:
            request = response.request
            if not is_interesting_request(request):
                return
            matching = next(
                (
                    item
                    for item in reversed(captures)
                    if item["request"]["url"] == request.url
                    and item["request"]["method"] == request.method
                    and item["response"] is None
                ),
                None,
            )
            if matching is None:
                return
            body_file = None
            body_size = None
            body_error = None
            try:
                body = await response.body()
                body_size = len(body)
                body_file = safe_filename(captures.index(matching), request.url)
                (artifact_dir / body_file).write_bytes(body)
            except Exception as exc:  # Some redirects/streaming responses have no retrievable body.
                body_error = str(exc)
            matching["response"] = {
                "status": response.status,
                "content_type": response.headers.get("content-type"),
                "body_file": body_file,
                "body_size": body_size,
                "body_error": body_error,
            }

        page.on("request", record_request)
        page.on("response", lambda response: response_tasks.append(asyncio.create_task(record_response(response))))

        encoded_keyword = args.keyword.replace(" ", "+")
        search_url = (
            f"https://www.google.com/maps/search/{encoded_keyword}/"
            f"@{args.lat},{args.lng},{args.zoom}z?hl=en"
        )
        navigation_error = None
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as exc:
            # A slow top-level document must not discard XHRs already observed.
            navigation_error = str(exc)
        await page.wait_for_timeout(int(args.settle_seconds * 1000))
        await asyncio.gather(*response_tasks, return_exceptions=True)

        title = await page.title()
        final_url = page.url
        await context.close()
        await browser.close()

    metadata = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "proxy": {"host": route.host, "port": route.port, "egress_ip": egress["ip"]},
        "search": {
            "keyword": args.keyword,
            "latitude": args.lat,
            "longitude": args.lng,
            "zoom": args.zoom,
            "requested_url": search_url,
            "final_url": final_url,
            "title": title,
            "navigation_error": navigation_error,
        },
        "captures": captures,
    }
    metadata_path = artifact_dir / "capture.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"artifact_dir={artifact_dir}")
    print(f"proxy={route.host}:{route.port} egress_ip={egress['ip']}")
    print(f"page_title={title!r}")
    print(f"captured_requests={len(captures)}")
    for index, item in enumerate(captures):
        response = item["response"] or {}
        url = item["request"]["url"]
        print(
            f"[{index:03d}] {item['request']['method']} {item['request']['resource_type']} "
            f"status={response.get('status')} bytes={response.get('body_size')} {url[:240]}"
        )


if __name__ == "__main__":
    asyncio.run(main())
