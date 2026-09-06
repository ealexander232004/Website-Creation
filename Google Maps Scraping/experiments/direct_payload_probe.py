"""Probe Google Maps' current direct search payload using a mandatory proxy.

The Maps HTML bootstrap publishes a same-origin ``/search?tbm=map`` data URL.
This harness discovers that URL for each query instead of hard-coding a stale
protobuf template, then replays it through the same verified proxy session.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from curl_cffi import requests

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import DEFAULT_CONFIG
from proxy_manager import ProxyManager
from rpc_client import GoogleMapsRpcClient


BOOTSTRAP_LINK_RE = re.compile(
    r'''href=["'](?P<href>/search\?[^"']*\btbm=map[^"']*)["']''',
    flags=re.IGNORECASE,
)


class ProxyEnforcedSession:
    """Small guard that makes an unproxied experiment request impossible."""

    def __init__(self, proxy_url: str, timeout: float = 30.0) -> None:
        if not proxy_url:
            raise RuntimeError("Proxy enforcement failed: proxy URL is required")
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, url: str, **kwargs: Any) -> tuple[Any, float]:
        started = time.perf_counter()
        response = self.session.get(
            url,
            proxy=self.proxy_url,
            impersonate="chrome124",
            timeout=self.timeout,
            **kwargs,
        )
        return response, time.perf_counter() - started


def decode_google_json(payload: str) -> Any:
    """Decode the optional XSSI prefix used on internal Google JSON responses."""
    candidate = payload.lstrip()
    if candidate.startswith(")]}'"):
        candidate = candidate[4:].lstrip("\r\n")
    return json.loads(candidate)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", default="plumber")
    parser.add_argument("--lat", type=float, default=37.7749)
    parser.add_argument("--lng", type=float, default=-122.4194)
    parser.add_argument("--zoom", type=int, default=14)
    parser.add_argument("--proxy-worker", type=int, default=3)
    args = parser.parse_args()

    artifact_dir = PROJECT_DIR / "experiments" / "artifacts" / datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ-direct"
    )
    artifact_dir.mkdir(parents=True, exist_ok=False)

    proxy_manager = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    route = proxy_manager.get_route_for_worker(args.proxy_worker)
    if route is None:
        raise RuntimeError("Proxy enforcement failed: no configured route is available")
    client = ProxyEnforcedSession(route.raw_url)

    common_headers = {
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "user-agent": DEFAULT_CONFIG.user_agent,
    }

    ip_response, ip_seconds = client.get(
        "https://api.ipify.org?format=json",
        headers={"accept": "application/json", **common_headers},
    )
    ip_response.raise_for_status()
    egress_ip = ip_response.json().get("ip")
    if not egress_ip:
        raise RuntimeError("Proxy verification failed: egress IP was not returned")

    keyword_path = urllib.parse.quote(args.keyword, safe="")
    bootstrap_url = (
        f"https://www.google.com/maps/search/{keyword_path}/"
        f"@{args.lat},{args.lng},{args.zoom}z?hl=en"
    )
    bootstrap_response, bootstrap_seconds = client.get(
        bootstrap_url,
        headers={"accept": "text/html,application/xhtml+xml", **common_headers},
    )
    bootstrap_response.raise_for_status()
    bootstrap_text = bootstrap_response.text
    (artifact_dir / "bootstrap.html").write_text(bootstrap_text, encoding="utf-8")

    link_match = BOOTSTRAP_LINK_RE.search(bootstrap_text)
    if link_match is None:
        raise RuntimeError("Google bootstrap did not publish a /search?tbm=map data link")
    payload_path = html.unescape(link_match.group("href"))
    payload_url = urllib.parse.urljoin("https://www.google.com", payload_path)

    payload_response, payload_seconds = client.get(
        payload_url,
        headers={
            "accept": "*/*",
            "referer": bootstrap_url,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            **common_headers,
        },
    )
    payload_bytes = payload_response.content
    (artifact_dir / "payload.bin").write_bytes(payload_bytes)

    decoded: Any = None
    decode_error = None
    parsed_leads = []
    try:
        decoded = decode_google_json(payload_response.text)
        (artifact_dir / "payload.decoded.json").write_text(
            json.dumps(decoded, indent=2), encoding="utf-8"
        )
        parser_client = GoogleMapsRpcClient(proxy_url=route.raw_url)
        parsed_leads = parser_client._extract_leads_from_rpc_data(
            decoded, args.keyword, args.lat, args.lng
        )
    except Exception as exc:
        decode_error = str(exc)

    summary = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "proxy": {"host": route.host, "port": route.port, "egress_ip": egress_ip},
        "query": {
            "keyword": args.keyword,
            "latitude": args.lat,
            "longitude": args.lng,
            "zoom": args.zoom,
        },
        "bootstrap": {
            "url": bootstrap_url,
            "status": bootstrap_response.status_code,
            "bytes": len(bootstrap_response.content),
            "seconds": bootstrap_seconds,
        },
        "payload": {
            "url": payload_url,
            "status": payload_response.status_code,
            "content_type": payload_response.headers.get("content-type"),
            "bytes": len(payload_bytes),
            "seconds": payload_seconds,
            "json_decoded": decoded is not None,
            "decode_error": decode_error,
            "legacy_parser_leads": len(parsed_leads),
        },
        "ip_check_seconds": ip_seconds,
    }
    (artifact_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"artifact_dir={artifact_dir}")
    print(f"proxy={route.host}:{route.port} egress_ip={egress_ip}")
    print(
        f"bootstrap_status={bootstrap_response.status_code} "
        f"bytes={len(bootstrap_response.content)} seconds={bootstrap_seconds:.3f}"
    )
    print(
        f"payload_status={payload_response.status_code} bytes={len(payload_bytes)} "
        f"seconds={payload_seconds:.3f} content_type={payload_response.headers.get('content-type')!r}"
    )
    print(f"json_decoded={decoded is not None} legacy_parser_leads={len(parsed_leads)}")
    if decode_error:
        print(f"decode_error={decode_error}")
    if parsed_leads:
        for lead in parsed_leads[:5]:
            print(f"lead={lead.name!r} phone={lead.phone!r} website={lead.website_raw!r}")


if __name__ == "__main__":
    main()
