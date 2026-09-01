"""Shared domain types for fetches and durable queue jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FetchStatus(StrEnum):
    """Outcome of one anonymous public-document request."""

    OK = "ok"
    NO_POST_TIMESTAMP = "no_post_timestamp"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    LOGIN_REQUIRED = "login_required"
    CHALLENGE = "challenge"
    ACCESS_DENIED = "access_denied"
    RATE_LIMITED = "rate_limited"
    HTTP_ERROR = "http_error"
    DOCUMENT_TOO_LARGE = "document_too_large"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"

    @property
    def is_access_control(self) -> bool:
        return self in {
            FetchStatus.LOGIN_REQUIRED,
            FetchStatus.CHALLENGE,
            FetchStatus.ACCESS_DENIED,
            FetchStatus.RATE_LIMITED,
        }


@dataclass(frozen=True, slots=True)
class FetchResult:
    status: FetchStatus
    requested_url: str
    final_url: str | None
    checked_at: datetime
    last_post_at: datetime | None = None
    http_status: int | None = None
    extraction_method: str | None = None
    document_bytes: int = 0
    duration_ms: int = 0
    error_code: str | None = None
    error_detail: str | None = None
    proxy_label: str | None = None


@dataclass(frozen=True, slots=True)
class ProfileJob:
    profile_id: int
    entity_id: int
    source: str
    input_handle_or_url: str
    normalized_url: str
    attempt_count: int


@dataclass(frozen=True, slots=True)
class RunSummary:
    claimed: int
    succeeded: int
    no_data: int
    unavailable: int
    blocked: int
    retried_or_failed: int
    halted_reason: str | None = None
