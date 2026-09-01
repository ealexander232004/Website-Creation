"""Credential-safe helpers for fixed outbound proxy routes."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse


def validate_proxy_url(proxy_url: str) -> str:
    candidate = proxy_url.strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("proxy URL must use http or https")
    if not parsed.hostname or not parsed.port:
        raise ValueError("proxy URL must include a host and port")
    return candidate


def load_proxy_urls(path: str | Path) -> list[str]:
    proxy_path = Path(path)
    values = [
        validate_proxy_url(line)
        for line in proxy_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not values:
        raise ValueError(f"no proxy URLs found in {proxy_path}")
    return values


def proxy_label(proxy_url: str | None, index: int | None = None) -> str:
    if not proxy_url:
        return "direct"
    parsed = urlparse(validate_proxy_url(proxy_url))
    route = f"{parsed.hostname}:{parsed.port}"
    return f"proxy-{index:02d}@{route}" if index is not None else route


def playwright_proxy(proxy_url: str | None) -> dict[str, str] | None:
    if not proxy_url:
        return None
    parsed = urlparse(validate_proxy_url(proxy_url))
    settings = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        settings["username"] = unquote(parsed.username)
    if parsed.password:
        settings["password"] = unquote(parsed.password)
    return settings
