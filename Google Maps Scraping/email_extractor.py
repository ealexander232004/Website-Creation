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

# Common public email providers utilized by small trade businesses
FREE_EMAIL_PROVIDERS: Set[str] = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com",
    "comcast.net", "sbcglobal.net", "att.net", "verizon.net", "msn.com", "bellsouth.net",
    "cox.net", "charter.net", "earthlink.net", "live.com", "me.com", "ymail.com"
}

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')


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
        
    if domain in BLACKLIST_DOMAINS:
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
        self.concurrency = concurrency
        self._headers = {
            "User-Agent": self.config.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._ensure_email_schema()

    def _ensure_email_schema(self) -> None:
        """Ensures the lead_emails and email_extraction_status database tables exist."""
        with self.db._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lead_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    source_url TEXT,
                    source_type TEXT,
                    confidence REAL DEFAULT 0.70,
                    is_free_provider INTEGER DEFAULT 1,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (place_id) REFERENCES leads(place_id),
                    UNIQUE(place_id, email)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_extraction_status (
                    place_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL, -- 'completed', 'no_email', 'error'
                    emails_found_count INTEGER DEFAULT 0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (place_id) REFERENCES leads(place_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lead_emails_place_id ON lead_emails(place_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lead_emails_email ON lead_emails(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email_status ON email_extraction_status(status)")

    def _get_proxy_dict(self) -> Optional[Dict[str, str]]:
        if self.proxy_manager and self.proxy_manager.total_proxies > 0:
            route = self.proxy_manager.get_next_proxy()
            if route:
                return {"http": route.raw_url, "https": route.raw_url}
        return None

    def search_lead_footprint(self, lead: Dict[str, Any]) -> List[ExtractedEmail]:
        """Synchronous worker that searches and extracts email footprints for a single lead."""
        name = lead["name"]
        phone = lead.get("phone") or ""
        city = lead.get("city") or ""
        place_id = lead["place_id"]
        
        clean_phone = re.sub(r'[^\d]', '', phone) if phone else ""
        formatted_phone = f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}" if len(clean_phone) == 10 else phone

        discovered: List[ExtractedEmail] = []
        seen_emails: Set[str] = set()

        proxies = self._get_proxy_dict()

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
                    continue
                    
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 1. Check raw SERP snippets
                serp_text = " ".join([b.get_text() for b in soup.select("li.b_algo, .b_caption, p")])
                for raw_em in EMAIL_REGEX.findall(serp_text):
                    cleaned = clean_extracted_email(raw_em)
                    if cleaned and cleaned not in seen_emails:
                        seen_emails.add(cleaned)
                        domain = cleaned.split("@")[-1]
                        conf = calculate_email_confidence(cleaned, name, city)
                        discovered.append(ExtractedEmail(
                            email=cleaned,
                            source_url=url,
                            source_type="search_snippet",
                            confidence=conf,
                            is_free_provider=domain in FREE_EMAIL_PROVIDERS,
                            lead_place_id=place_id
                        ))

                # 2. Extract and visit top landing URLs
                candidate_links = []
                for item in soup.select("li.b_algo"):
                    a = item.select_one("h2 a")
                    if a and a.get("href"):
                        real_url = decode_bing_url(a.get("href"))
                        if real_url.startswith("http") and not any(d in real_url for d in ["bing.com", "microsoft.com", "google.com", "wikipedia.org"]):
                            candidate_links.append(real_url)

                for link in candidate_links[:3]:
                    try:
                        page_resp = requests.get(
                            link,
                            headers=self._headers,
                            proxies=proxies,
                            timeout=6,
                            impersonate="chrome120"
                        )
                        if page_resp.status_code == 200:
                            for raw_em in EMAIL_REGEX.findall(page_resp.text):
                                cleaned = clean_extracted_email(raw_em)
                                if cleaned and cleaned not in seen_emails:
                                    seen_emails.add(cleaned)
                                    domain = cleaned.split("@")[-1]
                                    conf = calculate_email_confidence(cleaned, name, city)
                                    discovered.append(ExtractedEmail(
                                        email=cleaned,
                                        source_url=link,
                                        source_type="directory_landing_page",
                                        confidence=conf,
                                        is_free_provider=domain in FREE_EMAIL_PROVIDERS,
                                        lead_place_id=place_id
                                    ))
                    except Exception:
                        pass

                if discovered:
                    break  # Break early once qualified emails are found

            except Exception as e:
                logger.debug("Footprint search error for %s: %s", name, e)

        return discovered

    def save_extracted_emails(self, emails: List[ExtractedEmail]) -> int:
        """Persists extracted emails to SQLite."""
        if not emails:
            return 0
        saved = 0
        with self.db._get_connection() as conn:
            for em in emails:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO lead_emails (
                            place_id, email, source_url, source_type, confidence, is_free_provider
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        em.lead_place_id,
                        em.email,
                        em.source_url,
                        em.source_type,
                        em.confidence,
                        1 if em.is_free_provider else 0
                    ))
                    saved += 1
                except Exception as e:
                    logger.debug("Failed saving email: %s", e)
        return saved

    def mark_lead_status(self, place_id: str, status: str, count: int) -> None:
        """Records lead extraction completion status to enable resume capabilities."""
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO email_extraction_status (place_id, status, emails_found_count, processed_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (place_id, status, count))

    def get_pending_leads_count(self) -> int:
        """Returns the number of remaining unprocessed no-website leads."""
        with self.db._get_connection() as conn:
            return conn.execute("""
                SELECT count(*) FROM leads 
                WHERE has_website = 0 
                  AND place_id NOT IN (SELECT place_id FROM email_extraction_status)
            """).fetchone()[0]

    def get_pending_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Queries the next batch of unprocessed no-website leads."""
        query = """
            SELECT place_id, name, category, phone, full_address, city, state 
            FROM leads 
            WHERE has_website = 0 
              AND place_id NOT IN (SELECT place_id FROM email_extraction_status)
            ORDER BY (phone IS NOT NULL) DESC
        """
        params: Tuple[Any, ...] = ()
        if limit:
            query += " LIMIT ?"
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
                LEFT JOIN lead_emails e ON l.place_id = e.place_id
                WHERE l.has_website = 0
                GROUP BY l.place_id
                ORDER BY (e.email IS NOT NULL) DESC, e.confidence DESC, l.reviews_count DESC
            """
            df_all_no_web = pd.read_sql_query(query, conn)
            
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

    db = Database(DEFAULT_CONFIG.database_path)
    pm = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    extractor = EmailFootprintExtractor(database=db, config=DEFAULT_CONFIG, proxy_manager=pm, concurrency=args.workers)

    if args.export_only:
        extractor.export_final_datasets()
        return

    extractor.run_full_campaign(max_workers=args.workers, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
