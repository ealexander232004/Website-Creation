"""Focused Google Maps enrichment for the no-website, yes-email warehouse.

The search phase reuses :class:`GoogleMapsRpcClient`, whose Google requests are
proxy-enforced. Matching uses a high-recall, name-dominant policy: normalized
business name contributes 85% and coarse locality contributes 15%. Review count
comes from the structured search entity and newest-review time comes from Maps'
structured qv9Egd review RPC.
"""

from __future__ import annotations

import json
import math
import random
import re
import threading
import time
import unicodedata
import urllib.parse
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Iterable, Optional, Sequence

import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from models import Lead
from captcha_handler import CaptchaHandler
from proxy_manager import ProxyRoute
from rpc_client import (
    DEFAULT_HEADERS,
    GoogleMapsChallengeError,
    GoogleMapsPayloadDiscoveryError,
    GoogleMapsRpcClient,
    GoogleMapsThrottleError,
)


LEGAL_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "llc",
    "llp",
    "lp",
    "ltd",
    "limited",
    "pc",
    "pllc",
}
GENERIC_NAME_TOKENS = LEGAL_SUFFIXES | {
    "and",
    "at",
    "by",
    "center",
    "centre",
    "company",
    "group",
    "home",
    "market",
    "of",
    "realty",
    "realtor",
    "salon",
    "service",
    "services",
    "shop",
    "solutions",
    "spa",
    "store",
    "the",
}

# Binary, deliberately recall-favoring policy selected by replaying the prior
# 5,000-row run. The version and cutoff are stored with every new decision so
# downstream consumers can reproduce the decision from match_score.
MATCH_POLICY_VERSION = "binary_name85_location15_v1"
MATCH_THRESHOLD = 0.65


@dataclass(frozen=True)
class EnrichmentJob:
    entity_id: int
    canonical_name: str
    street_address: Optional[str]
    city: Optional[str]
    region: Optional[str]
    postcode: Optional[str]
    country: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass(frozen=True)
class WebsiteJob:
    entity_id: int
    website_url: str


@dataclass(frozen=True)
class CandidateAssessment:
    lead: Lead
    name_score: float
    address_score: float
    distance_meters: Optional[float]
    composite_score: float
    location_evidence: bool
    strong_location_evidence: bool
    meaningful_name_overlap: float
    meaningful_name_containment: bool
    reason: str


@dataclass(frozen=True)
class MatchDecision:
    status: str
    best: Optional[CandidateAssessment]
    candidates: Sequence[CandidateAssessment]
    reason: str


@dataclass(frozen=True)
class ReviewMetadata:
    review_count: Optional[int]
    latest_review_at: Optional[datetime]
    website_url: Optional[str]
    source: str
    is_operational: Optional[bool] = None
    has_operating_hours: Optional[bool] = None
    is_claimed_owner: Optional[bool] = None
    is_permanently_closed: Optional[bool] = None
    is_temporarily_closed: Optional[bool] = None
    current_status: Optional[str] = None
    regular_hours: Optional[dict[str, str]] = None
    special_hours_notice: Optional[str] = None

@dataclass(frozen=True)
class WebsiteVerification:
    verified: Optional[bool]
    status: Optional[str]
    checked_at: Optional[datetime]


class RunAborted(RuntimeError):
    """Raised inside a worker after the shared throttle controller aborts."""


class ProxyRateLimiter:
    """Spaces logical Maps searches across every worker sharing one proxy."""

    def __init__(self, requests_per_second: float) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero")
        self.interval_seconds = 1.0 / requests_per_second
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def acquire(self, controller: "ThrottleController") -> bool:
        with self._lock:
            now = time.monotonic()
            scheduled = max(now, self._next_allowed)
            self._next_allowed = scheduled + self.interval_seconds
        return controller.wait(scheduled - now)


class ThrottleController:
    """Coordinates proxy cooldowns and aborts on sustained Google throttling."""

    def __init__(
        self,
        window_size: int = 100,
        minimum_events: int = 30,
        rate_threshold: float = 0.35,
        consecutive_limit: int = 15,
    ) -> None:
        self.window_size = window_size
        self.minimum_events = minimum_events
        self.rate_threshold = rate_threshold
        self.consecutive_limit = consecutive_limit
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._recent: deque[bool] = deque(maxlen=window_size)
        self._consecutive_throttles = 0
        self._total_search_attempts = 0
        self._throttle_events = 0
        self._abort_reason: Optional[str] = None

    @property
    def stop_requested(self) -> bool:
        return self._stop.is_set()

    @property
    def abort_reason(self) -> Optional[str]:
        with self._lock:
            return self._abort_reason

    def abort(self, reason: str) -> None:
        with self._lock:
            if self._abort_reason is None:
                self._abort_reason = reason
            self._stop.set()

    def wait_for_route(self, route: ProxyRoute) -> bool:
        while not self.stop_requested:
            remaining = route.cooldown_until - time.time()
            if remaining <= 0:
                return True
            self._stop.wait(min(1.0, remaining))
        return False

    def wait(self, seconds: float) -> bool:
        """Waits interruptibly; returns False when an abort was requested."""
        return not self._stop.wait(max(0.0, seconds))

    def _record_outcome(self, throttled: bool) -> None:
        self._recent.append(throttled)
        self._total_search_attempts += 1
        if throttled:
            self._throttle_events += 1
            self._consecutive_throttles += 1
        else:
            self._consecutive_throttles = 0

        rolling_rate = sum(self._recent) / len(self._recent) if self._recent else 0.0
        if self._consecutive_throttles >= self.consecutive_limit:
            self.abort(
                f"hard throttle: {self._consecutive_throttles} consecutive throttled searches"
            )
        elif len(self._recent) >= self.minimum_events and rolling_rate >= self.rate_threshold:
            self.abort(
                "hard throttle: "
                f"{sum(self._recent)}/{len(self._recent)} recent searches throttled "
                f"({rolling_rate:.1%})"
            )

    def record_success(self, route: ProxyRoute, challenge_detected: bool = False) -> None:
        with self._lock:
            if challenge_detected:
                route.mark_failure(base_cooldown=15.0)
            else:
                route.mark_success()
            self._record_outcome(challenge_detected)

    def record_failure(
        self,
        route: ProxyRoute,
        error: Exception,
        challenge_detected: bool = False,
    ) -> bool:
        throttled = challenge_detected or isinstance(
            error,
            (GoogleMapsThrottleError, GoogleMapsChallengeError),
        )
        payload_discovery_miss = isinstance(error, GoogleMapsPayloadDiscoveryError)
        with self._lock:
            if not payload_discovery_miss:
                route.mark_failure(base_cooldown=30.0 if throttled else 5.0)
            self._record_outcome(throttled)
        return throttled

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            rolling_rate = sum(self._recent) / len(self._recent) if self._recent else 0.0
            return {
                "search_attempts": self._total_search_attempts,
                "throttle_events": self._throttle_events,
                "rolling_window": len(self._recent),
                "rolling_throttle_rate": rolling_rate,
                "consecutive_throttles": self._consecutive_throttles,
                "aborted": self.stop_requested,
                "abort_reason": self._abort_reason,
            }


