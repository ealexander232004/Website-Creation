from datetime import datetime, timezone

from facebook_last_post.database import decide_persistence
from facebook_last_post.models import FetchResult, FetchStatus


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _result(status: FetchStatus) -> FetchResult:
    return FetchResult(
        status=status,
        requested_url="https://www.facebook.com/Meta",
        final_url="https://www.facebook.com/Meta",
        checked_at=NOW,
    )


def test_access_control_becomes_terminal_blocked_state() -> None:
    decision = decide_persistence(
        _result(FetchStatus.LOGIN_REQUIRED),
        attempt_count=1,
        max_attempts=3,
    )

    assert decision.state == "blocked"
    assert decision.next_attempt_at is None


def test_transient_error_gets_bounded_retry() -> None:
    decision = decide_persistence(
        _result(FetchStatus.NETWORK_ERROR),
        attempt_count=1,
        max_attempts=3,
    )

    assert decision.state == "retry"
    assert decision.next_attempt_at is not None


def test_transient_error_exhausts_attempts() -> None:
    decision = decide_persistence(
        _result(FetchStatus.NETWORK_ERROR),
        attempt_count=3,
        max_attempts=3,
    )

    assert decision.state == "failed"
    assert decision.next_attempt_at is None


def test_oversized_document_is_not_retried() -> None:
    decision = decide_persistence(
        _result(FetchStatus.DOCUMENT_TOO_LARGE),
        attempt_count=1,
        max_attempts=3,
    )

    assert decision.state == "failed"
    assert decision.next_attempt_at is None
