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
import random
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
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
from captcha_handler import CaptchaHandler

logger = logging.getLogger("gmaps_scraper.rpc_client")

# Google Maps web bootstrap and the current structured search-data endpoint.
GMAPS_BOOTSTRAP_ORIGIN = "https://www.google.com"
BOOTSTRAP_PAYLOAD_LINK_RE = re.compile(
    r'''href=["'](?P<href>/search\?[^"']*\btbm=map[^"']*)["']''',
    flags=re.IGNORECASE,
)
BOOTSTRAP_KEI_RE = re.compile(r'''\bkEI\s*=\s*["'](?P<kei>[^"']+)["']''')
REVIEW_RPC_ID = "qv9Egd"
REVIEW_RPC_PATH = "/maps/_/MapsWizUi/data/batchexecute"

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


class GoogleMapsRpcError(RuntimeError):
    """Base error for a failed direct Maps request."""


class GoogleMapsThrottleError(GoogleMapsRpcError):
    """Google rejected or throttled the assigned proxy route."""


class GoogleMapsChallengeError(GoogleMapsThrottleError):
    """A Google bot challenge could not be solved."""


class GoogleMapsPayloadDiscoveryError(GoogleMapsRpcError):
    """The bootstrap loaded but did not expose the structured Maps endpoint."""


class GoogleMapsReviewRpcError(GoogleMapsRpcError):
    """The structured Maps review RPC returned an invalid or rejected payload."""


@dataclass(frozen=True)
class GoogleMapsReviewPage:
    """The newest public review returned by MapsUgcPostService.ListUgcPosts."""

    latest_review_at: Optional[datetime]
    relative_date: Optional[str]
    has_reviews: bool
    exhausted: bool


