"""High-performance direct HTTP client for Google Maps internal search RPC endpoint.

Bypasses DOM rendering entirely, querying Google's internal Protobuf-encoded
search endpoints (/maps/rpc/search) directly using curl_cffi with TLS fingerprint
impersonation.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
from typing import Any, Dict, Generator, List, Optional, Tuple

try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import httpx as cffi_requests
    CURL_CFFI_AVAILABLE = False

from models import ClaimedStatus, Lead, SearchJob, WebsiteType
from parser import parse_phone, parse_us_address
from website_analyzer import classify_website

logger = logging.getLogger("gmaps_scraper.rpc_client")

# Google Maps Internal Search RPC Endpoint
GMAPS_RPC_ENDPOINT = "https://www.google.com/maps/rpc/search"

# Realistic Chrome browser headers
DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.google.com/maps",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"128.0.6613.120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "x-maps-client-version": "10.0.0",
}


def build_pb_param(
    keyword: str,
    lat: float = 37.7749,
    lng: float = -122.4194,
    zoom_span: float = 0.05,
    start_index: int = 0,
    page_size: int = 20,
) -> str:
    """Constructs Google's serialized Protobuf parameter string ('pb') for spatial queries."""
    # pb format specifies viewport bounding spans, coordinates, query string, and pagination offset
    pb = (
        f"!1m8!1m3!1d{zoom_span}!2d{lng}!3d{lat}!3m2!1i1920!2i1080!4f13.1"
        f"!7i{page_size}!8i{start_index}!10b1!12m8!1m1!18b1!2m3!5m1!6e2!20e3!10b1!16b1"
        f"!19m4!2m3!1i360!2i120!4i8!20m57!2m2!1i203!2i100!3m2!2i1!5b1!6m6!1m2!1i86!2i86!1m2!1i408!2i240"
        f"!7m42!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2"
        f"!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!2b1!4b1!9b0"
        f"!22m6!1sa9z!2z!7e81!12e3!17sa9z!18e15!24m102!1m34!13m10!2m7!2i4!3i10!5b1!8f0!9m2!2b1!4b1!10m1!1e1!4b1"
        f"!19m6!2m1!1i360!2i120!4i8!20m1!1e1!2b1!26m4!2m3!1i80!2i92!4i8!30m1!1e3!39m1!1c1!44b1!50m1!2e1!2b1!5m5!2b1!3b1!5b1!6b1!7b1"
        f"!10m1!8e3!14m1!3b1!17b1!20m4!1e3!1e6!1e14!1e15!24b1!25b1!26b1!30b1!36b1!39m3!2e2!3b1!5b1!43b1!52b1!54m1!1b1!55b1"
        f"!56m2!1b1!3b1!65m5!3m4!1m3!1m2!1i224!2i298!71b1!72b1!89b1!26m4!2m3!1i80!2i92!4i8"
        f"!30m3!1m2!1d{lat}!2d{lng}!34m18!2b1!3b1!4b1!6b1!8m6!1b1!3b1!4b1!5b1!6b1!7b1!9b1!12b1!14b1!20b1!23b1!25b1!26b1"
        f"!37m1!1e81!47m0!49m8!3b1!6m2!1b1!2b1!7m2!1e3!2b1!8b1!9b1!50m4!2e2!3m2!1b1!3b1!67m2!7b1!10b1!69i637"
        f"!2m2!1i{start_index}!2s{keyword}"
    )
    return pb