@dataclass
class WorkerStats:
    worker_number: int
    processed: int = 0
    matched: int = 0
    not_found: int = 0
    failed: int = 0
    requeued: int = 0
    search_attempts: int = 0
    retries: int = 0
    payload_session_resets: int = 0
    throttled_searches: int = 0
    review_attempts: int = 0
    review_retries: int = 0
    review_counts_found: int = 0
    latest_reviews_found: int = 0
    empty_review_payloads: int = 0
    failed_review_requests: int = 0
    throttled_review_requests: int = 0
    captchas_detected: int = 0
    captchas_solved: int = 0
    captchas_failed: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class WebsiteWorkerStats:
    worker_number: int
    processed: int = 0
    live: int = 0
    errors: int = 0
    requeued: int = 0
    error_samples: list[str] = field(default_factory=list)


def _ascii_fold(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character))


def normalize_text(value: Optional[str]) -> str:
    value = _ascii_fold(value).lower().replace("&", " and ")
    value = re.sub(r"\b(?:d/b/a|dba)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def normalize_business_name(value: Optional[str]) -> str:
    tokens = normalize_text(value).split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set, right_set = set(left), set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def name_similarity(left: Optional[str], right: Optional[str]) -> float:
    left_normalized = normalize_business_name(left)
    right_normalized = normalize_business_name(right)
    if not left_normalized or not right_normalized:
        return 0.0
    if left_normalized == right_normalized:
        return 1.0

    sequence = SequenceMatcher(None, left_normalized, right_normalized).ratio()
    left_tokens = left_normalized.split()
    right_tokens = right_normalized.split()
    shorter_phrase = left_normalized if len(left_tokens) <= len(right_tokens) else right_normalized
    longer_phrase = right_normalized if len(left_tokens) <= len(right_tokens) else left_normalized
    phrase_containment = 0.96 if len(shorter_phrase.split()) >= 2 and shorter_phrase in longer_phrase else 0.0
    token_sort = SequenceMatcher(
        None,
        " ".join(sorted(left_tokens)),
        " ".join(sorted(right_tokens)),
    ).ratio()
    token_overlap = _jaccard(left_tokens, right_tokens)
    containment = min(len(left_tokens), len(right_tokens)) / max(len(left_tokens), len(right_tokens))
    if set(left_tokens) <= set(right_tokens) or set(right_tokens) <= set(left_tokens):
        containment = max(containment, 0.90)
    return min(
        1.0,
        max(sequence, token_sort, phrase_containment, 0.72 * token_overlap + 0.28 * containment),
    )


def _meaningful_name_tokens(value: Optional[str]) -> set[str]:
    return {
        token
        for token in normalize_business_name(value).split()
        if len(token) >= 3 and token not in GENERIC_NAME_TOKENS
    }


def _meaningful_name_agreement(
    source_name: Optional[str],
    candidate_name: Optional[str],
) -> tuple[float, bool]:
    source_tokens = _meaningful_name_tokens(source_name)
    candidate_tokens = _meaningful_name_tokens(candidate_name)
    if not source_tokens or not candidate_tokens:
        return 0.0, False
    overlap = len(source_tokens & candidate_tokens) / len(source_tokens | candidate_tokens)
    containment = source_tokens <= candidate_tokens or candidate_tokens <= source_tokens
    return overlap, containment


def _postcode_root(value: Optional[str]) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
    if len(normalized) >= 5 and normalized[:5].isdigit():
        return normalized[:5]
    return normalized


def _haversine_meters(
    left_latitude: Optional[float],
    left_longitude: Optional[float],
    right_latitude: Optional[float],
    right_longitude: Optional[float],
) -> Optional[float]:
    if None in (left_latitude, left_longitude, right_latitude, right_longitude):
        return None
    radius_meters = 6_371_008.8
    lat1, lat2 = math.radians(float(left_latitude)), math.radians(float(right_latitude))
    delta_latitude = lat2 - lat1
    delta_longitude = math.radians(float(right_longitude) - float(left_longitude))
    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_longitude / 2) ** 2
    )
    return 2 * radius_meters * math.asin(math.sqrt(haversine))


