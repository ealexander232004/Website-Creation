"""High-performance direct HTTP client for Google Maps web search payloads.

The current Maps web client publishes a ``/search?tbm=map`` payload URL in its
HTML bootstrap. This module discovers that live URL and requests its JSON payload
without rendering a browser or downloading Maps assets. All network access is
proxy-enforced because the endpoint is an undocumented web implementation detail.
"""

from __future__ import annotations

import html
import json
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

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

# Google Maps web bootstrap and the current structured search-data endpoint.
GMAPS_BOOTSTRAP_ORIGIN = "https://www.google.com"
BOOTSTRAP_PAYLOAD_LINK_RE = re.compile(
    r'''href=["'](?P<href>/search\?[^"']*\btbm=map[^"']*)["']''',
    flags=re.IGNORECASE,
)

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
class GoogleMapsRpcClient:
    """Queries Google Maps web payloads directly without DOM rendering."""

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: float = 15.0,
        zoom_level: int = 14,
    ) -> None:
        if not proxy_url:
            raise ValueError("Direct Google Maps requests require a configured proxy URL")
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.zoom_level = zoom_level
        self._session = (
            cffi_requests.Session()
            if CURL_CFFI_AVAILABLE
            else cffi_requests.Client(proxy=self.proxy_url, timeout=self.timeout, follow_redirects=True)
        )
        self._payload_url_cache: Dict[Tuple[str, float, float], Tuple[str, str]] = {}

    def close(self) -> None:
        """Release sockets held by the underlying proxied HTTP session."""
        self._session.close()

    def _get(self, url: str, headers: Dict[str, str]) -> Any:
        """Makes one guarded GET; no direct-network fallback is permitted."""
        request_kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
        }
        if CURL_CFFI_AVAILABLE:
            request_kwargs["proxy"] = self.proxy_url
            request_kwargs["impersonate"] = "chrome124"
        return self._session.get(url, **request_kwargs)

    def _bootstrap_url(self, keyword: str, lat: float, lng: float) -> str:
        keyword_path = urllib.parse.quote(keyword, safe="")
        return (
            f"{GMAPS_BOOTSTRAP_ORIGIN}/maps/search/{keyword_path}/"
            f"@{lat},{lng},{self.zoom_level}z?hl=en"
        )

    def _discover_payload_url(self, keyword: str, lat: float, lng: float) -> Tuple[str, str]:
        """Reads the current ``tbm=map`` data URL from Google's HTML bootstrap."""
        cache_key = (keyword, round(lat, 7), round(lng, 7))
        cached = self._payload_url_cache.get(cache_key)
        if cached:
            return cached

        bootstrap_url = self._bootstrap_url(keyword, lat, lng)
        headers = {
            **DEFAULT_HEADERS,
            "accept": "text/html,application/xhtml+xml",
            "referer": "https://www.google.com/maps",
        }
        response = self._get(bootstrap_url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Maps bootstrap returned HTTP {response.status_code}")

        match = BOOTSTRAP_PAYLOAD_LINK_RE.search(response.text)
        if match is None:
            raise RuntimeError("Maps bootstrap did not publish a /search?tbm=map payload URL")

        relative_url = html.unescape(match.group("href"))
        payload_url = urllib.parse.urljoin(GMAPS_BOOTSTRAP_ORIGIN, relative_url)
        discovered = (bootstrap_url, payload_url)
        self._payload_url_cache[cache_key] = discovered
        return discovered

    @staticmethod
    def _payload_url_with_offset(payload_url: str, start_index: int, page_size: int = 20) -> str:
        """Updates pagination fields inside a live, Google-generated ``pb`` value."""
        parts = urllib.parse.urlsplit(payload_url)
        query_pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        updated_pairs: List[Tuple[str, str]] = []
        found_pb = False

        for key, value in query_pairs:
            if key != "pb":
                updated_pairs.append((key, value))
                continue

            found_pb = True
            pb = re.sub(r"!7i\d+", f"!7i{page_size}", value, count=1)
            if re.search(r"!8i\d+", pb):
                pb = re.sub(r"!8i\d+", f"!8i{start_index}", pb, count=1)
            elif start_index > 0:
                pb, replacements = re.subn(
                    r"(!7i\d+)", rf"\1!8i{start_index}", pb, count=1
                )
                if replacements != 1:
                    raise RuntimeError("Could not locate page-size field in Maps payload")
            updated_pairs.append((key, pb))

        if not found_pb:
            raise RuntimeError("Maps payload URL is missing its pb parameter")

        return urllib.parse.urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urllib.parse.urlencode(updated_pairs),
                parts.fragment,
            )
        )

    def fetch_page(
        self,
        keyword: str,
        lat: float,
        lng: float,
        start_index: int = 0,
    ) -> List[Lead]:
        """Fetches one page of 20 records from Google's current direct payload."""
        try:
            bootstrap_url, base_payload_url = self._discover_payload_url(keyword, lat, lng)
            payload_url = self._payload_url_with_offset(base_payload_url, start_index=start_index)
            headers = {
                **DEFAULT_HEADERS,
                "accept": "*/*",
                "referer": bootstrap_url,
            }
            response = self._get(payload_url, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Google Maps payload returned HTTP {response.status_code} "
                    f"for {keyword!r} (offset={start_index})"
                )

            text = response.text.lstrip()
            if text.startswith(")]}'"):
                text = text[4:].lstrip("\r\n")

            raw_data = json.loads(text)
            return self._extract_leads_from_rpc_data(raw_data, keyword, lat, lng)

        except Exception as e:
            logger.error("Direct Maps search failed for '%s': %s", keyword, e)
            raise RuntimeError(f"Direct Maps search failed for {keyword!r}: {e}") from e

    def _extract_leads_from_rpc_data(
        self,
        data: Any,
        keyword: str,
        lat: float,
        lng: float,
    ) -> List[Lead]:
        """Finds full place arrays by shape so top-level index changes are tolerated."""
        leads: List[Lead] = []
        place_arrays: List[List[Any]] = []
        seen_place_ids: set[str] = set()

        def is_place_array(value: Any) -> bool:
            return (
                isinstance(value, list)
                and len(value) > 178
                and isinstance(value[11], str)
                and bool(value[11])
                and isinstance(value[9], list)
                and len(value[9]) > 3
                and isinstance(value[78], str)
                and value[78].startswith("ChIJ")
            )

        def visit(value: Any) -> None:
            if not isinstance(value, list):
                return
            if is_place_array(value):
                place_id = value[78]
                if place_id not in seen_place_ids:
                    seen_place_ids.add(place_id)
                    place_arrays.append(value)
                return
            for child in value:
                visit(child)

        visit(data)
        for place_data in place_arrays:
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

        # 2. Categories: current payloads expose the full list at p[13].
        all_categories: List[str] = []
        if len(p) > 13 and isinstance(p[13], list):
            all_categories = [value for value in p[13] if isinstance(value, str)]
        elif len(p) > 13 and isinstance(p[13], str):
            all_categories = [p[13]]
        elif len(p) > 76 and isinstance(p[76], list):
            all_categories = [value for value in p[76] if isinstance(value, str)]
        category = all_categories[0] if all_categories else None

        # 3. Rating and review count: rating is p[4][7], count is p[37][1].
        rating = None
        reviews_count = 0
        if len(p) > 4 and isinstance(p[4], list) and len(p[4]) > 7:
            try:
                rating = float(p[4][7]) if p[4][7] is not None else None
            except (ValueError, TypeError):
                pass
        if len(p) > 37 and isinstance(p[37], list) and len(p[37]) > 1:
            try:
                reviews_count = int(p[37][1]) if p[37][1] is not None else 0
            except (ValueError, TypeError):
                pass
        elif len(p) > 4 and isinstance(p[4], list) and len(p[4]) > 8:
            try:
                reviews_count = int(p[4][8]) if p[4][8] is not None else 0
            except (ValueError, TypeError):
                pass

        # 4. Full address: p[39] is formatted; p[2] has split lines.
        full_address = None
        if len(p) > 39 and isinstance(p[39], str):
            full_address = p[39]
        elif len(p) > 2 and isinstance(p[2], list) and len(p[2]) > 0:
            full_address = p[2][0]

        street, city, state, zip_code = parse_us_address(full_address)

        # 5. Phone number.
        phone = None
        if len(p) > 178 and isinstance(p[178], list) and len(p[178]) > 0:
            sub = p[178][0]
            if isinstance(sub, list) and len(sub) > 0 and isinstance(sub[0], str):
                phone = parse_phone(sub[0])
            elif isinstance(sub, str):
                phone = parse_phone(sub)

        # 6. Website URL: p[7] contains URL and display domain when present.
        website_raw = None
        if len(p) > 7 and isinstance(p[7], list) and len(p[7]) > 0:
            if isinstance(p[7][0], str) and p[7][0].startswith("http"):
                website_raw = p[7][0]
            elif len(p[7]) > 1 and isinstance(p[7][1], str) and p[7][1].startswith("http"):
                website_raw = p[7][1]

        # 7. Coordinates: p[9][2] (lat) and p[9][3] (lng).
        lat = None
        lng = None
        if len(p) > 9 and isinstance(p[9], list) and len(p[9]) > 3:
            try:
                lat = float(p[9][2])
                lng = float(p[9][3])
            except (ValueError, TypeError):
                pass

        # 8. Place ID and CID. p[10] is a hex data ID; p[78] is the ChIJ ID.
        place_id = None
        cid = None
        if len(p) > 78 and isinstance(p[78], str) and p[78].startswith("ChIJ"):
            place_id = p[78]
        if len(p) > 10 and isinstance(p[10], str):
            cid_match = re.fullmatch(r"0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)", p[10])
            if cid_match:
                cid = str(int(cid_match.group(1), 16))

        # Claimed status is intentionally unknown: the current payload has no
        # stable, verified ownership field and guessing would contaminate data.
        is_claimed = ClaimedStatus.UNKNOWN

        # Classify website
        web_type, has_real_web, explanation = classify_website(website_raw)

        maps_query = urllib.parse.quote_plus(name)
        maps_url = (
            f"https://www.google.com/maps/search/?api=1&query={maps_query}&query_place_id={place_id}"
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
        seen_ids: set[str] = set()
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
                added = 0
                for lead in leads:
                    identity = lead.place_id or lead.cid or f"{lead.name}|{lead.phone}|{lead.full_address}"
                    if identity in seen_ids:
                        continue
                    seen_ids.add(identity)
                    all_leads.append(lead)
                    added += 1
                    if len(all_leads) >= max_results:
                        break
                if added == 0:
                    break
                if len(leads) < 20:  # End of available results for this viewport
                    break

            offset += 20

        return all_leads[:max_results]
