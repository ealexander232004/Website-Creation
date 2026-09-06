"""Bandwidth-bounded anonymous Facebook public-document fetcher.

The fetcher intentionally does not call undocumented GraphQL endpoints, log in,
solve challenges, or replay private browser requests. Chromium is used only for
the public top-level document; scripts, images, media, fonts, and stylesheets are
blocked. Post dates are read from structured timestamp fields embedded in that
document instead of brittle visual DOM selectors.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Iterable
from urllib.parse import urlparse

from .models import FetchResult, FetchStatus
from .normalization import normalize_facebook_profile
from .proxy import playwright_proxy, proxy_label, validate_proxy_url


EXTRACTION_METHOD = "embedded_public_document_timestamps_v1"
_FACEBOOK_EPOCH = int(datetime(2004, 2, 4, tzinfo=timezone.utc).timestamp())
_TIMESTAMP_FIELD_RE = re.compile(
    r"(?:(?:\\?\")|&quot;)"
    r"(?:creation_time|publish_time|creation_timestamp)"
    r"(?:(?:\\?\")|&quot;)\s*:\s*"
    r"(?:(?:\\?\")|&quot;)?(?P<epoch>\d{9,13})"
)
_UNAVAILABLE_MARKERS = (
    "this content isn't available",
    "this content is not available",
    "the link you followed may be broken",
    "page isn't available",
    "page is not available",
)
_RATE_LIMIT_MARKERS = (
    "temporarily blocked",
    "you’re temporarily blocked",
    "you're temporarily blocked",
    "too many requests",
)
_CHALLENGE_MARKERS = (
    "security check required",
    "confirm you're human",
    "confirm you are human",
)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def extract_post_timestamps(
    document: str | bytes,
    *,
    checked_at: datetime | None = None,
) -> list[datetime]:
    """Extract plausible post timestamps from structured public document data."""

    text = document.decode("utf-8", errors="replace") if isinstance(document, bytes) else document
    observed_at = checked_at or _utc_now()
    upper_bound = int((observed_at + timedelta(days=1)).timestamp())
    epochs: set[int] = set()

    for match in _TIMESTAMP_FIELD_RE.finditer(text):
        raw_epoch = int(match.group("epoch"))
        epoch = raw_epoch // 1000 if raw_epoch > 10_000_000_000 else raw_epoch
        if _FACEBOOK_EPOCH <= epoch <= upper_bound:
            epochs.add(epoch)

    return [datetime.fromtimestamp(epoch, tz=timezone.utc) for epoch in sorted(epochs)]


def classify_public_document(
    *,
    requested_url: str,
    final_url: str,
    http_status: int,
    document: bytes,
    checked_at: datetime,
    duration_ms: int,
    route_label: str,
    max_document_bytes: int,
) -> FetchResult:
    """Classify a fetched document without confusing access walls with no posts."""

    size = len(document)
    base = {
        "requested_url": requested_url,
        "final_url": final_url,
        "http_status": http_status,
        "checked_at": checked_at,
        "document_bytes": size,
        "duration_ms": duration_ms,
        "proxy_label": route_label,
    }
    parsed_final = urlparse(final_url)
    final_path = parsed_final.path.lower()
    final_host = (parsed_final.hostname or "").lower()

    if size > max_document_bytes:
        return FetchResult(
            FetchStatus.DOCUMENT_TOO_LARGE,
            error_code="document_limit",
            error_detail=f"public document exceeded {max_document_bytes} bytes",
            **base,
        )
    if http_status == 429:
        return FetchResult(FetchStatus.RATE_LIMITED, error_code="http_429", **base)
    if final_host != "facebook.com" and not final_host.endswith(".facebook.com"):
        return FetchResult(
            FetchStatus.ACCESS_DENIED,
            error_code="unexpected_final_host",
            error_detail="navigation left the facebook.com origin",
            **base,
        )
    if "/checkpoint" in final_path or "/captcha" in final_path:
        return FetchResult(FetchStatus.CHALLENGE, error_code="challenge_redirect", **base)
    if final_path == "/login" or final_path.startswith("/login/"):
        return FetchResult(FetchStatus.LOGIN_REQUIRED, error_code="login_redirect", **base)
    if http_status in {401, 403}:
        return FetchResult(FetchStatus.ACCESS_DENIED, error_code=f"http_{http_status}", **base)
    if http_status == 404:
        return FetchResult(FetchStatus.NOT_FOUND, error_code="http_404", **base)
    if http_status >= 400:
        return FetchResult(FetchStatus.HTTP_ERROR, error_code=f"http_{http_status}", **base)

    timestamps = extract_post_timestamps(document, checked_at=checked_at)
    if timestamps:
        return FetchResult(
            FetchStatus.OK,
            last_post_at=max(timestamps),
            extraction_method=EXTRACTION_METHOD,
            **base,
        )

    lowered = document.decode("utf-8", errors="ignore").lower()
    if any(marker in lowered for marker in _RATE_LIMIT_MARKERS):
        return FetchResult(FetchStatus.RATE_LIMITED, error_code="rate_limit_marker", **base)
    if any(marker in lowered for marker in _CHALLENGE_MARKERS):
        return FetchResult(FetchStatus.CHALLENGE, error_code="challenge_marker", **base)
    if any(marker in lowered for marker in _UNAVAILABLE_MARKERS):
        return FetchResult(FetchStatus.UNAVAILABLE, error_code="unavailable_marker", **base)

    return FetchResult(
        FetchStatus.NO_POST_TIMESTAMP,
        extraction_method=EXTRACTION_METHOD,
        error_code="no_supported_timestamp",
        error_detail="public document contained no supported post timestamp field",
        **base,
    )


class FacebookPublicDocumentClient:
    """Reusable Chromium session that fetches only public top-level documents."""

    def __init__(
        self,
        *,
        proxy_url: str,
        route_name: str | None = None,
        timeout_seconds: float = 35.0,
        min_interval_seconds: float = 5.0,
        max_document_bytes: int = 5_000_000,
    ) -> None:
        if not proxy_url:
            raise ValueError("a proxy is required; direct-network fallback is disabled")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds cannot be negative")
        if max_document_bytes < 1:
            raise ValueError("max_document_bytes must be positive")
        self.proxy_url = validate_proxy_url(proxy_url)
        self.route_name = route_name or proxy_label(proxy_url)
        self.timeout_seconds = timeout_seconds
        self.min_interval_seconds = min_interval_seconds
        self.max_document_bytes = max_document_bytes
        self._playwright = None
        self._browser = None
        self._context = None
        self._last_request_started = 0.0

    def __enter__(self) -> "FacebookPublicDocumentClient":
        from playwright.sync_api import sync_playwright

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                proxy=playwright_proxy(self.proxy_url),
                args=[
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-default-apps",
                    "--disable-domain-reliability",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--no-first-run",
                ],
            )
            self._context = self._browser.new_context(
                java_script_enabled=False,
                locale="en-US",
                service_workers="block",
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            )
        except Exception:
            if self._browser is not None:
                self._browser.close()
            if self._playwright is not None:
                self._playwright.stop()
            raise
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request_started
        remaining = self.min_interval_seconds - elapsed
        if self._last_request_started and remaining > 0:
            time.sleep(remaining)
        self._last_request_started = time.monotonic()

    def fetch(self, requested_url: str) -> FetchResult:
        if self._context is None:
            raise RuntimeError("FacebookPublicDocumentClient must be used as a context manager")

        target_url = normalize_facebook_profile(requested_url).normalized_url
        self._pace()
        checked_at = _utc_now()
        started = time.monotonic()
        page = self._context.new_page()
        def route_top_level_document(route) -> None:
            request = route.request
            if request.resource_type == "document" and request.frame == page.main_frame:
                route.continue_()
            else:
                route.abort()

        page.route("**/*", route_top_level_document)
        try:
            response = page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=int(self.timeout_seconds * 1000),
            )
            if response is None:
                raise RuntimeError("navigation completed without a document response")
            try:
                document = response.body()
            except Exception:
                # Chromium can evict the raw response body after some redirects.
                # The DOM is already loaded with JavaScript disabled and all
                # non-document requests blocked, so serializing it does not make
                # another network request or expand the scraper's surface.
                document = page.content().encode("utf-8")
            duration_ms = int((time.monotonic() - started) * 1000)
            return classify_public_document(
                requested_url=target_url,
                final_url=page.url,
                http_status=response.status,
                document=document,
                checked_at=checked_at,
                duration_ms=duration_ms,
                route_label=self.route_name,
                max_document_bytes=self.max_document_bytes,
            )
        except Exception as exc:  # Playwright errors are normalized for persistence.
            duration_ms = int((time.monotonic() - started) * 1000)
            return FetchResult(
                FetchStatus.NETWORK_ERROR,
                requested_url=target_url,
                final_url=page.url or None,
                checked_at=checked_at,
                duration_ms=duration_ms,
                error_code=type(exc).__name__,
                error_detail=str(exc).splitlines()[0][:500],
                proxy_label=self.route_name,
            )
        finally:
            try:
                page.close()
            except Exception:
                pass


def newest_timestamp(values: Iterable[datetime]) -> datetime | None:
    """Small helper kept public for downstream reporting code."""

    return max(values, default=None)


class FacebookTriageClient:
    """High-throughput HTTP client implementing 3 strategies:
    1. Wire Compression (gzip / deflate)
    2. Streaming Early-Abort socket disconnect on creation_time
    3. Two-Tier Mobile Triage (m.facebook.com -> desktop canonical SSR)
    """

    def __init__(
        self,
        *,
        proxy_url: str,
        route_name: str | None = None,
        timeout_seconds: float = 12.0,
        max_document_bytes: int = 2_000_000,
    ) -> None:
        if not proxy_url:
            raise ValueError("a proxy is required; direct-network fallback is disabled")
        self.proxy_url = validate_proxy_url(proxy_url)
        self.route_name = route_name or proxy_label(proxy_url)
        self.timeout_seconds = timeout_seconds
        self.max_document_bytes = max_document_bytes
        self.session = None

    def __enter__(self) -> "FacebookTriageClient":
        import requests

        self.session = requests.Session()
        self.session.proxies.update({"http": self.proxy_url, "https": self.proxy_url})
        try:
            self.session.get(
                "https://m.facebook.com/",
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                    "Accept-Encoding": "gzip, deflate",
                },
                timeout=self.timeout_seconds,
            )
        except Exception:
            pass
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None

    def _is_proxy_rate_limited(self) -> bool:
        """Check if Meta's edge firewall is redirecting all traffic from this proxy to /login/."""
        import requests
        try:
            resp = requests.get(
                "https://m.facebook.com/Meta",
                proxies={"http": self.proxy_url, "https": self.proxy_url},
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                },
                allow_redirects=True,
                timeout=10.0,
            )
            return "login" in resp.url.lower()
        except Exception:
            return False
    def fetch(self, requested_url: str) -> FetchResult:
        if self.session is None:
            raise RuntimeError("FacebookTriageClient must be used as a context manager")

        target_url = normalize_facebook_profile(requested_url).normalized_url
        checked_at = _utc_now()
        started = time.monotonic()
        document_bytes = 0

        # --- Stage 1: Mobile Triage Probe (~15-30 KB) ---
        m_url = target_url.replace("www.facebook.com", "m.facebook.com")
        try:
            resp_m = self.session.get(
                m_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                },
                allow_redirects=True,
                timeout=self.timeout_seconds,
            )
            document_bytes += len(resp_m.content)
        except Exception as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            return FetchResult(
                FetchStatus.NETWORK_ERROR,
                requested_url=target_url,
                final_url=None,
                checked_at=checked_at,
                duration_ms=duration_ms,
                error_code=type(exc).__name__,
                error_detail=str(exc).splitlines()[0][:500],
                proxy_label=self.route_name,
            )

        if resp_m.status_code == 404:
            duration_ms = int((time.monotonic() - started) * 1000)
            return FetchResult(
                FetchStatus.NOT_FOUND,
                requested_url=target_url,
                final_url=resp_m.url,
                checked_at=checked_at,
                http_status=404,
                document_bytes=document_bytes,
                duration_ms=duration_ms,
                proxy_label=self.route_name,
            )

        lowered_m = resp_m.text.lower()
        if any(marker in lowered_m for marker in _UNAVAILABLE_MARKERS):
            duration_ms = int((time.monotonic() - started) * 1000)
            return FetchResult(
                FetchStatus.UNAVAILABLE,
                requested_url=target_url,
                final_url=resp_m.url,
                checked_at=checked_at,
                http_status=resp_m.status_code,
                document_bytes=document_bytes,
                duration_ms=duration_ms,
                proxy_label=self.route_name,
            )

        # Extract OpenGraph metadata
        canonical_m = re.search(r'<meta[^>]*property=["\']og:url["\'][^>]*content=["\']([^"\']+)["\']', resp_m.text, re.IGNORECASE)
        canonical_url = canonical_m.group(1).strip() if canonical_m else None

        # If mobile redirected to login or canonical is /login/, verify via canary
        if "login" in resp_m.url.lower() or (canonical_url and "/login" in canonical_url.lower()):
            is_proxy_blocked = self._is_proxy_rate_limited()
            duration_ms = int((time.monotonic() - started) * 1000)
            if is_proxy_blocked:
                return FetchResult(
                    FetchStatus.RATE_LIMITED,
                    requested_url=target_url,
                    final_url=resp_m.url,
                    checked_at=checked_at,
                    http_status=resp_m.status_code,
                    document_bytes=document_bytes,
                    duration_ms=duration_ms,
                    error_code="proxy_rate_limited",
                    proxy_label=self.route_name,
                )
            return FetchResult(
                FetchStatus.LOGIN_REQUIRED,
                requested_url=target_url,
                final_url=resp_m.url,
                checked_at=checked_at,
                http_status=resp_m.status_code,
                document_bytes=document_bytes,
                duration_ms=duration_ms,
                error_code="account_restricted",
                proxy_label=self.route_name,
                canonical_url=canonical_url,
            )

        desc_m = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', resp_m.text, re.IGNORECASE)
        og_desc = desc_m.group(1).strip() if desc_m else ""

        likes_count = None
        talking_about_count = None
        was_here_count = None
        page_category = None

        if og_desc:
            likes_match = re.search(r'([\d,]+)\s+likes?', og_desc, re.IGNORECASE)
            if likes_match:
                try:
                    likes_count = int(likes_match.group(1).replace(",", ""))
                except Exception:
                    pass

            talking_match = re.search(r'([\d,]+)\s+talking about this', og_desc, re.IGNORECASE)
            if talking_match:
                try:
                    talking_about_count = int(talking_match.group(1).replace(",", ""))
                except Exception:
                    pass

            were_here_match = re.search(r'([\d,]+)\s+were here', og_desc, re.IGNORECASE)
            if were_here_match:
                try:
                    was_here_count = int(were_here_match.group(1).replace(",", ""))
                except Exception:
                    pass

            if "." in og_desc:
                cat_cand = og_desc.rsplit(".", 1)[-1].strip()
                if cat_cand and len(cat_cand) < 60 and not re.search(r'\d', cat_cand):
                    page_category = cat_cand

        # --- Stage 2: Desktop SSR with Gzip & Streaming Early-Abort ---
        desktop_target = canonical_url or target_url
        desktop_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            resp_desk = self.session.get(
                desktop_target,
                headers=desktop_headers,
                allow_redirects=True,
                stream=True,
                timeout=self.timeout_seconds,
            )
            final_url = resp_desk.url
            http_status = resp_desk.status_code

            if "login" in final_url.lower():
                resp_desk.close()
                is_proxy_blocked = self._is_proxy_rate_limited()
                duration_ms = int((time.monotonic() - started) * 1000)
                status = FetchStatus.RATE_LIMITED if is_proxy_blocked else FetchStatus.LOGIN_REQUIRED
                error_code = "proxy_rate_limited" if is_proxy_blocked else "account_restricted"
                return FetchResult(
                    status,
                    requested_url=target_url,
                    final_url=final_url,
                    checked_at=checked_at,
                    http_status=http_status,
                    document_bytes=document_bytes,
                    duration_ms=duration_ms,
                    error_code=error_code,
                    proxy_label=self.route_name,
                    canonical_url=canonical_url,
                    likes_count=likes_count,
                    talking_about_count=talking_about_count,
                    was_here_count=was_here_count,
                    page_category=page_category,
                )
            buffer = bytearray()
            timestamps = []
            bytes_streamed = 0

            for chunk in resp_desk.iter_content(chunk_size=32768):
                bytes_streamed += len(chunk)
                buffer.extend(chunk)
                if b'"creation_time"' in buffer or b'"publish_time"' in buffer:
                    timestamps = extract_post_timestamps(bytes(buffer), checked_at=checked_at)
                    if timestamps:
                        resp_desk.close()
                        break
                if bytes_streamed >= self.max_document_bytes:
                    resp_desk.close()
                    break

            document_bytes += bytes_streamed
            duration_ms = int((time.monotonic() - started) * 1000)

            if timestamps:
                return FetchResult(
                    FetchStatus.OK,
                    requested_url=target_url,
                    final_url=final_url,
                    checked_at=checked_at,
                    last_post_at=max(timestamps),
                    http_status=http_status,
                    extraction_method=EXTRACTION_METHOD,
                    document_bytes=document_bytes,
                    duration_ms=duration_ms,
                    proxy_label=self.route_name,
                    canonical_url=canonical_url,
                    likes_count=likes_count,
                    talking_about_count=talking_about_count,
                    was_here_count=was_here_count,
                    page_category=page_category,
                )

            return FetchResult(
                FetchStatus.NO_POST_TIMESTAMP,
                requested_url=target_url,
                final_url=final_url,
                checked_at=checked_at,
                http_status=http_status,
                extraction_method=EXTRACTION_METHOD,
                document_bytes=document_bytes,
                duration_ms=duration_ms,
                error_code="no_supported_timestamp",
                proxy_label=self.route_name,
                canonical_url=canonical_url,
                likes_count=likes_count,
                talking_about_count=talking_about_count,
                was_here_count=was_here_count,
                page_category=page_category,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            return FetchResult(
                FetchStatus.NETWORK_ERROR,
                requested_url=target_url,
                final_url=canonical_url or target_url,
                checked_at=checked_at,
                duration_ms=duration_ms,
                error_code=type(exc).__name__,
                error_detail=str(exc).splitlines()[0][:500],
                proxy_label=self.route_name,
                canonical_url=canonical_url,
                likes_count=likes_count,
                talking_about_count=talking_about_count,
                was_here_count=was_here_count,
                page_category=page_category,
            )
