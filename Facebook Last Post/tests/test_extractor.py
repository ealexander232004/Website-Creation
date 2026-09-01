from datetime import datetime, timezone

import pytest

from facebook_last_post.extractor import (
    EXTRACTION_METHOD,
    FacebookPublicDocumentClient,
    classify_public_document,
    extract_post_timestamps,
)
from facebook_last_post.models import FetchStatus


CHECKED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def _epoch(value: datetime) -> int:
    return int(value.timestamp())


def test_extracts_escaped_and_unescaped_structured_timestamps() -> None:
    older = datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc)
    newer = datetime(2026, 8, 31, 19, 25, 15, tzinfo=timezone.utc)
    document = (
        f'{{"publish_time":{_epoch(older)},'
        f'"nested":"{{\\"creation_time\\":{_epoch(newer)}}}"}}'
    )

    assert extract_post_timestamps(document, checked_at=CHECKED_AT) == [older, newer]


def test_converts_millisecond_epochs_and_ignores_generic_timestamp() -> None:
    expected = datetime(2026, 8, 31, 9, 0, tzinfo=timezone.utc)
    document = (
        f'{{"publish_time":{_epoch(expected) * 1000},'
        f'"timestamp":{_epoch(CHECKED_AT)}}}'
    )

    assert extract_post_timestamps(document, checked_at=CHECKED_AT) == [expected]


def test_ignores_implausible_future_timestamp() -> None:
    future = datetime(2030, 1, 1, tzinfo=timezone.utc)
    document = f'{{"publish_time":{_epoch(future)}}}'

    assert extract_post_timestamps(document, checked_at=CHECKED_AT) == []


def test_public_page_with_login_button_is_success_when_post_data_exists() -> None:
    post_time = datetime(2026, 8, 31, 19, 25, 15, tzinfo=timezone.utc)
    result = classify_public_document(
        requested_url="https://www.facebook.com/Meta/",
        final_url="https://www.facebook.com/Meta/",
        http_status=200,
        document=f'<button>Log in</button>{{"publish_time":{_epoch(post_time)}}}'.encode(),
        checked_at=CHECKED_AT,
        duration_ms=100,
        route_label="proxy-01@example:8001",
        max_document_bytes=10_000,
    )

    assert result.status is FetchStatus.OK
    assert result.last_post_at == post_time
    assert result.extraction_method == EXTRACTION_METHOD


def test_login_redirect_is_not_misclassified_as_no_posts() -> None:
    result = classify_public_document(
        requested_url="https://www.facebook.com/Meta/",
        final_url="https://www.facebook.com/login/",
        http_status=200,
        document=b"<html>Log into Facebook</html>",
        checked_at=CHECKED_AT,
        duration_ms=100,
        route_label="proxy-01@example:8001",
        max_document_bytes=10_000,
    )

    assert result.status is FetchStatus.LOGIN_REQUIRED
    assert result.last_post_at is None


def test_challenge_redirect_takes_precedence_over_embedded_noise() -> None:
    result = classify_public_document(
        requested_url="https://www.facebook.com/Meta/",
        final_url="https://www.facebook.com/checkpoint/123",
        http_status=200,
        document=b'{"publish_time":1788200000}',
        checked_at=CHECKED_AT,
        duration_ms=100,
        route_label="proxy-01@example:8001",
        max_document_bytes=10_000,
    )

    assert result.status is FetchStatus.CHALLENGE


def test_document_limit_is_enforced_before_parsing() -> None:
    result = classify_public_document(
        requested_url="https://www.facebook.com/Meta/",
        final_url="https://www.facebook.com/Meta/",
        http_status=200,
        document=b"x" * 101,
        checked_at=CHECKED_AT,
        duration_ms=100,
        route_label="proxy-01@example:8001",
        max_document_bytes=100,
    )

    assert result.status is FetchStatus.DOCUMENT_TOO_LARGE


def test_client_refuses_direct_network_mode() -> None:
    with pytest.raises(ValueError, match="direct-network fallback is disabled"):
        FacebookPublicDocumentClient(proxy_url="")


def test_http_error_is_not_misclassified_as_no_posts() -> None:
    result = classify_public_document(
        requested_url="https://www.facebook.com/Meta/",
        final_url="https://www.facebook.com/Meta/",
        http_status=400,
        document=b"<title>Error</title>",
        checked_at=CHECKED_AT,
        duration_ms=100,
        route_label="proxy-01@example:8001",
        max_document_bytes=10_000,
    )

    assert result.status is FetchStatus.HTTP_ERROR


def test_redirect_off_facebook_is_access_denied() -> None:
    result = classify_public_document(
        requested_url="https://www.facebook.com/Meta/",
        final_url="https://example.test/interstitial",
        http_status=200,
        document=b'{"publish_time":1788200000}',
        checked_at=CHECKED_AT,
        duration_ms=100,
        route_label="proxy-01@example:8001",
        max_document_bytes=10_000,
    )

    assert result.status is FetchStatus.ACCESS_DENIED
    assert result.last_post_at is None
