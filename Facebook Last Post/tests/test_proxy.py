from pathlib import Path

import pytest

from facebook_last_post.proxy import (
    load_proxy_urls,
    playwright_proxy,
    proxy_label,
    validate_proxy_url,
)


def test_proxy_label_never_contains_credentials() -> None:
    value = "http://user:secret@example.test:8001"
    label = proxy_label(value, 1)

    assert label == "proxy-01@example.test:8001"
    assert "user" not in label
    assert "secret" not in label


def test_playwright_proxy_splits_credentials() -> None:
    settings = playwright_proxy("http://user:p%40ss@example.test:8001")

    assert settings == {
        "server": "http://example.test:8001",
        "username": "user",
        "password": "p@ss",
    }


def test_proxy_file_skips_comments(tmp_path: Path) -> None:
    path = tmp_path / "proxies.txt"
    path.write_text("# private routes\nhttp://u:p@example.test:8001\n", encoding="utf-8")

    assert load_proxy_urls(path) == ["http://u:p@example.test:8001"]


@pytest.mark.parametrize(
    "value",
    ["", "ftp://example.test:21", "socks5://example.test:1080", "http://example.test"],
)
def test_invalid_proxy_url_fails_closed(value: str) -> None:
    with pytest.raises(ValueError):
        validate_proxy_url(value)