def build_location(job: EnrichmentJob) -> str:
    locality_parts = [part.strip() for part in (job.city, job.region, job.postcode) if part and part.strip()]
    if locality_parts:
        return " ".join(locality_parts)
    fallback_parts = [part.strip() for part in (job.street_address, job.country) if part and part.strip()]
    return " ".join(fallback_parts)


def build_search_query(job: EnrichmentJob) -> str:
    """Build the requested ``{Business name} {Location}`` query."""
    return " ".join(part for part in (job.canonical_name.strip(), build_location(job)) if part).strip()


def _address_assessment(job: EnrichmentJob, lead: Lead) -> tuple[float, bool, bool, list[str]]:
    """Scores only coarse locality; street-level evidence is intentionally ignored."""
    score = 0.0
    reasons: list[str] = []
    source_postcode = _postcode_root(job.postcode)
    candidate_postcode = _postcode_root(lead.zip_code)
    postcode_match = bool(source_postcode and candidate_postcode and source_postcode == candidate_postcode)
    if postcode_match:
        score += 0.45
        reasons.append("postcode")

    source_city = normalize_text(job.city)
    candidate_city = normalize_text(lead.city)
    candidate_address = normalize_text(lead.full_address)
    city_match = bool(source_city and (source_city == candidate_city or source_city in candidate_address))
    if city_match:
        score += 0.35
        reasons.append("city")

    source_region = normalize_text(job.region)
    candidate_region = normalize_text(lead.state)
    region_match = bool(source_region and (source_region == candidate_region or source_region in candidate_address))
    if region_match:
        score += 0.20
        reasons.append("region")

    location_evidence = postcode_match or city_match or region_match
    strong_location = postcode_match or (city_match and region_match)
    return min(score, 1.0), location_evidence, strong_location, reasons


def assess_candidate(job: EnrichmentJob, lead: Lead) -> CandidateAssessment:
    name_score = name_similarity(job.canonical_name, lead.name)
    meaningful_overlap, meaningful_containment = _meaningful_name_agreement(
        job.canonical_name,
        lead.name,
    )
    address_score, location_evidence, strong_location, reasons = _address_assessment(job, lead)
    distance = _haversine_meters(job.latitude, job.longitude, lead.latitude, lead.longitude)

    if distance is None:
        geo_score = 0.0
    elif distance <= 250:
        geo_score = 1.0
        reasons.append("within_250m")
        strong_location = True
        location_evidence = True
    elif distance <= 1_000:
        geo_score = 0.85
        reasons.append("within_1km")
        strong_location = True
        location_evidence = True
    elif distance <= 5_000:
        geo_score = 0.60
        reasons.append("within_5km")
        location_evidence = True
    elif distance <= 25_000:
        geo_score = 0.25
    else:
        geo_score = 0.0

    rough_location_score = max(address_score, geo_score)
    composite = min(1.0, 0.85 * name_score + 0.15 * rough_location_score)
    return CandidateAssessment(
        lead=lead,
        name_score=name_score,
        address_score=address_score,
        distance_meters=distance,
        composite_score=composite,
        location_evidence=location_evidence,
        strong_location_evidence=strong_location,
        meaningful_name_overlap=meaningful_overlap,
        meaningful_name_containment=meaningful_containment,
        reason=",".join(reasons) or "name_only",
    )


def choose_match(job: EnrichmentJob, leads: Sequence[Lead]) -> MatchDecision:
    if not leads:
        return MatchDecision("not_found", None, (), "search_returned_no_candidates")

    assessments = sorted(
        (assess_candidate(job, lead) for lead in leads),
        key=lambda assessment: assessment.composite_score,
        reverse=True,
    )
    best = assessments[0]
    if best.composite_score >= MATCH_THRESHOLD:
        return MatchDecision("matched", best, assessments, "binary_score_at_or_above_threshold")
    return MatchDecision("not_found", best, assessments, "binary_score_below_threshold")


def candidate_snapshot(assessments: Sequence[CandidateAssessment], limit: int = 5) -> list[dict[str, Any]]:
    snapshot: list[dict[str, Any]] = []
    for assessment in assessments[:limit]:
        snapshot.append(
            {
                "place_id": assessment.lead.place_id,
                "name": assessment.lead.name,
                "address": assessment.lead.full_address,
                "website": assessment.lead.website_raw,
                "name_score": round(assessment.name_score, 6),
                "address_score": round(assessment.address_score, 6),
                "rough_location_score": round(assessment.address_score, 6),
                "meaningful_name_overlap": round(assessment.meaningful_name_overlap, 6),
                "meaningful_name_containment": assessment.meaningful_name_containment,
                "distance_meters": (
                    round(assessment.distance_meters, 1)
                    if assessment.distance_meters is not None
                    else None
                ),
                "composite_score": round(assessment.composite_score, 6),
            }
        )
    return snapshot


