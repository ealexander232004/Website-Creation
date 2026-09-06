"""High-Performance Small Business Email Footprint Extractor.

Discovers, extracts, verifies, and scores business emails for no-website Google Maps leads
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


# Top-Level Domains valid for business & personal email routing
VALID_TLDS: Set[str] = {
    "com", "org", "net", "edu", "gov", "mil", "biz", "info", "mobi", "name",
    "aero", "asia", "jobs", "museum", "co", "us", "io", "me", "pro", "tv",
    "cc", "ws", "tech", "site", "online", "store", "club", "xyz", "agency", "live"
}

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
    "support", "noreply", "no-reply", "privacy", "abuse", "legal", "webmaster",
    "postmaster", "hostmaster", "security", "mailer-daemon", "root", "daemon", "your",
    "name", "user", "test", "admin"
}

GENERIC_BUSINESS_TOKENS: Set[str] = {
    "and", "company", "corp", "corporation", "inc", "incorporated", "llc",
    "ltd", "service", "services", "solutions", "the"
}

GENERIC_INDUSTRY_TOKENS: Set[str] = {
    "ac", "air", "construction", "contractor", "electric", "electrical", "electrician",
    "heating", "hvac", "motor", "plumber", "plumbing", "roof", "roofer", "roofing",
}

# Common public email providers utilized by small trade businesses
FREE_EMAIL_PROVIDERS: Set[str] = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com",
    "comcast.net", "sbcglobal.net", "att.net", "verizon.net", "msn.com", "bellsouth.net",
    "cox.net", "charter.net", "earthlink.net", "live.com", "me.com", "ymail.com"
}

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
MAX_EMAILS_PER_LEAD = 3
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


def _email_contexts(html: str, radius: int = 700) -> List[Tuple[str, str]]:
    """Return each address with nearby visible text instead of one whole-page blob."""
    contexts: List[Tuple[str, str]] = []
    for match in EMAIL_REGEX.finditer(html or ""):
        fragment = html[max(0, match.start() - radius):match.end() + radius]
        visible = BeautifulSoup(fragment, "html.parser").get_text(" ", strip=True)
        contexts.append((match.group(0), visible))
    return contexts


def email_matches_business(
    email: str,
    business_name: str,
    *,
    category: str = "",
    phone: str = "",
    local_context: str = "",
    result_context: str = "",
    source_url: str = "",
) -> bool:
    """Require address-level evidence tying an email to this specific business."""
    local_part, domain = email.lower().split("@", 1)
    identity = re.sub(r"[^a-z0-9]", "", f"{local_part}{domain.split('.')[0]}")
    local_identity = re.sub(r"[^a-z0-9]", "", local_part)
    name_tokens = [
        token
        for token in _normalized_tokens(business_name)
        if token not in GENERIC_BUSINESS_TOKENS
    ]
    distinctive = _distinctive_business_tokens(business_name, category)
    meaningful_matches = {token for token in name_tokens if len(token) > 2 and token in identity}
    distinctive_matches = {token for token in distinctive if token in identity}
    brand_acronyms = _brand_acronyms(business_name)
    clean_phone = re.sub(r"\D", "", phone)
    evidence_phone = re.sub(r"\D", "", f"{local_context} {result_context}")
    phone_confirmed = len(clean_phone) >= 7 and clean_phone[-10:] in evidence_phone

    # Initial-only generic names such as B & S Electric are too ambiguous without
    # a matching phone in the actual result or nearby page fragment.
    if not distinctive and not brand_acronyms and not phone_confirmed:
        return False

    # Multiple brand tokens are strong evidence (for example central-valley.com).
    if len(distinctive_matches) >= 2:
        return True

    # One long brand token in the mailbox is useful for names such as
    # psmith@... while avoiding short collisions such as Star vs All Star.
    if any(len(token) >= 5 and token in local_identity for token in distinctive):
        return True

    # A long brand token plus another meaningful name/trade token in the domain
    # accepts domains such as eliteroofinc.com without trusting generic trade words alone.
    if any(len(token) >= 5 and token in identity for token in distinctive) and len(meaningful_matches) >= 2:
        return True

    # Uppercase business acronyms such as SOS or BR are intentional brand signals.
    if any(len(token) >= 2 and token in identity for token in brand_acronyms):
        return True

    compact_name = "".join(name_tokens)
    if len(compact_name) >= 5 and compact_name in identity:
        return True

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
    """Strictly validates and normalizes an email address string."""
    if not email_str or "@" not in email_str:
        return None
    
    email_str = email_str.lower().strip(" .\t\r\n'\"<>(),;:#*[]{}|")
    
    parts = email_str.split("@", 1)
    if len(parts) != 2:
        return None
    local, domain = parts[0], parts[1]
    
    if len(local) < 2 or len(domain) < 3 or "." not in domain:
        return None
        
    tld = domain.split(".")[-1]
    if tld in INVALID_EXTENSIONS or tld not in VALID_TLDS:
        return None
        
    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLACKLIST_DOMAINS):
        return None
        
    if any(local.startswith(p) or local == p for p in SYSTEM_PREFIXES):
        return None
        
    # Exclude invalid characters from URL encodings or corrupt strings
    if any(c in email_str for c in ["%", " ", "\\", "+", "/", "=", "&", "?", "$", "^"]):
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
        
        clean_phone = re.sub(r'[^\d]', '', phone) if phone else ""
        formatted_phone = f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}" if len(clean_phone) == 10 else phone

        discovered: List[ExtractedEmail] = []
        seen_emails: Set[str] = set()

        proxies = self._get_proxy_dict()
        successful_search_responses = 0
        last_search_error: Optional[Exception] = None

        # Query Strategies:
        queries = []
        if phone:
            queries.append(f'"{name}" "{formatted_phone}" OR "{clean_phone}"')
            queries.append(f'"{formatted_phone}" ("@gmail.com" OR "@yahoo.com" OR "@outlook.com" OR "email")')
        if city:
            queries.append(f'"{name}" "{city}" email OR contact')
        else:
            queries.append(f'"{name}" email OR contact')

        for q in queries[:2]:
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
                                source_url=url,
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
                                        local_context=local_context,
                                        result_context=result_context,
                                        source_url=link,
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

    def save_extracted_emails(self, emails: List[ExtractedEmail]) -> int:
        """Persists extracted emails to PostgreSQL."""
        if not emails:
            return 0
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO lead_emails (
                        place_id, email, source_url, source_type, confidence, is_free_provider
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (place_id, email) DO NOTHING
                    """,
                    [(
                        em.lead_place_id,
                        em.email,
                        em.source_url,
                        em.source_type,
                        em.confidence,
                        em.is_free_provider,
                    ) for em in emails],
                )
                return max(cursor.rowcount, 0)

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
        if emails:
            self.save_extracted_emails(emails)
            self.mark_lead_status(place_id, "completed", len(emails))
            status = f"FOUND ({len(emails)})"
        else:
            self.mark_lead_status(place_id, "no_email", 0)
            status = "NO_EMAIL"
            
        email_list = [e.email for e in emails]
        if idx % 25 == 0 or emails:
            print(f"[{idx}/{total}] [{status}] {name} ({city} | {phone}) -> {email_list[:2]}", flush=True)
            
        return {
            "place_id": place_id,
            "name": name,
            "category": lead.get("category"),
            "phone": phone,
            "city": city,
            "state": lead.get("state"),
            "has_email": len(emails) > 0,
            "emails": email_list,
            "top_email": email_list[0] if email_list else None,
            "confidence": emails[0].confidence if emails else 0.0,
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
