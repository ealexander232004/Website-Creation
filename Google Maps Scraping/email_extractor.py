"""High-Performance Small Business Email Footprint Extractor.

Discovers, extracts, validates, and scores business emails for no-website Google Maps leads
by analyzing public search engine footprints, local directories, state registries,
and social profile footprints using proxy rotation.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from curl_cffi import requests
from bs4 import BeautifulSoup

# Ensure parent path resolution for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DEFAULT_CONFIG, ScraperConfig
from database import Database
from proxy_manager import ProxyManager, ProxyRoute

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gmaps_scraper.email_extractor")


# Image and static asset extensions erroneously captured by naive regexes
INVALID_EXTENSIONS: Set[str] = {
    "png", "jpg", "jpeg", "webp", "svg", "gif", "css", "js", "ico", "woff",
    "woff2", "ttf", "eot", "mp4", "mp3", "pdf", "zip", "tar", "gz"
}

BLACKLIST_DOMAINS: Set[str] = {
    "example.com", "domain.com", "sentry.io", "w3.org", "schema.org", "cloudflare.com",
    "wixpress.com", "sentry-next.wixpress.com", "akamai.com", "google.com", "bing.com", "yahoo.com",
    "microsoft.com", "duckduckgo.com", "apple.com", "yandex.com", "yelp.com", "facebook.com",
    "bbb.org", "yellowpages.com", "chamberofcommerce.com", "whitepages.com", "manta.com", "godaddy.com",
    "namecheap.com", "wordpress.com", "squarespace.com", "hubspot.com", "mailchimp.com", "birdeye.com",
    "email.com"
}

SYSTEM_PREFIXES: Set[str] = {
    "noreply", "no-reply", "do-not-reply", "donotreply", "abuse", "webmaster",
    "postmaster", "hostmaster", "mailer-daemon", "root", "daemon", "your",
    "name", "user", "test"
}

GENERIC_BUSINESS_TOKENS: Set[str] = {
    "and", "company", "corp", "corporation", "inc", "incorporated", "llc",
    "ltd", "service", "services", "solutions", "the", "your"
}

GENERIC_INDUSTRY_TOKENS: Set[str] = {
    "ac", "air", "auto", "automotive", "bakery", "bar", "beauty", "cafe", "car",
    "carpentry", "catering", "center", "cleaning", "construction", "contractor", "detail", "detailing",
    "drywall", "electric", "electrical", "electrician", "fabrication", "fitness", "food",
    "hair", "heating", "hvac", "landscaping", "lawn", "mechanic", "mobile", "motor",
    "nail", "nails", "painting", "plumber", "plumbing", "repair", "restaurant", "roof",
    "roofer", "roofing", "salon", "shop", "spa", "studio", "towing", "truck", "welding",
}

# These words can be valid brands, but are too common to establish ownership
# by themselves. They remain useful when a second distinctive token agrees.
AMBIGUOUS_SINGLE_BRAND_TOKENS: Set[str] = {
    "best", "care", "choice", "complete", "first", "freedom", "global", "great",
    "green", "grow", "home", "local", "main", "master", "new", "premier", "pro",
    "quality", "royal", "smart", "star", "superior", "total", "true", "united",
    "valet", "west", "world",
}

CORPORATE_SUFFIX_TOKENS: Set[str] = {
    "co", "company", "corp", "corporation", "inc", "incorporated", "llc", "ltd",
}

# Common public email providers utilized by small trade businesses
FREE_EMAIL_PROVIDERS: Set[str] = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com",
    "comcast.net", "sbcglobal.net", "att.net", "verizon.net", "msn.com", "bellsouth.net",
    "cox.net", "charter.net", "earthlink.net", "live.com", "me.com", "ymail.com",
    "centurylink.net", "fastmail.com", "frontier.com", "gmx.com", "gmx.us", "mail.com",
    "optonline.net", "pm.me", "proton.me", "protonmail.com", "roadrunner.com", "spectrum.net",
    "windstream.net",
}

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
MAX_EMAILS_PER_LEAD = 3
MAX_SEARCH_QUERIES_PER_LEAD = 3
MAX_BUSINESSES_PER_EMAIL = 3
MIN_LANDING_PAGE_CONFIDENCE = 0.75


@dataclass
class ExtractedEmail:
    """Represents a discovered business email with provenance and confidence score."""
    email: str
    source_url: str
    source_type: str
    confidence: float  # 0.0 - 1.0
    is_free_provider: bool
    lead_place_id: str
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def decode_bing_url(href: str) -> str:
    """Decodes base64 target URLs from Bing click-tracking redirects."""
    if not href:
        return ""
    if "bing.com/ck/a" in href:
        try:
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            u_param = qs.get("u", [""])[0]
            if u_param.startswith("a1"):
                raw_b64 = u_param[2:]
                padded = raw_b64 + "=" * ((4 - len(raw_b64) % 4) % 4)
                return base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return href


def _normalized_tokens(value: Optional[str]) -> List[str]:
    return re.findall(r"[a-z0-9]+", (value or "").lower())


def _distinctive_business_tokens(business_name: str, category: str = "") -> List[str]:
    category_tokens = set(_normalized_tokens(category))
    return [
        token
        for token in _normalized_tokens(business_name)
        if len(token) > 2
        and token not in GENERIC_BUSINESS_TOKENS
        and token not in GENERIC_INDUSTRY_TOKENS
        and token not in category_tokens
    ]


def _brand_acronyms(business_name: str) -> Set[str]:
    """Return standalone uppercase brand acronyms, excluding apostrophe surnames."""
    return {
        token.lower()
        for token in re.findall(r"(?<![A-Za-z'’])[A-Z]{2,5}(?![A-Za-z])", business_name)
        if token.lower() not in GENERIC_BUSINESS_TOKENS
        and token.lower() not in GENERIC_INDUSTRY_TOKENS
    }


def _email_contexts(html: str, radius: int = 350) -> List[Tuple[str, str]]:
    """Return each address with nearby visible text instead of one whole-page blob."""
    contexts: List[Tuple[str, str]] = []
    for match in EMAIL_REGEX.finditer(html or ""):
        fragment = html[max(0, match.start() - radius):match.end() + radius]
        visible = BeautifulSoup(fragment, "html.parser").get_text(" ", strip=True)
        contexts.append((match.group(0), visible))
    return contexts


def _source_hostname(source_url: str) -> str:
    """Return a normalized source hostname without credentials or a www prefix."""
    try:
        hostname = (urllib.parse.urlparse(source_url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    return hostname[4:] if hostname.startswith("www.") else hostname


def _core_business_tokens(business_name: str) -> List[str]:
    """Return name tokens useful for exact compact/phrase comparisons."""
    return [
        token
        for token in _normalized_tokens(business_name)
        if token not in CORPORATE_SUFFIX_TOKENS
        and token not in {"and", "for", "of", "the"}
    ]


def _identity_matches_brand(identity: str, business_name: str, category: str = "") -> bool:
    """Require a distinctive business token rather than a generic trade/category word."""
    normalized_identity = re.sub(r"[^a-z0-9]", "", identity.lower())
    core_tokens = _core_business_tokens(business_name)
    compact_full_name = "".join(core_tokens)
    if (
        len(core_tokens) >= 2
        and len(compact_full_name) >= 6
        and compact_full_name in normalized_identity
    ):
        return True

    distinctive = _distinctive_business_tokens(business_name, category)
    matched = {token for token in distinctive if token in normalized_identity}
    if len(matched) >= 2:
        return True

    compact_brand = "".join(distinctive)
    if len(distinctive) >= 2 and len(compact_brand) >= 6 and compact_brand in normalized_identity:
        return True

    if len(distinctive) == 1:
        token = distinctive[0]
        if (
            ((len(token) >= 2 and any(char.isdigit() for char in token))
             or (len(token) >= 4 and token not in AMBIGUOUS_SINGLE_BRAND_TOKENS))
            and token in normalized_identity
        ):
            return True

    return any(
        acronym in normalized_identity
        for acronym in _brand_acronyms(business_name)
        if len(acronym) >= 2
    )


def _business_name_confirmed(context: str, business_name: str, category: str = "") -> bool:
    """Require the result card to identify the business, not merely repeat its phone."""
    context_tokens = _normalized_tokens(context)
    normalized_context = " ".join(context_tokens)
    core_tokens = _core_business_tokens(business_name)
    core_name = " ".join(core_tokens)
    if core_name and core_name in normalized_context:
        return True

    distinctive = set(_distinctive_business_tokens(business_name, category))
    if len(distinctive) < 2:
        return False
    required_matches = max(2, (3 * len(distinctive) + 3) // 4)
    return sum(token in context_tokens for token in distinctive) >= required_matches


def _category_confirmed(context: str, category: str) -> bool:
    """Use loose category stems only as corroboration for one-word business names."""
    context_tokens = _normalized_tokens(context)
    category_tokens = [token for token in _normalized_tokens(category) if len(token) >= 5]
    return any(
        context_token.startswith(category_token[:5])
        or category_token.startswith(context_token[:5])
        for category_token in category_tokens
        for context_token in context_tokens
        if len(context_token) >= 5
    )


def build_search_queries(
    business_name: str,
    *,
    phone: str = "",
    city: str = "",
) -> List[str]:
    """Build precision-first queries while always retaining a name/city fallback."""
    clean_phone = re.sub(r"[^\d]", "", phone)
    formatted_phone = (
        f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
        if len(clean_phone) == 10
        else phone
    )

    queries: List[str] = []
    if phone:
        queries.append(f'"{business_name}" ("{formatted_phone}" OR "{clean_phone}")')
    if city:
        queries.append(f'"{business_name}" "{city}" (email OR contact)')
    else:
        queries.append(f'"{business_name}" (email OR contact)')
    if phone:
        queries.append(
            f'"{formatted_phone}" ("@gmail.com" OR "@yahoo.com" OR "@outlook.com" OR email)'
        )

    return list(dict.fromkeys(queries))[:MAX_SEARCH_QUERIES_PER_LEAD]


def email_matches_business(
    email: str,
    business_name: str,
    *,
    category: str = "",
    phone: str = "",
    city: str = "",
    local_context: str = "",
    result_context: str = "",
    source_url: str = "",
    allow_phone_confirmation: bool = True,
    require_local_corroboration: bool = False,
) -> bool:
    """Require address-level evidence tying an email to this specific business."""
    local_part, domain = email.lower().split("@", 1)
    local_identity = re.sub(r"[^a-z0-9]", "", local_part)
    domain_identity = re.sub(r"[^a-z0-9]", "", domain.split(".", 1)[0])
    domain_brand_match = _identity_matches_brand(domain_identity, business_name, category)
    source_host = _source_hostname(source_url)
    source_owns_email_domain = bool(
        source_host
        and (source_host == domain or source_host.endswith(f".{domain}"))
    )
    # A directory or marketplace's own mailbox is not the listed business's
    # mailbox, even when its footer happens to sit near the business phone.
    if source_owns_email_domain and not domain_brand_match:
        return False

    clean_phone = re.sub(r"\D", "", phone)
    evidence_phone = re.sub(r"\D", "", local_context)
    phone_near_email = len(clean_phone) >= 7 and clean_phone[-10:] in evidence_phone
    normalized_city = " ".join(_normalized_tokens(city))
    normalized_evidence = " ".join(
        _normalized_tokens(f"{local_context} {result_context}")
    )
    location_near_email = bool(
        normalized_city and normalized_city in normalized_evidence
    )
    if (
        require_local_corroboration
        and not source_owns_email_domain
        and not (phone_near_email or location_near_email)
    ):
        return False

    result_name_confirmed = _business_name_confirmed(
        result_context,
        business_name,
        category,
    )
    phone_confirmed = (
        allow_phone_confirmation
        and phone_near_email
        and result_name_confirmed
    )
    if phone_confirmed:
        return True

    local_brand_match = _identity_matches_brand(local_identity, business_name, category)
    if not local_brand_match and not domain_brand_match:
        return False

    name_confirmed = _business_name_confirmed(
        f"{local_context} {result_context}",
        business_name,
        category,
    )
    if domain in FREE_EMAIL_PROVIDERS:
        return local_brand_match and name_confirmed
    if domain_brand_match:
        core_tokens = _core_business_tokens(business_name)
        if len(core_tokens) <= 1:
            combined_context = " ".join(
                _normalized_tokens(f"{local_context} {result_context}")
            )
            corroborated = bool(
                (normalized_city and normalized_city in combined_context)
                or _category_confirmed(combined_context, category)
            )
            return name_confirmed and corroborated
        return name_confirmed
    # A branded local part at another organization's custom domain identifies
    # a person, not ownership by this business (for example, a CPA name at an
    # insurance-company domain). Custom domains must match the business brand.
    return False


def is_search_result_relevant(
    result_text: str,
    business_name: str,
    phone: str = "",
    city: str = "",
    category: str = "",
) -> bool:
    """Require result-level evidence before accepting its emails or links."""
    result_tokens = _normalized_tokens(result_text)
    normalized_result = " ".join(result_tokens)
    normalized_name = " ".join(_normalized_tokens(business_name))
    clean_phone = re.sub(r"\D", "", phone)
    result_phone = re.sub(r"\D", "", result_text)
    phone_matches = len(clean_phone) >= 7 and clean_phone[-10:] in result_phone
    name_tokens = _distinctive_business_tokens(business_name, category)
    brand_acronyms = _brand_acronyms(business_name)

    if normalized_name and normalized_name in normalized_result:
        return bool(name_tokens or brand_acronyms or phone_matches)

    if phone_matches:
        return True

    if not name_tokens:
        return False

    matched = sum(token in result_tokens for token in set(name_tokens))
    if matched >= 2:
        return True

    normalized_city = " ".join(_normalized_tokens(city))
    return bool(normalized_city and normalized_city in normalized_result and matched >= 2)


def clean_extracted_email(email_str: str) -> Optional[str]:
    """Validate practical email syntax without maintaining a brittle TLD allowlist."""
    if not email_str or email_str.count("@") != 1:
        return None
    
    email_str = email_str.lower().strip(" .\t\r\n'\"<>(),;:#*[]{}|")
    
    local, domain = email_str.split("@", 1)
    
    if (
        len(email_str) > 254
        or len(local) < 1
        or len(local) > 64
        or len(domain) < 3
        or "." not in domain
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
    ):
        return None

    if not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+", local):
        return None

    labels = domain.rstrip(".").split(".")
    if any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        return None

    tld = domain.split(".")[-1]
    if len(tld) < 2 or tld.isdigit() or tld in INVALID_EXTENSIONS:
        return None
        
    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLACKLIST_DOMAINS):
        return None
        
    mailbox_role = local.split("+", 1)[0]
    if mailbox_role in SYSTEM_PREFIXES:
        return None
        
    return f"{local}@{domain}"


def calculate_email_confidence(email: str, business_name: str, city: Optional[str] = None) -> float:
    """Computes a heuristic confidence score (0.50 - 0.98) based on context relevance."""
    score = 0.65
    local_part, domain = email.split("@", 1)
    
    # Check if domain or local part matches business name components
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', business_name.lower())
    name_tokens = [t for t in clean_name.split() if len(t) > 2 and t not in ["the", "and", "llc", "inc", "co", "pro", "services", "company"]]
    
    matched_tokens = sum(1 for t in name_tokens if t in local_part or t in domain)
    if matched_tokens >= 2:
        score += 0.25
    elif matched_tokens == 1:
        score += 0.15
        
    # Check city match
    if city and city.lower() in local_part:
        score += 0.10
        
    # High confidence for popular business free email providers
    if domain in FREE_EMAIL_PROVIDERS:
        score += 0.05
        
    return min(score, 0.98)


class EmailFootprintExtractor:
    """Asynchronous batch email discovery engine for small businesses."""

    def __init__(
        self,
        database: Database,
        config: Optional[ScraperConfig] = None,
        proxy_manager: Optional[ProxyManager] = None,
        concurrency: int = 10,
    ) -> None:
        self.db = database
        self.config = config or DEFAULT_CONFIG
        self.proxy_manager = proxy_manager or ProxyManager(proxy_urls_file=self.config.proxy_urls_file)
        if self.proxy_manager.total_proxies < 1:
            raise RuntimeError(
                "Email extraction requires at least one configured proxy; direct-network fallback is disabled"
            )
        self.concurrency = concurrency
        self._headers = {
            "User-Agent": self.config.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._ensure_email_schema()

    def _ensure_email_schema(self) -> None:
        """Verifies that the PostgreSQL schema initialized by Database is available."""
        self.db.ping()

    def _get_proxy_dict(self) -> Dict[str, str]:
        """Return one required proxy mapping; never permit direct-network fallback."""
        route = self.proxy_manager.get_next_proxy()
        if route is None or not route.raw_url or not route.host:
            raise RuntimeError(
                "No valid email proxy route is available; direct-network fallback is disabled"
            )
        return {"http": route.raw_url, "https": route.raw_url}

    def search_lead_footprint(self, lead: Dict[str, Any]) -> List[ExtractedEmail]:
        """Synchronous worker that searches and extracts email footprints for a single lead."""
        name = lead["name"]
        category = lead.get("category") or ""
        phone = lead.get("phone") or ""
        city = lead.get("city") or ""
        place_id = lead["place_id"]
        
        discovered: List[ExtractedEmail] = []
        seen_emails: Set[str] = set()

        proxies = self._get_proxy_dict()
        successful_search_responses = 0
        last_search_error: Optional[Exception] = None

        queries = build_search_queries(name, phone=phone, city=city)
        for q in queries:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
            try:
                resp = requests.get(
                    url,
                    headers=self._headers,
                    proxies=proxies,
                    timeout=8,
                    impersonate="chrome120"
                )
                if resp.status_code != 200:
                    last_search_error = RuntimeError(
                        f"Bing returned HTTP {resp.status_code} through the configured proxy"
                    )
                    continue
                successful_search_responses += 1
                    
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Evaluate each result independently. Concatenating the entire SERP
                # imports addresses from unrelated results and directory chrome.
                candidate_links: List[Tuple[str, str]] = []
                for item in soup.select("li.b_algo"):
                    item_text = item.get_text(" ", strip=True)
                    if not is_search_result_relevant(
                        item_text,
                        business_name=name,
                        phone=phone,
                        city=city,
                        category=category,
                    ):
                        continue

                    a = item.select_one("h2 a")
                    real_url = ""
                    if a and a.get("href"):
                        real_url = decode_bing_url(a.get("href"))

                    for raw_em in EMAIL_REGEX.findall(item_text):
                        cleaned = clean_extracted_email(raw_em)
                        if (
                            cleaned
                            and cleaned not in seen_emails
                            and email_matches_business(
                                cleaned,
                                name,
                                category=category,
                                phone=phone,
                                city=city,
                                local_context=item_text,
                                result_context=item_text,
                                source_url=real_url,
                            )
                        ):
                            seen_emails.add(cleaned)
                            domain = cleaned.split("@")[-1]
                            conf = max(calculate_email_confidence(cleaned, name, city), 0.80)
                            discovered.append(ExtractedEmail(
                                email=cleaned,
                                source_url=real_url or url,
                                source_type="search_snippet",
                                confidence=conf,
                                is_free_provider=domain in FREE_EMAIL_PROVIDERS,
                                lead_place_id=place_id
                            ))

                    if real_url.startswith("http") and not any(
                        domain in real_url
                        for domain in ["bing.com", "microsoft.com", "google.com", "wikipedia.org"]
                    ):
                        candidate_links.append((real_url, item_text))

                # Visit only landing URLs from result cards already matched to the lead.
                for link, result_context in candidate_links[:3]:
                    try:
                        page_resp = requests.get(
                            link,
                            headers=self._headers,
                            proxies=proxies,
                            timeout=6,
                            impersonate="chrome120"
                        )
                        if page_resp.status_code == 200:
                            for raw_em, local_context in _email_contexts(page_resp.text):
                                cleaned = clean_extracted_email(raw_em)
                                if cleaned and cleaned not in seen_emails:
                                    domain = cleaned.split("@")[-1]
                                    conf = calculate_email_confidence(cleaned, name, city)
                                    # Directory pages commonly contain many businesses.
                                    # Require evidence for this individual address in its
                                    # nearby fragment; never trust the whole page at once.
                                    if not email_matches_business(
                                        cleaned,
                                        name,
                                        category=category,
                                        phone=phone,
                                        city=city,
                                        local_context=local_context,
                                        result_context=result_context,
                                        source_url=link,
                                        allow_phone_confirmation=False,
                                        require_local_corroboration=True,
                                    ):
                                        continue
                                    conf = max(conf, MIN_LANDING_PAGE_CONFIDENCE)
                                    seen_emails.add(cleaned)
                                    discovered.append(ExtractedEmail(
                                        email=cleaned,
                                        source_url=link,
                                        source_type="contextual_landing_page",
                                        confidence=conf,
                                        is_free_provider=domain in FREE_EMAIL_PROVIDERS,
                                        lead_place_id=place_id
                                    ))
                    except Exception:
                        pass

                if discovered:
                    break  # Break early once qualified emails are found

            except Exception as e:
                last_search_error = e
                logger.debug("Footprint search error for %s: %s", name, e)

        if successful_search_responses == 0:
            detail = f": {last_search_error}" if last_search_error else ""
            raise RuntimeError(
                f"All proxied email search requests failed for {name!r}{detail}"
            )

        # Prefer the strongest, search-specific evidence and prevent a directory
        # page from attaching an unbounded staff list to one business lead.
        discovered.sort(
            key=lambda email: (
                email.confidence,
                email.source_type == "search_snippet",
            ),
            reverse=True,
        )
        return discovered[:MAX_EMAILS_PER_LEAD]

    def _reconcile_email_state(self, conn: Any, place_ids: List[str]) -> None:
        """Keep global status and durable queue rows aligned after quarantine deletes."""
        for place_id in sorted(set(place_ids)):
            saved_count = int(
                conn.execute(
                    "SELECT count(*) AS email_count FROM lead_emails WHERE place_id = %s",
                    (place_id,),
                ).fetchone()["email_count"]
            )
            status = "completed" if saved_count else "no_email"
            conn.execute(
                """
                INSERT INTO email_extraction_status (place_id, status, emails_found_count, processed_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (place_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    emails_found_count = EXCLUDED.emails_found_count,
                    processed_at = EXCLUDED.processed_at
                """,
                (place_id, status, saved_count),
            )
            conn.execute(
                """
                UPDATE email_queue
                SET status = %s, emails_found = %s, completed_at = CURRENT_TIMESTAMP
                WHERE place_id = %s AND status IN ('completed', 'no_email')
                """,
                (status, saved_count, place_id),
            )

    def save_extracted_emails(self, emails: List[ExtractedEmail]) -> int:
        """Persist one lead's emails, globally quarantining over-reused addresses."""
        if not emails:
            return 0
        place_ids = {email.lead_place_id for email in emails}
        if len(place_ids) != 1:
            raise ValueError("save_extracted_emails expects emails for exactly one lead")
        place_id = next(iter(place_ids))

        with self.db._get_connection() as conn:
            conn.execute("SET LOCAL lock_timeout = '5s'")
            for email in sorted(emails, key=lambda item: item.email):
                # A deterministic transaction-level advisory lock prevents two
                # workers from pushing the same address past the reuse limit.
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    (email.email,),
                )
                if conn.execute(
                    "SELECT 1 FROM quarantined_emails WHERE email = %s",
                    (email.email,),
                ).fetchone():
                    conn.execute(
                        """
                        UPDATE quarantined_emails
                        SET occurrences = occurrences + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE email = %s
                        """,
                        (email.email,),
                    )
                    continue

                if conn.execute(
                    "SELECT 1 FROM lead_emails WHERE place_id = %s AND email = %s",
                    (place_id, email.email),
                ).fetchone():
                    continue

                existing_place_ids = [
                    row["place_id"]
                    for row in conn.execute(
                        "SELECT DISTINCT place_id FROM lead_emails WHERE email = %s ORDER BY place_id",
                        (email.email,),
                    ).fetchall()
                ]
                if len(existing_place_ids) >= MAX_BUSINESSES_PER_EMAIL:
                    conn.execute(
                        """
                        INSERT INTO quarantined_emails (email, reason, occurrences)
                        VALUES (%s, 'cross_business_reuse', %s)
                        ON CONFLICT (email) DO UPDATE SET
                            occurrences = greatest(
                                quarantined_emails.occurrences,
                                EXCLUDED.occurrences
                            ),
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (email.email, len(existing_place_ids) + 1),
                    )
                    removed_place_ids = [
                        row["place_id"]
                        for row in conn.execute(
                            "DELETE FROM lead_emails WHERE email = %s RETURNING place_id",
                            (email.email,),
                        ).fetchall()
                    ]
                    self._reconcile_email_state(conn, removed_place_ids)
                    logger.warning(
                        "Quarantined an address on %d businesses (domain=%s).",
                        len(existing_place_ids) + 1,
                        email.email.split("@", 1)[1],
                    )
                    continue

                conn.execute(
                    """
                    INSERT INTO lead_emails (
                        place_id, email, source_url, source_type, confidence, is_free_provider
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (place_id, email) DO NOTHING
                    """,
                    (
                        email.lead_place_id,
                        email.email,
                        email.source_url,
                        email.source_type,
                        email.confidence,
                        email.is_free_provider,
                    ),
                )
            return int(
                conn.execute(
                    "SELECT count(*) AS email_count FROM lead_emails WHERE place_id = %s",
                    (place_id,),
                ).fetchone()["email_count"]
            )

    def mark_lead_status(self, place_id: str, status: str, count: int) -> None:
        """Records lead extraction completion status to enable resume capabilities."""
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT INTO email_extraction_status (place_id, status, emails_found_count, processed_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (place_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    emails_found_count = EXCLUDED.emails_found_count,
                    processed_at = EXCLUDED.processed_at
            """, (place_id, status, count))

    def get_pending_leads_count(self) -> int:
        """Returns the number of remaining unprocessed no-website leads."""
        with self.db._get_connection() as conn:
            return conn.execute("""
                SELECT count(*) AS pending_count FROM leads AS lead
                WHERE NOT lead.has_website
                  AND NOT EXISTS (
                      SELECT 1 FROM email_extraction_status AS status
                      WHERE status.place_id = lead.place_id
                  )
            """).fetchone()["pending_count"]

    def get_pending_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Queries the next batch of unprocessed no-website leads."""
        query = """
            SELECT place_id, name, category, phone, full_address, city, state 
            FROM leads AS lead
            WHERE NOT lead.has_website
              AND NOT EXISTS (
                  SELECT 1 FROM email_extraction_status AS status
                  WHERE status.place_id = lead.place_id
              )
            ORDER BY (phone IS NOT NULL) DESC
        """
        params: Tuple[Any, ...] = ()
        if limit:
            query += " LIMIT %s"
            params = (limit,)

        with self.db._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def process_lead_worker(self, lead: Dict[str, Any], idx: int, total: int) -> Dict[str, Any]:
        """Worker function for concurrent thread pool execution."""
        name = lead["name"]
        phone = lead.get("phone") or ""
        city = lead.get("city") or ""
        place_id = lead["place_id"]
        
        emails = self.search_lead_footprint(lead)
        saved_count = self.save_extracted_emails(emails) if emails else 0
        if saved_count:
            self.mark_lead_status(place_id, "completed", saved_count)
            status = f"FOUND ({saved_count})"
        else:
            self.mark_lead_status(place_id, "no_email", 0)
            status = "NO_EMAIL"
            
        saved_rows: List[Dict[str, Any]] = []
        if saved_count:
            with self.db._get_connection() as conn:
                saved_rows = [
                    dict(row)
                    for row in conn.execute(
                        """
                        SELECT email, confidence
                        FROM lead_emails
                        WHERE place_id = %s
                        ORDER BY confidence DESC, email
                        LIMIT %s
                        """,
                        (place_id, MAX_EMAILS_PER_LEAD),
                    ).fetchall()
                ]
        email_list = [row["email"] for row in saved_rows]
        if idx % 25 == 0 or email_list:
            print(f"[{idx}/{total}] [{status}] {name} ({city} | {phone}) -> {email_list[:2]}", flush=True)
            
        return {
            "place_id": place_id,
            "name": name,
            "category": lead.get("category"),
            "phone": phone,
            "city": city,
            "state": lead.get("state"),
            "has_email": saved_count > 0,
            "emails": email_list,
            "top_email": email_list[0] if email_list else None,
            "confidence": float(saved_rows[0]["confidence"]) if saved_rows else 0.0,
        }

    def run_full_campaign(self, max_workers: int = 10, batch_size: int = 500) -> None:
        """Executes full resume-capable email extraction across all pending no-website leads."""
        pending_count = self.get_pending_leads_count()
        logger.info("Starting Full Email Footprint Campaign: %d pending no-website leads to process...", pending_count)
        
        start_time = time.time()
        processed_total = 0
        matched_total = 0

        while True:
            batch = self.get_pending_leads(limit=batch_size)
            if not batch:
                break
                
            batch_size_actual = len(batch)
            logger.info("Processing batch of %d leads across %d worker threads...", batch_size_actual, max_workers)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.process_lead_worker, lead, processed_total + idx, pending_count): lead
                    for idx, lead in enumerate(batch, 1)
                }
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        processed_total += 1
                        if res["has_email"]:
                            matched_total += 1
                    except Exception as e:
                        logger.warning("Lead task error: %s", e)

            elapsed = time.time() - start_time
            rate = round(processed_total / (elapsed / 60.0), 1) if elapsed > 0 else 0.0
            hit_pct = round((matched_total / processed_total) * 100, 1) if processed_total > 0 else 0.0
            logger.info(
                "Batch Progress: %d / %d processed (%.1f%%) | Matched: %d emails (%.1f%% hit rate) | Speed: %.1f leads/min",
                processed_total, pending_count, (processed_total / pending_count) * 100, matched_total, hit_pct, rate
            )

        logger.info("Email Footprint Extraction Campaign Finished! Exporting final datasets...")
        self.export_final_datasets()

    def export_final_datasets(self) -> None:
        """Generates unified, enriched CSV, Excel, and JSONL datasets of all no-website leads with emails."""
        with self.db._get_connection() as conn:
            # Query all no-website leads with their top discovered email and metadata
            query = """
                SELECT 
                    l.name,
                    l.category,
                    l.phone,
                    l.full_address,
                    l.city,
                    l.state,
                    l.zip_code,
                    l.rating,
                    l.reviews_count,
                    l.maps_url,
                    e.email AS primary_email,
                    e.confidence AS email_confidence,
                    e.source_type AS email_source,
                    CASE WHEN e.email IS NOT NULL THEN 1 ELSE 0 END AS has_discovered_email
                FROM leads l
                LEFT JOIN LATERAL (
                    SELECT email, confidence, source_type
                    FROM lead_emails
                    WHERE place_id = l.place_id
                    ORDER BY confidence DESC, discovered_at ASC
                    LIMIT 1
                ) e ON TRUE
                WHERE NOT l.has_website
                ORDER BY (e.email IS NOT NULL) DESC, e.confidence DESC, l.reviews_count DESC
            """
            df_all_no_web = pd.DataFrame(conn.execute(query).fetchall())
            
            # Query leads that have emails discovered
            df_with_emails = df_all_no_web[df_all_no_web["has_discovered_email"] == 1]

        export_dir = self.config.export_dir
        export_dir.mkdir(parents=True, exist_ok=True)

        # 1. CSV of leads with emails
        csv_path = export_dir / "leads_no_website_with_emails_final.csv"
        df_with_emails.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info("Exported %d leads with emails to CSV: %s", len(df_with_emails), csv_path)

        # 2. Multi-tab Excel Workbook
        excel_path = export_dir / "leads_no_website_with_emails_final.xlsx"
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_with_emails.to_excel(writer, sheet_name="Leads With Emails", index=False)
            df_all_no_web.to_excel(writer, sheet_name="All No-Website Leads", index=False)
        logger.info("Exported Multi-Tab Excel Workbook to: %s", excel_path)

        # 3. JSONL
        jsonl_path = export_dir / "leads_no_website_with_emails_final.jsonl"
        df_with_emails.to_json(jsonl_path, orient="records", lines=True)
        logger.info("Exported JSONL to: %s", jsonl_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Small Business Email Footprint Extractor")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent proxy worker threads (default 10)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for lead queries (default 500)")
    parser.add_argument("--export-only", action="store_true", help="Export existing extracted emails without scraping")
    args = parser.parse_args()

    db = Database(DEFAULT_CONFIG.database_url)
    pm = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    extractor = EmailFootprintExtractor(database=db, config=DEFAULT_CONFIG, proxy_manager=pm, concurrency=args.workers)

    if args.export_only:
        extractor.export_final_datasets()
        return

    extractor.run_full_campaign(max_workers=args.workers, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
