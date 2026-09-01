import pytest

from facebook_last_post.normalization import (
    InvalidFacebookProfile,
    normalize_facebook_profile,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("123456789", "https://www.facebook.com/123456789"),
        ("@Meta", "https://www.facebook.com/Meta"),
        ("facebook.com/Meta/posts/123", "https://www.facebook.com/Meta"),
        ("https://m.facebook.com/Meta/?ref=page", "https://www.facebook.com/Meta"),
        (
            "https://www.facebook.com/profile.php?id=12345&ref=bookmarks",
            "https://www.facebook.com/profile.php?id=12345",
        ),
        (
            "https://facebook.com/pages/Example-Page/998877",
            "https://www.facebook.com/pages/Example-Page/998877",
        ),
    ],
)
def test_normalizes_account_references(raw: str, expected: str) -> None:
    assert normalize_facebook_profile(raw).normalized_url == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "https://example.com/Meta",
        "https://facebook.com/groups/123",
        "https://facebook.com/events/123",
        "https://facebook.com/reel/123",
        "https://facebook.com/profile.php?ref=missing-id",
    ],
)
def test_rejects_non_account_surfaces(raw: str) -> None:
    with pytest.raises(InvalidFacebookProfile):
        normalize_facebook_profile(raw)