def fetch_official_review_metadata(
    client: GoogleMapsRpcClient,
    place_id: str,
    api_key: Optional[str],
) -> ReviewMetadata:
    """Fetch verified review metadata, asking Legacy Details for newest first.

    The request deliberately uses the worker's proxy-enforced HTTP session.  If
    no key is configured, review fields remain NULL instead of substituting an
    unrelated counter from the anonymous Maps payload.
    """
    if not api_key:
        return ReviewMetadata(None, None, None, "unavailable_no_api_key")

    parameters = {
        "place_id": place_id,
        "fields": "place_id,website,user_ratings_total,reviews",
        "reviews_sort": "newest",
        "language": "en",
        "key": api_key,
    }
    url = "https://maps.googleapis.com/maps/api/place/details/json?" + urllib.parse.urlencode(parameters)
    response = client._get(
        url,
        headers={
            **DEFAULT_HEADERS,
            "accept": "application/json",
            "referer": "https://www.google.com/maps",
        },
    )
    if response.status_code != 200:
        return ReviewMetadata(None, None, None, f"places_api_http_{response.status_code}")
    payload = response.json()
    status = str(payload.get("status") or "UNKNOWN")
    if status != "OK":
        return ReviewMetadata(None, None, None, f"places_api_{status.lower()}")

    result = payload.get("result") or {}
    raw_count = result.get("user_ratings_total")
    review_count = int(raw_count) if isinstance(raw_count, (int, float)) and raw_count >= 0 else None
    latest_review_at: Optional[datetime] = None
    reviews = result.get("reviews") or []
    if reviews and isinstance(reviews[0], dict):
        raw_timestamp = reviews[0].get("time")
        if isinstance(raw_timestamp, (int, float)) and raw_timestamp > 0:
            latest_review_at = datetime.fromtimestamp(raw_timestamp, tz=timezone.utc)
    website = result.get("website") if isinstance(result.get("website"), str) else None
    return ReviewMetadata(review_count, latest_review_at, website, "places_api_legacy_newest")


def fetch_internal_review_metadata(
    client: GoogleMapsRpcClient,
    lead: Lead,
) -> ReviewMetadata:
    """Extracts review count, operational hours, and claim status directly from search entity."""
    del client
    review_count = int(lead.reviews_count) if lead.review_count_available else None
    source = (
        "maps_search_structured"
        if lead.review_count_available
        else "maps_search_unlisted_or_zero"
    )
    return ReviewMetadata(
        review_count=review_count,
        latest_review_at=None,
        website_url=None,
        source=source,
        is_operational=lead.is_operational,
        has_operating_hours=lead.has_operating_hours,
        is_claimed_owner=lead.is_claimed_owner,
        is_permanently_closed=lead.is_permanently_closed,
        is_temporarily_closed=lead.is_temporarily_closed,
        current_status=lead.current_status,
        regular_hours=lead.operating_hours if lead.operating_hours else None,
        special_hours_notice=lead.special_hours_notice,
    )


def _website_network_error_status(error: Exception) -> str:
    message = f"{type(error).__name__} {error}".lower()
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if any(token in message for token in ("ssl", "tls", "certificate")):
        return "tls_error"
    if "redirect" in message:
        return "too_many_redirects"
    return "network_error"


