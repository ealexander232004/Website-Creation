"""Normalize warehouse Facebook identifiers into public account URLs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse


_ALLOWED_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "web.facebook.com",
    "business.facebook.com",
}
_NON_ACCOUNT_PREFIXES = {
    "events",
    "gaming",
    "groups",
    "help",
    "login",
    "marketplace",
    "photo",
    "reel",
    "share",
    "story.php",
    "watch",
}
_HANDLE_RE = re.compile(r"^[A-Za-z0-9._-]{2,200}$")


@dataclass(frozen=True, slots=True)
class NormalizedProfile:
    original: str
    normalized_url: str


class InvalidFacebookProfile(ValueError):
    """Raised when a social value is not a Facebook account/page reference."""


def normalize_facebook_profile(value: str) -> NormalizedProfile:
    """Return a canonical HTTPS URL for a Facebook account/page reference.

    Numeric Foursquare Facebook IDs and ordinary handles are accepted. Links to
    groups, events, individual posts, media, and login surfaces are rejected so
    the queue remains scoped to account pages.
    """

    original = value
    candidate = value.strip()
    if not candidate:
        raise InvalidFacebookProfile("empty Facebook profile value")
    if len(candidate) > 4_096:
        raise InvalidFacebookProfile("Facebook profile value is unreasonably long")

    if candidate.startswith("@"):
        candidate = candidate[1:]

    if candidate.isdigit():
        return NormalizedProfile(original, f"https://www.facebook.com/{candidate}")

    if _HANDLE_RE.fullmatch(candidate):
        return NormalizedProfile(original, f"https://www.facebook.com/{candidate}")

    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    elif not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", candidate):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().rstrip(".")
    if host not in _ALLOWED_HOSTS:
        raise InvalidFacebookProfile(f"unsupported Facebook host: {host or '<missing>'}")

    decoded_path = unquote(parsed.path or "").strip("/")
    path_parts = [part for part in decoded_path.split("/") if part]
    if not path_parts:
        raise InvalidFacebookProfile("Facebook URL has no account identifier")

    first = path_parts[0]
    first_lower = first.lower()
    if first_lower in _NON_ACCOUNT_PREFIXES:
        raise InvalidFacebookProfile(f"Facebook URL is not an account page: {first_lower}")

    if first_lower == "profile.php":
        profile_id = (parse_qs(parsed.query).get("id") or [""])[0]
        if not profile_id.isdigit():
            raise InvalidFacebookProfile("profile.php URL has no numeric id")
        normalized = f"https://www.facebook.com/profile.php?id={profile_id}"
        return NormalizedProfile(original, normalized)

    if first_lower == "pages":
        if len(path_parts) < 3 or not path_parts[-1].isdigit():
            raise InvalidFacebookProfile("legacy pages URL has no numeric page id")
        path = "/".join(path_parts[:3])
        normalized = f"https://www.facebook.com/{path}"
        if len(normalized) > 500:
            raise InvalidFacebookProfile("normalized Facebook page URL is too long")
        return NormalizedProfile(original, normalized)

    if first_lower == "pg":
        if len(path_parts) < 2:
            raise InvalidFacebookProfile("pg URL has no account handle")
        first = path_parts[1]

    if first.lower() in _NON_ACCOUNT_PREFIXES or not _HANDLE_RE.fullmatch(first):
        raise InvalidFacebookProfile("Facebook account handle contains unsupported characters")

    return NormalizedProfile(original, f"https://www.facebook.com/{first}")
