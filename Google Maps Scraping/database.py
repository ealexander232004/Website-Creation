"""SQLite storage engine with WAL mode and deduplication for scraped leads."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models import ClaimedStatus, Lead, SearchJob, SearchJobStatus, WebsiteType

logger = logging.getLogger("gmaps_scraper.database")


class Database:
    """Thread-safe SQLite database manager for Google Maps leads and queue management."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode with manual transactions
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            # Leads storage table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    place_id TEXT PRIMARY KEY,
                    cid TEXT,
                    name TEXT NOT NULL,
                    category TEXT,
                    all_categories TEXT,
                    phone TEXT,
                    full_address TEXT,
                    street TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    country TEXT DEFAULT 'United States',
                    latitude REAL,
                    longitude REAL,
                    plus_code TEXT,
                    website_raw TEXT,
                    website_type TEXT,
                    website_explanation TEXT,
                    has_website INTEGER NOT NULL,
                    rating REAL,
                    reviews_count INTEGER DEFAULT 0,
                    is_claimed TEXT,
                    price_level TEXT,
                    business_status TEXT,
                    maps_url TEXT,
                    search_keyword TEXT,
                    search_location TEXT,
                    scraped_at TEXT NOT NULL
                );
                """
            )

            # Performance indexes on common query filters
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_has_website ON leads (has_website);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_website_type ON leads (website_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_state ON leads (state);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_city ON leads (city);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_category ON leads (category);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads (phone);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_is_claimed ON leads (is_claimed);")

            # Search task queue table for resumable nationwide campaigns
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS search_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    location_name TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    zoom_level INTEGER DEFAULT 14,
                    bounding_box TEXT,
                    status TEXT DEFAULT 'pending',
                    results_found INTEGER DEFAULT 0,
                    leads_saved INTEGER DEFAULT 0,
                    error_message TEXT,
                    attempts INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON search_queue (status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_keyword ON search_queue (keyword);")

    def save_lead(self, lead: Lead) -> bool:
        """Upserts a single lead record. Returns True if inserted or updated."""
        with self._lock, self._get_connection() as conn:
            # Fallback identifier if place_id is empty: hash of name + phone or name + address
            unique_id = lead.place_id
            if not unique_id:
                unique_id = f"custom_{hash((lead.name, lead.phone or '', lead.full_address or ''))}"

            categories_json = json.dumps(lead.all_categories)

            query = """
                INSERT INTO leads (
                    place_id, cid, name, category, all_categories, phone,
                    full_address, street, city, state, zip_code, country,
                    latitude, longitude, plus_code, website_raw, website_type,
                    website_explanation, has_website, rating, reviews_count,
                    is_claimed, price_level, business_status, maps_url,
                    search_keyword, search_location, scraped_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
                ON CONFLICT(place_id) DO UPDATE SET
                    cid = coalesce(excluded.cid, leads.cid),
                    phone = coalesce(excluded.phone, leads.phone),
                    website_raw = coalesce(excluded.website_raw, leads.website_raw),
                    website_type = excluded.website_type,
                    website_explanation = excluded.website_explanation,
                    has_website = excluded.has_website,
                    rating = coalesce(excluded.rating, leads.rating),
                    reviews_count = max(excluded.reviews_count, leads.reviews_count),
                    is_claimed = coalesce(excluded.is_claimed, leads.is_claimed),
                    full_address = coalesce(excluded.full_address, leads.full_address),
                    scraped_at = excluded.scraped_at;
            """
            params = (
                unique_id,
                lead.cid,
                lead.name,
                lead.category,
                categories_json,
                lead.phone,
                lead.full_address,
                lead.street,
                lead.city,
                lead.state,
                lead.zip_code,
                lead.country,
                lead.latitude,
                lead.longitude,
                lead.plus_code,
                lead.website_raw,
                lead.website_type.value,
                lead.website_explanation,
                1 if lead.has_website else 0,
                lead.rating,
                lead.reviews_count,
                lead.is_claimed.value,
                lead.price_level,
                lead.business_status,
                lead.maps_url,
                lead.search_keyword,
                lead.search_location,
                lead.scraped_at.isoformat(),
            )
            conn.execute(query, params)
            return True

    def save_leads_batch(self, leads: List[Lead]) -> int:
        """Saves a batch of leads in an atomic transaction."""
        count = 0
        for lead in leads:
            if self.save_lead(lead):
                count += 1
        return count

    def enqueue_jobs(self, jobs: List[SearchJob]) -> int:
        """Adds a list of search jobs to the execution queue, avoiding exact duplicates."""
        added = 0
        with self._lock, self._get_connection() as conn:
            for job in jobs:
                # Check for existing job with same keyword and location
                existing = conn.execute(
                    "SELECT id FROM search_queue WHERE keyword = ? AND location_name = ?",
                    (job.keyword, job.location_name),
                ).fetchone()

                if not existing:
                    conn.execute(
                        """
                        INSERT INTO search_queue (
                            keyword, location_name, latitude, longitude, zoom_level,
                            bounding_box, status, attempts, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            job.keyword,
                            job.location_name,
                            job.latitude,
                            job.longitude,
                            job.zoom_level,
                            job.bounding_box,
                            SearchJobStatus.PENDING.value,
                            0,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                    added += 1
        return added

    def claim_next_job(self) -> Optional[SearchJob]:
        """Atomically locks and claims the next pending search job."""
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM search_queue
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT 1;
                """
            ).fetchone()

            if not row:
                return None

            job_id = row["id"]
            conn.execute(
                """
                UPDATE search_queue
                SET status = 'in_progress', attempts = attempts + 1
                WHERE id = ?;
                """,
                (job_id,),
            )

            return SearchJob(
                id=row["id"],
                keyword=row["keyword"],
                location_name=row["location_name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                zoom_level=row["zoom_level"],
                bounding_box=row["bounding_box"],
                status=SearchJobStatus.IN_PROGRESS,
                attempts=row["attempts"] + 1,
            )

    def complete_job(self, job_id: int, results_found: int, leads_saved: int) -> None:
        """Marks a search job as successfully completed."""
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                UPDATE search_queue
                SET status = 'completed',
                    results_found = ?,
                    leads_saved = ?,
                    completed_at = ?
                WHERE id = ?;
                """,
                (results_found, leads_saved, datetime.now(timezone.utc).isoformat(), job_id),
            )

    def fail_job(self, job_id: int, error_msg: str) -> None:
        """Marks a search job as failed."""
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                UPDATE search_queue
                SET status = 'failed',
                    error_message = ?,
                    completed_at = ?
                WHERE id = ?;
                """,
                (error_msg, datetime.now(timezone.utc).isoformat(), job_id),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistical overview of the database."""
        with self._get_connection() as conn:
            total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            no_website_leads = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE has_website = 0"
            ).fetchone()[0]
            social_only = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE website_type = 'social_media'"
            ).fetchone()[0]
            unclaimed = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE is_claimed = 'unclaimed'"
            ).fetchone()[0]

            # Queue statistics
            total_jobs = conn.execute("SELECT COUNT(*) FROM search_queue").fetchone()[0]
            pending_jobs = conn.execute(
                "SELECT COUNT(*) FROM search_queue WHERE status = 'pending'"
            ).fetchone()[0]
            completed_jobs = conn.execute(
                "SELECT COUNT(*) FROM search_queue WHERE status = 'completed'"
            ).fetchone()[0]
            failed_jobs = conn.execute(
                "SELECT COUNT(*) FROM search_queue WHERE status = 'failed'"
            ).fetchone()[0]

            return {
                "total_leads": total_leads,
                "no_website_leads": no_website_leads,
                "social_only_leads": social_only,
                "unclaimed_leads": unclaimed,
                "percentage_no_website": (
                    round((no_website_leads / total_leads) * 100, 1) if total_leads > 0 else 0.0
                ),
                "queue_total": total_jobs,
                "queue_pending": pending_jobs,
                "queue_completed": completed_jobs,
                "queue_failed": failed_jobs,
            }

    def fetch_leads(
        self,
        no_website_only: bool = True,
        state: Optional[str] = None,
        category: Optional[str] = None,
        min_reviews: int = 0,
        unclaimed_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Queries leads matching specified filter criteria for export."""
        with self._get_connection() as conn:
            query = "SELECT * FROM leads WHERE 1=1"
            params: List[Any] = []

            if no_website_only:
                query += " AND has_website = 0"
            if state:
                query += " AND state = ?"
                params.append(state.upper())
            if category:
                query += " AND category LIKE ?"
                params.append(f"%{category}%")
            if min_reviews > 0:
                query += " AND reviews_count >= ?"
                params.append(min_reviews)
            if unclaimed_only:
                query += " AND is_claimed = 'unclaimed'"

            query += " ORDER BY scraped_at DESC"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