def verify_website(
    client: GoogleMapsRpcClient,
    website_url: Optional[str],
    max_attempts: int = 2,
) -> WebsiteVerification:
    """Checks reachability through the worker's proxy without semantic matching."""
    if not website_url:
        return WebsiteVerification(None, None, None)

    checked_at = datetime.now(timezone.utc)
    parsed = urllib.parse.urlsplit(website_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return WebsiteVerification(False, "invalid_url", checked_at)
    if parsed.hostname.lower() == "localhost" or parsed.hostname.lower().endswith(".local"):
        return WebsiteVerification(False, "invalid_url", checked_at)

    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client._get(
                website_url,
                headers={
                    "accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "no-cache",
                    "range": "bytes=0-65535",
                    "user-agent": DEFAULT_HEADERS["user-agent"],
                },
            )
            status_code = int(getattr(response, "status_code", 0) or 0)
            if 200 <= status_code < 400:
                return WebsiteVerification(True, "live", checked_at)
            if attempt < max_attempts and (status_code in {408, 425, 429} or status_code >= 500):
                time.sleep(min(3.0, (0.5 * (2 ** (attempt - 1))) + random.uniform(0.05, 0.35)))
                continue
            return WebsiteVerification(False, f"http_{status_code or 'unknown'}", checked_at)
        except Exception as error:
            last_error = error
            # TLS/certificate, redirect, DNS, and connection-refused failures
            # are deterministic for this reachability check. Only a timeout is
            # retried once; replaying every network error caused the prior run's
            # 60-90 second tail.
            if attempt < max_attempts and _website_network_error_status(error) == "timeout":
                time.sleep(min(3.0, (0.5 * (2 ** (attempt - 1))) + random.uniform(0.05, 0.35)))
                continue
            break

    return WebsiteVerification(
        False,
        _website_network_error_status(last_error or RuntimeError("unknown website error")),
        checked_at,
    )


class EnrichmentRepository:
    def __init__(self, connection_kwargs: dict[str, Any], pool_size: int = 25) -> None:
        if pool_size <= 0:
            raise ValueError("pool_size must be greater than zero")
        self.connection_kwargs = connection_kwargs
        self.pool_size = pool_size
        self.pool = ConnectionPool(
            kwargs={**connection_kwargs, "row_factory": dict_row},
            min_size=min(4, pool_size),
            max_size=pool_size,
            open=True,
            timeout=30.0,
            check=ConnectionPool.check_connection,
            name="google-maps-enrichment",
        )
        self.pool.wait(timeout=15.0)

    def connect(self) -> Any:
        """Borrow a pooled connection for one short database operation."""
        return self.pool.connection()

    def pool_stats(self) -> dict[str, int]:
        return dict(self.pool.get_stats())

    def close(self) -> None:
        self.pool.close()

    def create_run(
        self,
        requested_count: int,
        worker_count: int,
        website_worker_count: int,
        review_provider: str,
    ) -> uuid.UUID:
        run_id = uuid.uuid4()
        with self.connect() as connection:
            connection.execute(
                """
                insert into warehouse.google_maps_enrichment_runs (
                    run_id, status, requested_count, worker_count,
                    website_worker_count, review_provider
                ) values (%s, 'running', %s, %s, %s, %s)
                """,
                (run_id, requested_count, worker_count, website_worker_count, review_provider),
            )
        return run_id

    def enqueue(self, run_id: uuid.UUID, limit: int) -> int:
        with self.connect() as connection:
            rows = connection.execute(
                """
                insert into warehouse.google_maps_enrichment (entity_id, run_id, status)
                select qualified.entity_id, %s, 'queued'
                from warehouse.qualified_no_website_email_leads qualified
                where not exists (
                    select 1
                    from warehouse.google_maps_enrichment existing
                    where existing.entity_id = qualified.entity_id
                )
                order by qualified.entity_id
                limit %s
                on conflict (entity_id) do nothing
                returning entity_id
                """,
                (run_id, limit),
            ).fetchall()
            enqueued = len(rows)
            connection.execute(
                """
                update warehouse.google_maps_enrichment_runs
                set enqueued_count = %s
                where run_id = %s
                """,
                (enqueued, run_id),
            )
        return enqueued

    def prepare_resume(
        self,
        run_id: uuid.UUID,
        review_provider: str,
        retry_failed: bool = False,
        backfill_reviews: bool = False,
    ) -> int:
        resumable_statuses = ["in_progress"]
        if retry_failed:
            resumable_statuses.append("failed")
        with self.connect() as connection:
            run = connection.execute(
                "select run_id from warehouse.google_maps_enrichment_runs where run_id = %s",
                (run_id,),
            ).fetchone()
            if run is None:
                raise ValueError(f"Unknown enrichment run: {run_id}")
            connection.execute(
                """
                update warehouse.google_maps_enrichment
                set status = 'queued', worker_number = null, started_at = null,
                    error = null, updated_at = current_timestamp
                where run_id = %s
                  and (
                      status = any(%s)
                      or (%s and status = 'matched' and review_count is null)
                  )
                """,
                (run_id, resumable_statuses, backfill_reviews),
            )
            connection.execute(
                """
                update warehouse.google_maps_enrichment_runs
                set status = 'running', completed_at = null, summary = null,
                    error = null, review_provider = %s
                where run_id = %s
                """,
                (review_provider, run_id),
            )
            connection.execute(
                """
                update warehouse.google_maps_enrichment
                set website_check_state = 'queued', website_worker_number = null,
                    website_check_started_at = null, updated_at = current_timestamp
                where run_id = %s and website_check_state = 'in_progress'
                """,
                (run_id,),
            )
            pending = connection.execute(
                """
                select count(*) as count
                from warehouse.google_maps_enrichment
                where run_id = %s and status = 'queued'
                """,
                (run_id,),
            ).fetchone()["count"]
        return int(pending)

    @staticmethod
    def claim(connection: psycopg.Connection, run_id: uuid.UUID, worker_number: int) -> Optional[EnrichmentJob]:
        row = connection.execute(
            """
            with next_job as (
                select enrichment.entity_id
                from warehouse.google_maps_enrichment enrichment
                where enrichment.run_id = %s and enrichment.status = 'queued'
                order by enrichment.entity_id
                for update skip locked
                limit 1
            )
            update warehouse.google_maps_enrichment enrichment
            set status = 'in_progress',
                attempt_count = enrichment.attempt_count + 1,
                worker_number = %s,
                started_at = current_timestamp,
                updated_at = current_timestamp
            from next_job, warehouse.entities entity
            where enrichment.entity_id = next_job.entity_id
              and entity.entity_id = enrichment.entity_id
            returning
                entity.entity_id,
                entity.canonical_name,
                entity.street_address,
                entity.city,
                entity.region,
                entity.postcode,
                entity.country,
                entity.latitude,
                entity.longitude
            """,
            (run_id, worker_number),
        ).fetchone()
        connection.commit()
        if row is None:
            return None
        return EnrichmentJob(**row)

    @staticmethod
    def finish(
        connection: psycopg.Connection,
        job: EnrichmentJob,
        query: str,
        decision: MatchDecision,
        review_metadata: ReviewMetadata,
    ) -> None:
        best = decision.best
        # Candidate details remain in candidate_snapshot for audit. The best
        # candidate is associated at the top level only when its binary score
        # reaches the versioned cutoff.
        lead = best.lead if best and decision.status == "matched" else None
        exists = decision.status == "matched"
        website = review_metadata.website_url or (lead.website_raw if lead else None)
        google_website_found = website is not None if decision.status == "matched" else False
        if google_website_found:
            website_verification = WebsiteVerification(None, None, None)
            website_check_state = "queued"
        elif decision.status == "matched":
            website_verification = WebsiteVerification(
                False,
                "not_listed_on_google",
                datetime.now(timezone.utc),
            )
            website_check_state = "not_applicable"
        else:
            website_verification = WebsiteVerification(
                False,
                "business_not_found_on_google",
                datetime.now(timezone.utc),
            )
            website_check_state = "not_applicable"
        connection.execute(
            """
            update warehouse.google_maps_enrichment
            set status = %s,
                search_query = %s,
                candidate_count = %s,
                exists_on_google_maps = %s,
                google_maps_searched = true,
                google_website_found = %s,
                google_place_id = %s,
                google_cid = %s,
                google_name = %s,
                google_formatted_address = %s,
                google_latitude = %s,
                google_longitude = %s,
                google_maps_url = %s,
                website_url = %s,
                website_verified = %s,
                website_status = %s,
                website_checked_at = %s,
                website_check_state = %s,
                website_worker_number = null,
                website_check_attempt_count = 0,
                website_check_started_at = null,
                review_count = %s,
                latest_review_at = %s,
                review_metadata_source = %s,
                is_operational = %s,
                has_operating_hours = %s,
                is_claimed_owner = %s,
                is_permanently_closed = %s,
                is_temporarily_closed = %s,
                current_status = %s,
                regular_hours = %s,
                special_hours_notice = %s,
                match_score = %s,
                match_policy_version = %s,
                match_threshold = %s,
                name_score = %s,
                address_score = %s,
                distance_meters = %s,
                match_reason = %s,
                candidate_snapshot = %s,
                error = null,
                searched_at = current_timestamp,
                updated_at = current_timestamp
            where entity_id = %s
            """,
            (
                decision.status,
                query,
                len(decision.candidates),
                exists,
                google_website_found,
                lead.place_id if lead else None,
                lead.cid if lead else None,
                lead.name if lead else None,
                lead.full_address if lead else None,
                lead.latitude if lead else None,
                lead.longitude if lead else None,
                lead.maps_url if lead else None,
                website,
                website_verification.verified,
                website_verification.status,
                website_verification.checked_at,
                website_check_state,
                review_metadata.review_count,
                review_metadata.latest_review_at,
                review_metadata.source,
                review_metadata.is_operational,
                review_metadata.has_operating_hours,
                review_metadata.is_claimed_owner,
                review_metadata.is_permanently_closed,
                review_metadata.is_temporarily_closed,
                review_metadata.current_status,
                Jsonb(review_metadata.regular_hours) if review_metadata.regular_hours else None,
                review_metadata.special_hours_notice,
                best.composite_score if best else 0.0,
                MATCH_POLICY_VERSION,
                MATCH_THRESHOLD,
                best.name_score if best else None,
                best.address_score if best else None,
                best.distance_meters if best else None,
                f"{decision.reason};{best.reason if best else 'no_candidate'}",
                Jsonb(candidate_snapshot(decision.candidates)),
                job.entity_id,
            ),
        )
        connection.commit()

    @staticmethod
    def claim_website(
        connection: psycopg.Connection,
        run_id: uuid.UUID,
        worker_number: int,
    ) -> Optional[WebsiteJob]:
        row = connection.execute(
            """
            with next_job as (
                select entity_id
                from warehouse.google_maps_enrichment
                where run_id = %s and website_check_state = 'queued'
                order by entity_id
                for update skip locked
                limit 1
            )
            update warehouse.google_maps_enrichment enrichment
            set website_check_state = 'in_progress',
                website_worker_number = %s,
                website_check_attempt_count = enrichment.website_check_attempt_count + 1,
                website_check_started_at = current_timestamp,
                updated_at = current_timestamp
            from next_job
            where enrichment.entity_id = next_job.entity_id
            returning enrichment.entity_id, enrichment.website_url
            """,
            (run_id, worker_number),
        ).fetchone()
        connection.commit()
        if row is None:
            return None
        return WebsiteJob(**row)

    @staticmethod
    def finish_website(
        connection: psycopg.Connection,
        job: WebsiteJob,
        verification: WebsiteVerification,
    ) -> None:
        connection.execute(
            """
            update warehouse.google_maps_enrichment
            set website_verified = %s,
                website_status = %s,
                website_checked_at = %s,
                website_check_state = 'completed',
                updated_at = current_timestamp
            where entity_id = %s and website_check_state = 'in_progress'
            """,
            (
                verification.verified,
                verification.status,
                verification.checked_at,
                job.entity_id,
            ),
        )
        connection.commit()

    @staticmethod
    def requeue_website(connection: psycopg.Connection, entity_id: int) -> None:
        connection.execute(
            """
            update warehouse.google_maps_enrichment
            set website_check_state = 'queued', website_worker_number = null,
                website_check_started_at = null, updated_at = current_timestamp
            where entity_id = %s and website_check_state = 'in_progress'
            """,
            (entity_id,),
        )
        connection.commit()

    @staticmethod
    def requeue(
        connection: psycopg.Connection,
        entity_id: int,
        query: str,
        reason: str,
    ) -> None:
        connection.execute(
            """
            update warehouse.google_maps_enrichment
            set status = 'queued', worker_number = null, started_at = null,
                search_query = %s, error = %s,
                google_maps_searched = false, google_website_found = null,
                website_verified = null, website_status = null, website_checked_at = null,
                website_check_state = 'not_applicable', website_worker_number = null,
                website_check_attempt_count = 0,
                website_check_started_at = null,
                updated_at = current_timestamp
            where entity_id = %s
            """,
            (query, reason[:2_000], entity_id),
        )
        connection.commit()

    @staticmethod
    def fail(connection: psycopg.Connection, entity_id: int, query: str, error: Exception) -> None:
        message = f"{type(error).__name__}: {error}"[:2_000]
        connection.execute(
            """
            update warehouse.google_maps_enrichment
            set status = 'failed', search_query = %s, error = %s,
                google_maps_searched = false, google_website_found = null,
                website_verified = null, website_status = null, website_checked_at = null,
                website_check_state = 'not_applicable', website_worker_number = null,
                website_check_attempt_count = 0,
                website_check_started_at = null,
                searched_at = current_timestamp, updated_at = current_timestamp
            where entity_id = %s
            """,
            (query, message, entity_id),
        )
        connection.commit()

    @staticmethod
    def _summary(connection: psycopg.Connection, run_id: uuid.UUID) -> dict[str, Any]:
        status_rows = connection.execute(
            """
            select status, count(*) as count
            from warehouse.google_maps_enrichment
            where run_id = %s
            group by status
            order by status
            """,
            (run_id,),
        ).fetchall()
        website_status_rows = connection.execute(
            """
            select website_status, count(*) as count
            from warehouse.google_maps_enrichment
            where run_id = %s and website_status is not null
            group by website_status
            order by website_status
            """,
            (run_id,),
        ).fetchall()
        website_state_rows = connection.execute(
            """
            select website_check_state, count(*) as count
            from warehouse.google_maps_enrichment
            where run_id = %s
            group by website_check_state
            order by website_check_state
            """,
            (run_id,),
        ).fetchall()
        metrics = connection.execute(
            """
            select
                count(*) filter (where exists_on_google_maps) as exists_count,
                count(*) filter (where google_maps_searched) as google_maps_searched_count,
                count(*) filter (where google_website_found is true) as google_website_found_count,
                count(*) filter (where google_website_found is false) as google_website_not_found_count,
                count(*) filter (
                    where google_maps_searched and google_website_found is null
                ) as google_website_inconclusive_count,
                count(*) filter (where status = 'matched' and website_url is not null) as website_count,
                count(*) filter (where website_verified is true) as website_verified_count,
                count(*) filter (where website_verified is false) as website_negative_or_error_count,
                count(*) filter (where status = 'matched' and review_count is not null) as verified_review_count_rows,
                count(*) filter (where status = 'matched' and latest_review_at is not null) as latest_review_date_rows,
                avg(match_score) filter (where status = 'matched') as average_matched_score
            from warehouse.google_maps_enrichment
            where run_id = %s
            """,
            (run_id,),
        ).fetchone()
        return {
            "run_id": str(run_id),
            "statuses": {row["status"]: row["count"] for row in status_rows},
            "website_statuses": {
                row["website_status"]: row["count"] for row in website_status_rows
            },
            "website_check_states": {
                row["website_check_state"]: row["count"] for row in website_state_rows
            },
            **dict(metrics),
        }

    def progress(self, run_id: uuid.UUID) -> dict[str, Any]:
        with self.connect() as connection:
            return self._summary(connection, run_id)

    def complete_run(
        self,
        run_id: uuid.UUID,
        runtime: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            summary = self._summary(connection, run_id)
            if runtime:
                summary["runtime"] = runtime
            connection.execute(
                """
                update warehouse.google_maps_enrichment_runs
                set status = 'completed', completed_at = current_timestamp, summary = %s,
                    error = null
                where run_id = %s
                """,
                (Jsonb(summary), run_id),
            )
        return summary

    def abort_run(
        self,
        run_id: uuid.UUID,
        reason: str,
        throttle: dict[str, Any],
        runtime: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            summary = self._summary(connection, run_id)
            summary["throttle"] = throttle
            summary["aborted_reason"] = reason
            if runtime:
                summary["runtime"] = runtime
            connection.execute(
                """
                update warehouse.google_maps_enrichment_runs
                set status = 'aborted', completed_at = current_timestamp,
                    summary = %s, error = %s
                where run_id = %s
                """,
                (Jsonb(summary), reason[:2_000], run_id),
            )
        return summary


def run_maps_worker(
    repository: EnrichmentRepository,
    run_id: uuid.UUID,
    worker_number: int,
    route: ProxyRoute,
    api_key: Optional[str],
    captcha_api_key: Optional[str],
    throttle_controller: ThrottleController,
    rate_limiter: ProxyRateLimiter,
    timeout_seconds: float,
    max_attempts: int,
) -> WorkerStats:
    stats = WorkerStats(worker_number=worker_number)
    captcha_handler = CaptchaHandler(api_key=captcha_api_key)
    client = GoogleMapsRpcClient(
        proxy_url=route.raw_url,
        timeout=timeout_seconds,
        zoom_level=14,
        captcha_handler=captcha_handler,
    )
    try:
        while not throttle_controller.stop_requested:
            with repository.connect() as connection:
                job = repository.claim(connection, run_id, worker_number)
            if job is None:
                break
            query = build_search_query(job)
            try:
                leads: Sequence[Lead] = ()
                last_error: Optional[Exception] = None
                for attempt in range(1, max_attempts + 1):
                    if not throttle_controller.wait_for_route(route):
                        raise RunAborted(throttle_controller.abort_reason or "run aborted")
                    if not rate_limiter.acquire(throttle_controller):
                        raise RunAborted(throttle_controller.abort_reason or "run aborted")
                    captcha_before = client.captcha_detected
                    stats.search_attempts += 1
                    try:
                        leads = client.fetch_page(
                            keyword=query,
                            lat=job.latitude if job.latitude is not None else 39.8283,
                            lng=job.longitude if job.longitude is not None else -98.5795,
                            start_index=0,
                        )
                        challenge_detected = client.captcha_detected > captcha_before
                        throttle_controller.record_success(route, challenge_detected)
                        if challenge_detected:
                            stats.throttled_searches += 1
                        last_error = None
                        break
                    except Exception as error:  # network failures are retryable
                        last_error = error
                        challenge_detected = client.captcha_detected > captcha_before
                        throttled = throttle_controller.record_failure(
                            route,
                            error,
                            challenge_detected,
                        )
                        if throttled:
                            stats.throttled_searches += 1
                        if throttle_controller.stop_requested:
                            raise RunAborted(throttle_controller.abort_reason or "run aborted") from error
                        if isinstance(error, GoogleMapsPayloadDiscoveryError):
                            # This failure was concentrated in a single stale
                            # persistent session in the prior run. Retry it once
                            # with fresh cookies/connections; repeating it more
                            # than once only replays the same bad bootstrap.
                            if attempt < min(max_attempts, 2):
                                stats.retries += 1
                                stats.payload_session_resets += 1
                                client.reset_session()
                                if not throttle_controller.wait(random.uniform(0.25, 0.75)):
                                    raise RunAborted(
                                        throttle_controller.abort_reason or "run aborted"
                                    ) from error
                                continue
                            break
                        if attempt < max_attempts:
                            stats.retries += 1
                            backoff = min(
                                30.0,
                                float(2 ** (attempt - 1)) + random.uniform(0.15, 0.85),
                            )
                            if not throttle_controller.wait(backoff):
                                raise RunAborted(
                                    throttle_controller.abort_reason or "run aborted"
                                ) from error
                if last_error is not None:
                    raise last_error

                decision = choose_match(job, leads)
                metadata = ReviewMetadata(None, None, None, "not_applicable")
                if decision.status == "matched" and decision.best:
                    matched_lead = decision.best.lead
                    metadata = fetch_internal_review_metadata(client, matched_lead)
                    if metadata.review_count is not None:
                        stats.review_counts_found += 1

                    # Optional Places API key fallback if explicitly configured
                    if (
                        api_key
                        and matched_lead.place_id
                        and metadata.latest_review_at is None
                    ):
                        official = fetch_official_review_metadata(
                            client,
                            matched_lead.place_id,
                            api_key,
                        )
                        if official.latest_review_at is not None:
                            metadata = ReviewMetadata(
                                official.review_count
                                if official.review_count is not None
                                else metadata.review_count,
                                official.latest_review_at,
                                official.website_url,
                                f"{metadata.source}+places_api_legacy_fallback",
                                is_operational=metadata.is_operational,
                                current_status=metadata.current_status,
                                regular_hours=metadata.regular_hours,
                                is_claimed_owner=metadata.is_claimed_owner,
                                special_hours_notice=metadata.special_hours_notice,
                            )
                with repository.connect() as connection:
                    repository.finish(
                        connection,
                        job,
                        query,
                        decision,
                        metadata,
                    )
                stats.processed += 1
                if decision.status == "matched":
                    stats.matched += 1
                else:
                    stats.not_found += 1
            except RunAborted as error:
                with repository.connect() as connection:
                    repository.requeue(connection, job.entity_id, query, str(error))
                stats.requeued += 1
                break
            except Exception as error:
                with repository.connect() as connection:
                    repository.fail(connection, job.entity_id, query, error)
                stats.processed += 1
                stats.failed += 1
                if len(stats.errors) < 10:
                    stats.errors.append(f"entity_id={job.entity_id}: {type(error).__name__}: {error}")
    finally:
        stats.captchas_detected = client.captcha_detected
        stats.captchas_solved = client.captcha_solved
        stats.captchas_failed = client.captcha_failed
        client.close()
    return stats


def run_website_worker(
    repository: EnrichmentRepository,
    run_id: uuid.UUID,
    worker_number: int,
    route: ProxyRoute,
    maps_done: threading.Event,
    throttle_controller: ThrottleController,
    timeout_seconds: float,
    max_attempts: int,
) -> WebsiteWorkerStats:
    stats = WebsiteWorkerStats(worker_number=worker_number)
    client = GoogleMapsRpcClient(
        proxy_url=route.raw_url,
        timeout=timeout_seconds,
        zoom_level=14,
    )
    current_job: Optional[WebsiteJob] = None
    try:
        while not throttle_controller.stop_requested:
            with repository.connect() as connection:
                current_job = repository.claim_website(connection, run_id, worker_number)
            if current_job is None:
                if maps_done.is_set():
                    break
                maps_done.wait(0.20)
                continue

            try:
                verification = verify_website(
                    client,
                    current_job.website_url,
                    max_attempts=max_attempts,
                )
                with repository.connect() as connection:
                    repository.finish_website(connection, current_job, verification)
                stats.processed += 1
                if verification.verified:
                    stats.live += 1
                else:
                    stats.errors += 1
            except Exception as error:
                verification = WebsiteVerification(
                    False,
                    _website_network_error_status(error),
                    datetime.now(timezone.utc),
                )
                try:
                    with repository.connect() as connection:
                        repository.finish_website(connection, current_job, verification)
                    stats.processed += 1
                    stats.errors += 1
                except Exception:
                    with repository.connect() as connection:
                        repository.requeue_website(connection, current_job.entity_id)
                    stats.requeued += 1
                    raise
                if len(stats.error_samples) < 10:
                    stats.error_samples.append(
                        f"entity_id={current_job.entity_id}: {type(error).__name__}: {error}"
                    )
            finally:
                current_job = None
    finally:
        if current_job is not None:
            with repository.connect() as connection:
                repository.requeue_website(connection, current_job.entity_id)
            stats.requeued += 1
        client.close()
    return stats


def format_summary(summary: dict[str, Any]) -> str:
    return json.dumps(summary, indent=2, default=str, sort_keys=True)
