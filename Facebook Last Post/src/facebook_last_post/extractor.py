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