class GoogleMapsRpcClient:
    """Queries Google Maps internal search endpoints directly without DOM rendering."""

    def __init__(self, proxy_url: Optional[str] = None, timeout: float = 15.0) -> None:
        self.proxy_url = proxy_url
        self.timeout = timeout

    def fetch_page(
        self,
        keyword: str,
        lat: float,
        lng: float,
        start_index: int = 0,
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetches a single batch of 20 results via Google's internal RPC endpoint."""
        pb = build_pb_param(keyword=keyword, lat=lat, lng=lng, start_index=start_index)
        params = {
            "authuser": "0",
            "hl": "en",
            "gl": "us",
            "pb": pb,
            "q": keyword,
        }

        request_kwargs: Dict[str, Any] = {
            "headers": DEFAULT_HEADERS,
            "params": params,
            "timeout": self.timeout,
        }

        if self.proxy_url:
            request_kwargs["proxy"] = self.proxy_url

        if CURL_CFFI_AVAILABLE:
            request_kwargs["impersonate"] = "chrome124"

        try:
            response = cffi_requests.get(GMAPS_RPC_ENDPOINT, **request_kwargs)
            if response.status_code != 200:
                logger.warning(
                    "Google RPC returned HTTP %d for '%s' (offset=%d)",
                    response.status_code,
                    keyword,
                    start_index,
                )
                return None

            text = response.text
            # Strip Google XSSI security prefix: )]}' or /*-secure- \n
            if text.startswith(")]}'\n") or text.startswith(")]}'"):
                text = text.split("\n", 1)[1] if "\n" in text else text[4:]

            raw_data = json.loads(text)
            return self._extract_leads_from_rpc_data(raw_data, keyword, lat, lng)

        except Exception as e:
            logger.error("RPC search failed for '%s': %s", keyword, e)
            return None

    def _extract_leads_from_rpc_data(
        self,
        data: Any,
        keyword: str,
        lat: float,
        lng: float,
    ) -> List[Lead]:
        """Navigates Google Maps raw array hierarchy to extract structured lead records."""
        leads: List[Lead] = []

        if not isinstance(data, list) or len(data) == 0:
            return leads

        # Listings array is located at data[0][1] (or data[1][1] in older payloads)
        results_container = None
        try:
            if len(data) > 0 and isinstance(data[0], list) and len(data[0]) > 1:
                results_container = data[0][1]
            elif len(data) > 1 and isinstance(data[1], list) and len(data[1]) > 1:
                results_container = data[1][1]
        except Exception:
            pass

        if not results_container or not isinstance(results_container, list):
            return leads

        for item in results_container:
            if not isinstance(item, list) or len(item) < 15:
                continue

            place_data = item[14]
            if not isinstance(place_data, list):
                continue

            try:
                lead = self._parse_place_array(place_data, keyword, lat, lng)
                if lead:
                    leads.append(lead)
            except Exception as e:
                logger.debug("Failed parsing RPC place entity: %s", e)

        return leads

    def _parse_place_array(
        self,
        p: List[Any],
        keyword: str,
        search_lat: float,
        search_lng: float,
    ) -> Optional[Lead]:
        """Extracts fields by indexing into the Google internal entity array."""
        # 1. Title / Name: p[11]
        name = p[11] if len(p) > 11 and isinstance(p[11], str) else None
        if not name:
            return None

        # 2. Main Category: p[13]
        category = p[13] if len(p) > 13 and isinstance(p[13], str) else None

        # 3. Secondary Categories: p[76]
        all_categories = []
        if len(p) > 76 and isinstance(p[76], list):
            all_categories = [c for c in p[76] if isinstance(c, str)]
        if category and category not in all_categories:
            all_categories.insert(0, category)

        # 4. Rating & Reviews count: p[4][7] & p[4][8]
        rating = None
        reviews_count = 0
        if len(p) > 4 and isinstance(p[4], list) and len(p[4]) > 8:
            try:
                rating = float(p[4][7]) if p[4][7] is not None else None
                reviews_count = int(p[4][8]) if p[4][8] is not None else 0
            except (ValueError, TypeError):
                pass

        # 5. Full Address: p[39] or p[2]
        full_address = None
        if len(p) > 39 and isinstance(p[39], str):
            full_address = p[39]
        elif len(p) > 2 and isinstance(p[2], list) and len(p[2]) > 0:
            full_address = p[2][0]

        street, city, state, zip_code = parse_us_address(full_address)

        # 6. Phone Number: p[178] or p[183] or scanning
        phone = None
        if len(p) > 178 and isinstance(p[178], list) and len(p[178]) > 0:
            sub = p[178][0]
            if isinstance(sub, list) and len(sub) > 0 and isinstance(sub[0], str):
                phone = parse_phone(sub[0])
            elif isinstance(sub, str):
                phone = parse_phone(sub)

        # 7. Website URL: p[7][0] or p[7][1]
        # In Google's internal array, p[7] contains the direct website URL if present
        website_raw = None
        if len(p) > 7 and isinstance(p[7], list) and len(p[7]) > 0:
            if isinstance(p[7][0], str) and p[7][0].startswith("http"):
                website_raw = p[7][0]
            elif len(p[7]) > 1 and isinstance(p[7][1], str) and p[7][1].startswith("http"):
                website_raw = p[7][1]

        # 8. Coordinates: p[9][2] (lat) & p[9][3] (lng)
        lat = None
        lng = None
        if len(p) > 9 and isinstance(p[9], list) and len(p[9]) > 3:
            try:
                lat = float(p[9][2])
                lng = float(p[9][3])
            except (ValueError, TypeError):
                pass

        # 9. Place ID / Hex CID: p[10] / p[78]
        place_id = None
        cid = None
        if len(p) > 10 and isinstance(p[10], str):
            place_id = p[10]
        if len(p) > 78 and isinstance(p[78], str):
            cid = p[78]

        # 10. Claimed Status: check merchant ownership flag in p[89] or p[5]
        is_claimed = ClaimedStatus.UNKNOWN
        if len(p) > 89 and isinstance(p[89], list):
            # If claimable prompt is present
            is_claimed = ClaimedStatus.UNCLAIMED

        # Classify website
        web_type, has_real_web, explanation = classify_website(website_raw)

        maps_url = (
            f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            if place_id
            else f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        )

        return Lead(
            place_id=place_id,
            cid=cid,
            name=name,
            category=category,
            all_categories=all_categories,
            phone=phone,
            full_address=full_address,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            latitude=lat,
            longitude=lng,
            website_raw=website_raw,
            website_type=web_type,
            website_explanation=explanation,
            has_website=has_real_web,
            rating=rating,
            reviews_count=reviews_count,
            is_claimed=is_claimed,
            maps_url=maps_url,
            search_keyword=keyword,
            search_location=f"({search_lat:.4f}, {search_lng:.4f})",
        )

    def scrape_viewport_all(
        self,
        keyword: str,
        lat: float,
        lng: float,
        max_results: int = 120,
    ) -> List[Lead]:
        """Paginates through all available results (up to 120 cap) for a coordinate viewport."""
        all_leads: List[Lead] = []
        offset = 0
        consecutive_empty = 0

        while offset < max_results:
            leads = self.fetch_page(keyword=keyword, lat=lat, lng=lng, start_index=offset)
            if not leads:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
            else:
                consecutive_empty = 0
                all_leads.extend(leads)
                if len(leads) < 20:  # End of available results for this viewport
                    break

            offset += 20

        return all_leads