class GoogleMapsRpcClient:
    """Queries Google Maps web payloads directly without DOM rendering."""

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: float = 15.0,
        zoom_level: int = 14,
        captcha_handler: Optional[CaptchaHandler] = None,
    ) -> None:
        if not proxy_url:
            raise ValueError("Direct Google Maps requests require a configured proxy URL")
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.zoom_level = zoom_level
        self.captcha_handler = captcha_handler
        self.captcha_detected = 0
        self.captcha_solved = 0
        self.captcha_failed = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self._session = self._new_session()
        self._payload_url_cache: Dict[Tuple[str, float, float], Tuple[str, str]] = {}
        self._bootstrap_context_cache: Dict[Tuple[str, float, float], Tuple[str, str]] = {}
        self._last_bootstrap_context: Optional[Tuple[str, str]] = None
        self._session_base_pb: Optional[str] = None
        self._session_bootstrap_url: Optional[str] = None
        self._session_pb_uses = 0
        self._review_client_context: Optional[int] = None
        self._review_request_id = random.randint(100_000, 999_999)

    def _new_session(self) -> Any:
        return (
            cffi_requests.Session()
            if CURL_CFFI_AVAILABLE
            else cffi_requests.Client(
                proxy=self.proxy_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
        )

    def close(self) -> None:
        """Release sockets held by the underlying proxied HTTP session."""
        self._session.close()

    def reset_session(self) -> None:
        """Drops cookies/connections after a malformed or degraded bootstrap."""
        self._session.close()
        self._session = self._new_session()
        self._payload_url_cache.clear()
        self._bootstrap_context_cache.clear()
        self._last_bootstrap_context = None
        self._session_base_pb = None
        self._session_bootstrap_url = None
        self._session_pb_uses = 0
        self._review_client_context = None
    def _request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Makes one guarded proxied request; direct fallback is forbidden."""
        request_kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
        }
        if data is not None:
            request_kwargs["data"] = data
        if CURL_CFFI_AVAILABLE:
            request_kwargs["allow_redirects"] = True
            request_kwargs["proxy"] = self.proxy_url
            request_kwargs["impersonate"] = "chrome124"
        else:
            request_kwargs["follow_redirects"] = True
        req_body_len = 0
        if data is not None:
            if isinstance(data, str):
                req_body_len = len(data.encode("utf-8", errors="ignore"))
            elif isinstance(data, (bytes, bytearray)):
                req_body_len = len(data)
            elif isinstance(data, dict):
                req_body_len = sum(len(str(k)) + len(str(v)) + 2 for k, v in data.items())
        headers_len = sum(len(str(k)) + len(str(v)) + 4 for k, v in headers.items()) + len(url) + 50
        self.bytes_sent += req_body_len + headers_len

        response = self._session.request(method, url, **request_kwargs)

        resp_content = getattr(response, "content", b"") or b""
        if isinstance(resp_content, str):
            resp_content = resp_content.encode("utf-8", errors="ignore")
        resp_headers = getattr(response, "headers", {}) or {}
        resp_headers_len = sum(len(str(k)) + len(str(v)) + 4 for k, v in resp_headers.items()) + 50
        self.bytes_received += len(resp_content) + resp_headers_len

        return response
    def _get(self, url: str, headers: Dict[str, str]) -> Any:
        return self._request("GET", url, headers)

    @staticmethod
    def _page_title(page_content: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", page_content, flags=re.IGNORECASE | re.DOTALL)
        return html.unescape(match.group(1)).strip() if match else ""

    def _is_google_challenge(self, response: Any) -> bool:
        content = str(getattr(response, "text", "") or "")
        url = str(getattr(response, "url", "") or "")
        title = self._page_title(content)
        if self.captcha_handler:
            return self.captcha_handler.is_challenge_page(url, title, content)
        lowered = content.lower()
        return (
            "/sorry/index" in url.lower()
            or "google.com/sorry" in url.lower()
            or "unusual traffic from your computer network" in lowered
            or "our systems have detected unusual traffic" in lowered
        )

    def _submit_google_challenge(self, response: Any, token: str) -> Any:
        page_content = str(response.text or "")
        response_url = str(response.url)
        form_match = re.search(
            r"<form[^>]+action=[\"']([^\"']+)[\"']",
            page_content,
            flags=re.IGNORECASE,
        )
        form_url = urllib.parse.urljoin(
            response_url,
            html.unescape(form_match.group(1)) if form_match else "/sorry/index",
        )
        form_data: Dict[str, str] = {}
        for tag in re.findall(r"<input\b[^>]*>", page_content, flags=re.IGNORECASE):
            name_match = re.search(r"\bname=[\"']([^\"']+)[\"']", tag, flags=re.IGNORECASE)
            if name_match is None:
                continue
            value_match = re.search(r"\bvalue=[\"']([^\"']*)[\"']", tag, flags=re.IGNORECASE)
            form_data[html.unescape(name_match.group(1))] = (
                html.unescape(value_match.group(1)) if value_match else ""
            )
        form_data["g-recaptcha-response"] = token
        return self._request(
            "POST",
            form_url,
            headers={
                **DEFAULT_HEADERS,
                "accept": "text/html,application/xhtml+xml",
                "content-type": "application/x-www-form-urlencoded",
                "referer": response_url,
            },
            data=form_data,
        )

    def _guard_google_response(self, response: Any) -> Any:
        if self._is_google_challenge(response):
            self.captcha_detected += 1
            if self.captcha_handler and self.captcha_handler.enabled:
                page_content = str(response.text or "")
                page_url = str(response.url)
                site_key = self.captcha_handler.extract_sitekey(page_content, page_url)
                token = self.captcha_handler.solve_recaptcha(
                    page_url,
                    site_key,
                    proxy_url=self.proxy_url,
                )
                if token:
                    solved_response = self._submit_google_challenge(response, token)
                    if not self._is_google_challenge(solved_response):
                        self.captcha_solved += 1
                        return solved_response
            self.captcha_failed += 1
            raise GoogleMapsChallengeError("Google Maps CAPTCHA challenge was not solved")

        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code in {403, 429, 503}:
            raise GoogleMapsThrottleError(f"Google Maps returned HTTP {status_code}")
        return response

    def _get_google(self, url: str, headers: Dict[str, str]) -> Any:
        return self._guard_google_response(self._get(url, headers))

    def _safe_error(self, error: Exception) -> str:
        message = str(error).replace(self.proxy_url, "<proxy>")
        return message[:1_500]

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
            self._last_bootstrap_context = self._bootstrap_context_cache.get(cache_key)
            return cached

        bootstrap_url = self._bootstrap_url(keyword, lat, lng)
        headers = {
            **DEFAULT_HEADERS,
            "accept": "text/html,application/xhtml+xml",
            "referer": "https://www.google.com/maps",
        }
        response = self._get_google(bootstrap_url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Maps bootstrap returned HTTP {response.status_code}")

        match = BOOTSTRAP_PAYLOAD_LINK_RE.search(response.text)
        if match is None:
            raise GoogleMapsPayloadDiscoveryError(
                "Maps bootstrap did not publish a /search?tbm=map payload URL"
            )

        relative_url = html.unescape(match.group("href"))
        payload_url = urllib.parse.urljoin(GMAPS_BOOTSTRAP_ORIGIN, relative_url)
        kei_match = BOOTSTRAP_KEI_RE.search(response.text)
        if kei_match is None:
            raise GoogleMapsPayloadDiscoveryError("Maps bootstrap did not publish a kEI session ID")
        source_path = urllib.parse.urlsplit(bootstrap_url).path
        discovered = (bootstrap_url, payload_url)
        self._payload_url_cache[cache_key] = discovered
        self._bootstrap_context_cache[cache_key] = (kei_match.group("kei"), source_path)
        self._last_bootstrap_context = self._bootstrap_context_cache[cache_key]
        return discovered

    @staticmethod
    def _review_rpc_entry(response_text: str) -> list[Any]:
        """Extracts the qv9Egd entry from batchexecute's length-framed response."""
        text = response_text.lstrip()
        if text.startswith(")]}'"):
            text = text[4:].lstrip("\r\n")
        for line in text.splitlines():
            candidate = line.strip()
            if not candidate.startswith("["):
                continue
            try:
                frame = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if not isinstance(frame, list):
                continue
            for entry in frame:
                if (
                    isinstance(entry, list)
                    and len(entry) >= 3
                    and entry[0] == "wrb.fr"
                    and entry[1] == REVIEW_RPC_ID
                ):
                    return entry
        raise GoogleMapsReviewRpcError("Maps review RPC response was missing qv9Egd")

    @staticmethod
    def _parse_review_rpc_payload(payload: Any) -> GoogleMapsReviewPage:
        if not isinstance(payload, list):
            raise GoogleMapsReviewRpcError("Maps review RPC payload was not an array")

        exhausted = bool(payload[5]) if len(payload) > 5 else False
        posts = payload[2] if len(payload) > 2 and isinstance(payload[2], list) else []
        if not posts:
            return GoogleMapsReviewPage(None, None, False, exhausted)

        # Response field 3 is repeated UgcPost. Its field 1 contains the review,
        # whose field 2 is metadata. Google reads metadata field 4 as a
        # microsecond Unix timestamp when evaluating review age; field 7 is the
        # human-readable relative date shown in Maps.
        first_post = posts[0]
        try:
            review = first_post[0]
            metadata = review[1]
        except (IndexError, TypeError):
            raise GoogleMapsReviewRpcError("Newest Maps review was missing metadata")

        relative_date = (
            metadata[6]
            if isinstance(metadata, list) and len(metadata) > 6 and isinstance(metadata[6], str)
            else None
        )
        raw_timestamp = metadata[3] if isinstance(metadata, list) and len(metadata) > 3 else None
        latest_review_at: Optional[datetime] = None
        if isinstance(raw_timestamp, str) and raw_timestamp.isdigit():
            raw_timestamp = int(raw_timestamp)
        if isinstance(raw_timestamp, (int, float)) and raw_timestamp > 0:
            latest_review_at = datetime.fromtimestamp(
                float(raw_timestamp) / 1_000_000,
                tz=timezone.utc,
            )
        return GoogleMapsReviewPage(latest_review_at, relative_date, True, exhausted)

    def _review_rpc_inner(self, cid: str, kei: str, client_context: int) -> list[Any]:
        try:
            cid_hex = format(int(cid), "x")
        except (TypeError, ValueError) as error:
            raise GoogleMapsReviewRpcError(f"Invalid Google CID: {cid!r}") from error
        return [
            [
                [f"0x0:0x{cid_hex}"],
                None,
                None,
                None,
                None,
                [None, None, None, [[1]]],
            ],
            [20],
            None,
            None,
            [kei, None, None, None, None, None, client_context],
            None,
            None,
            [None, 1, 1],
            None,
            None,
            None,
            None,
            [2],
        ]

    def _post_review_rpc(
        self,
        cid: str,
        kei: str,
        source_path: str,
        client_context: int,
    ) -> GoogleMapsReviewPage:
        inner = self._review_rpc_inner(cid, kei, client_context)
        f_req = [[[REVIEW_RPC_ID, json.dumps(inner, separators=(",", ":")), None, "generic"]]]
        self._review_request_id += 100_000
        query = urllib.parse.urlencode(
            {
                "rpcids": REVIEW_RPC_ID,
                "source-path": source_path,
                "hl": "en",
                "_reqid": str(self._review_request_id),
                "rt": "c",
            }
        )
        url = f"{GMAPS_BOOTSTRAP_ORIGIN}{REVIEW_RPC_PATH}?{query}"
        response = self._guard_google_response(
            self._request(
                "POST",
                url,
                headers={
                    **DEFAULT_HEADERS,
                    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "origin": GMAPS_BOOTSTRAP_ORIGIN,
                    "referer": urllib.parse.urljoin(GMAPS_BOOTSTRAP_ORIGIN, source_path),
                    "x-same-domain": "1",
                },
                data={"f.req": json.dumps(f_req, separators=(",", ":"))},
            )
        )
        if response.status_code != 200:
            raise GoogleMapsReviewRpcError(f"Maps review RPC returned HTTP {response.status_code}")
        entry = self._review_rpc_entry(response.text)
        rpc_error = entry[5] if len(entry) > 5 else None
        if entry[2] is None:
            status = rpc_error[0] if isinstance(rpc_error, list) and rpc_error else "unknown"
            raise GoogleMapsReviewRpcError(f"Maps review RPC rejected context with status {status}")
        try:
            payload = json.loads(entry[2])
        except (TypeError, json.JSONDecodeError) as error:
            raise GoogleMapsReviewRpcError("Maps review RPC returned malformed JSON") from error
        return self._parse_review_rpc_payload(payload)

    def fetch_latest_review(self, cid: str) -> GoogleMapsReviewPage:
        """Fetches the newest review through the live qv9Egd RPC without DOM parsing."""
        if self._last_bootstrap_context is None:
            raise GoogleMapsReviewRpcError("Review RPC requires a successful Maps search bootstrap")
        kei, source_path = self._last_bootstrap_context
        contexts = (
            [self._review_client_context]
            if self._review_client_context is not None
            else [81, 0]
        )
        errors: list[str] = []
        for client_context in contexts:
            try:
                result = self._post_review_rpc(cid, kei, source_path, client_context)
                self._review_client_context = client_context
                return result
            except GoogleMapsReviewRpcError as error:
                errors.append(str(error))
                if "rejected context with status 3" not in str(error):
                    raise
        raise GoogleMapsReviewRpcError("; ".join(errors))

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
        page_size: int = 20,
    ) -> List[Lead]:
        """Fetches one page of records using session-cached pb template."""
        # 1. Fast path: reuse established session pb template to avoid downloading 220KB HTML
        if self._session_base_pb is not None and self._session_pb_uses < 300:
            self._session_pb_uses += 1
            encoded_kw = urllib.parse.quote_plus(keyword)
            pb = self._session_base_pb
            pb = re.sub(r"!1s[^!]+", f"!1s{encoded_kw}", pb, count=1)
            pb = re.sub(r"!2d[-0-9.]+", f"!2d{lng}", pb, count=1)
            pb = re.sub(r"!3d[-0-9.]+", f"!3d{lat}", pb, count=1)
            if start_index > 0:
                pb = re.sub(r"!8i\d+", f"!8i{start_index}", pb, count=1)

            query_params = {
                "tbm": "map",
                "authuser": "0",
                "hl": "en",
                "gl": "us",
                "q": keyword,
                "pb": pb,
            }
            payload_url = f"{GMAPS_BOOTSTRAP_ORIGIN}/search?{urllib.parse.urlencode(query_params)}"
            headers = {
                **DEFAULT_HEADERS,
                "accept": "*/*",
                "referer": self._session_bootstrap_url or "https://www.google.com/maps",
            }
            try:
                response = self._get_google(payload_url, headers=headers)
                if response.status_code == 200:
                    clean_text = response.text.lstrip()
                    if clean_text.startswith(")]}'"):
                        clean_text = clean_text[4:].lstrip()
                    try:
                        raw_data = json.loads(clean_text)
                        leads = self._extract_leads_from_rpc_data(raw_data, keyword, lat, lng)
                        if leads:
                            return leads
                    except json.JSONDecodeError:
                        pass
            except (GoogleMapsThrottleError, GoogleMapsChallengeError):
                raise
            except Exception:
                pass

        # 2. Bootstrap path: initialize or refresh session template
        try:
            bootstrap_url, base_payload_url = self._discover_payload_url(keyword, lat, lng)
            q_dict = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(base_payload_url).query))
            if "pb" in q_dict:
                self._session_base_pb = q_dict["pb"]
                self._session_bootstrap_url = bootstrap_url
                self._session_pb_uses = 1

            payload_url = self._payload_url_with_offset(
                base_payload_url, start_index=start_index, page_size=page_size
            )
            headers = {
                **DEFAULT_HEADERS,
                "accept": "*/*",
                "referer": bootstrap_url,
            }
            response = self._get_google(payload_url, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Direct Maps endpoint returned HTTP {response.status_code}"
                )
            clean_text = response.text.lstrip()
            if clean_text.startswith(")]}'"):
                clean_text = clean_text[4:].lstrip()
            try:
                raw_data = json.loads(clean_text)
            except json.JSONDecodeError as e:
                raise RuntimeError("Direct endpoint returned malformed JSON") from e
            return self._extract_leads_from_rpc_data(raw_data, keyword, lat, lng)
        except Exception as e:
            if isinstance(e, (GoogleMapsThrottleError, GoogleMapsChallengeError)):
                raise
            logger.error("Failed to fetch Maps page: %s", self._safe_error(e))
            raise

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

        # 3. Rating and review count: p[4][7] is rating and p[4][8]
        # is the true review count. p[37][1] is the photo count.
        rating = None
        reviews_count = 0
        review_count_available = False
        if len(p) > 4 and isinstance(p[4], list) and len(p[4]) > 7:
            try:
                rating = float(p[4][7]) if p[4][7] is not None else None
            except (ValueError, TypeError):
                pass
        if len(p) > 4 and isinstance(p[4], list) and len(p[4]) > 8:
            try:
                if p[4][8] is not None:
                    reviews_count = int(p[4][8])
                    review_count_available = True
            except (ValueError, TypeError):
                pass
        # Fallback: check p[4][3] which often contains ['https://...', '27 reviews', ...]
        if not review_count_available and len(p) > 4 and isinstance(p[4], list) and len(p[4]) > 3:
            sub = p[4][3]
            if isinstance(sub, list) and len(sub) > 1 and isinstance(sub[1], str):
                match = re.search(r"(\d[\d,]*)\s+reviews?", sub[1], flags=re.IGNORECASE)
                if match:
                    try:
                        reviews_count = int(match.group(1).replace(",", ""))
                        review_count_available = True
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

        # 9. Operating Hours Schedule (p[203])
        operating_hours: Dict[str, str] = {}
        if len(p) > 203 and isinstance(p[203], list):
            hours_data = p[203]
            if len(hours_data) > 0 and isinstance(hours_data[0], list):
                for day_entry in hours_data[0]:
                    if isinstance(day_entry, list) and len(day_entry) > 3:
                        day_name = day_entry[0] if isinstance(day_entry[0], str) else None
                        hours_list = day_entry[3] if isinstance(day_entry[3], list) else []
                        if day_name and hours_list and len(hours_list) > 0 and isinstance(hours_list[0], list):
                            time_str = hours_list[0][0] if len(hours_list[0]) > 0 and isinstance(hours_list[0][0], str) else None
                            if time_str:
                                operating_hours[day_name] = time_str
        has_operating_hours = len(operating_hours) > 0

        # 10. Closure Status (p[88])
        is_permanently_closed = False
        is_temporarily_closed = False
        business_status = "OPERATIONAL"
        if len(p) > 88 and isinstance(p[88], list) and len(p[88]) > 0:
            raw_status = p[88][0]
            if isinstance(raw_status, str):
                upper_status = raw_status.upper()
                if "CLOSED" in upper_status:
                    if "TEMP" in upper_status:
                        is_temporarily_closed = True
                        business_status = "CLOSED_TEMPORARILY"
                    else:
                        is_permanently_closed = True
                        business_status = "CLOSED_PERMANENTLY"

        # 11. Verified GBP Owner (p[57])
        is_claimed_owner = False
        if len(p) > 57 and isinstance(p[57], list) and len(p[57]) > 1:
            if isinstance(p[57][1], str) and "(Owner)" in p[57][1]:
                is_claimed_owner = True

        is_claimed = ClaimedStatus.CLAIMED if is_claimed_owner else ClaimedStatus.UNKNOWN

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
            review_count_available=review_count_available,
            is_claimed=is_claimed,
            is_claimed_owner=is_claimed_owner,
            operating_hours=operating_hours,
            business_status=business_status,
            has_operating_hours=has_operating_hours,
            is_permanently_closed=is_permanently_closed,
            is_temporarily_closed=is_temporarily_closed,
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
