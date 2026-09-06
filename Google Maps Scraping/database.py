"""PostgreSQL storage engine for scraped leads and resumable search jobs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from models import Lead, SearchJob, SearchJobStatus


class Database:
    """PostgreSQL database manager for Google Maps leads and queue management."""

    def __init__(self, database_url: str, *, initialize_schema: bool = True) -> None:
        self.database_url = database_url
        if initialize_schema:
            self._init_schema()

    @property
    def display_url(self) -> str:
        """Returns a connection URL safe to print in diagnostics."""
        parsed = urlsplit(self.database_url)
        if parsed.password is None:
            return self.database_url
        username = parsed.username or ""
        hostname = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        return urlunsplit(
            (parsed.scheme, f"{username}:***@{hostname}{port}", parsed.path, parsed.query, parsed.fragment)
        )

    def _get_connection(self) -> psycopg.Connection[Dict[str, Any]]:
        return psycopg.connect(
            self.database_url,
            row_factory=dict_row,
            connect_timeout=10,
            application_name="gmaps_scraper",
        )

    def _init_schema(self) -> None:
        schema_path = Path(__file__).resolve().parent / "postgres" / "init" / "001_schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        with self._get_connection() as conn:
            for statement in schema_sql.split(";"):
                if statement.strip():
                    conn.execute(statement)

    def ping(self) -> bool:
        """Checks that PostgreSQL accepts connections and queries."""
        with self._get_connection() as conn:
            return conn.execute("SELECT 1 AS ok").fetchone()["ok"] == 1

    @staticmethod
    def lead_identifier(lead: Lead) -> str:
        unique_id = lead.place_id
        if not unique_id:
            identity = "\x1f".join((lead.name, lead.phone or "", lead.full_address or ""))
            unique_id = f"custom_{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"
        return unique_id

    @classmethod
    def _lead_values(cls, lead: Lead) -> tuple[Any, ...]:
        return (
            cls.lead_identifier(lead),
            lead.cid,
            lead.name,
            lead.category,
            Jsonb(lead.all_categories),
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
            lead.has_website,
            lead.rating,
            lead.reviews_count,
            lead.is_claimed.value,
            lead.price_level,
            lead.business_status,
            lead.maps_url,
            lead.search_keyword,
            lead.search_location,
            lead.scraped_at,
        )

    @staticmethod
    def _lead_upsert_sql() -> str:
        return """
            INSERT INTO leads (
                place_id, cid, name, category, all_categories, phone,
                full_address, street, city, state, zip_code, country,
                latitude, longitude, plus_code, website_raw, website_type,
                website_explanation, has_website, rating, reviews_count,
                is_claimed, price_level, business_status, maps_url,
                search_keyword, search_location, scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (place_id) DO UPDATE SET
                cid = coalesce(EXCLUDED.cid, leads.cid),
                phone = coalesce(EXCLUDED.phone, leads.phone),
                website_raw = coalesce(EXCLUDED.website_raw, leads.website_raw),
                website_type = EXCLUDED.website_type,
                website_explanation = EXCLUDED.website_explanation,
                has_website = EXCLUDED.has_website,
                rating = coalesce(EXCLUDED.rating, leads.rating),
                reviews_count = greatest(EXCLUDED.reviews_count, leads.reviews_count),
                is_claimed = coalesce(EXCLUDED.is_claimed, leads.is_claimed),
                full_address = coalesce(EXCLUDED.full_address, leads.full_address),
                scraped_at = EXCLUDED.scraped_at
        """

    def save_lead(self, lead: Lead) -> bool:
        """Upserts a single lead record. Returns True when committed."""
        with self._get_connection() as conn:
            conn.execute(self._lead_upsert_sql(), self._lead_values(lead))
        return True

    def save_leads_batch(self, leads: List[Lead]) -> int:
        """Saves a batch of leads in one atomic transaction."""
        if not leads:
            return 0
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(self._lead_upsert_sql(), [self._lead_values(lead) for lead in leads])
        return len(leads)

    def create_campaign(
        self,
        name: str,
        target_jobs: int,
        search_workers: int,
        email_workers: int,
    ) -> int:
        """Creates a durable campaign record and returns its ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO campaigns (name, target_jobs, search_workers, email_workers)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, target_jobs, search_workers, email_workers),
            ).fetchone()
        return row["id"]

    def update_campaign_target(self, campaign_id: int, target_jobs: int) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE campaigns SET target_jobs = %s WHERE id = %s",
                (target_jobs, campaign_id),
            )

    def enqueue_jobs(self, jobs: List[SearchJob], campaign_id: Optional[int] = None) -> int:
        """Adds search jobs to the queue, avoiding keyword/location duplicates."""
        if not jobs:
            return 0
        query = """
            INSERT INTO search_queue (
                keyword, location_name, latitude, longitude, zoom_level,
                bounding_box, status, attempts, created_at, campaign_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (keyword, location_name) DO NOTHING
        """
        added = 0
        with self._get_connection() as conn:
            for job in jobs:
                cursor = conn.execute(
                    query,
                    (
                        job.keyword,
                        job.location_name,
                        job.latitude,
                        job.longitude,
                        job.zoom_level,
                        job.bounding_box,
                        SearchJobStatus.PENDING.value,
                        0,
                        job.created_at,
                        campaign_id if campaign_id is not None else job.campaign_id,
                    ),
                )
                added += cursor.rowcount
        return added

    def claim_next_job(self, campaign_id: Optional[int] = None) -> Optional[SearchJob]:
        """Atomically claims one pending or retryable job across workers."""
        campaign_filter = "AND campaign_id = %s" if campaign_id is not None else ""
        query = """
            WITH next_job AS (
                SELECT id
                FROM search_queue
                WHERE (status = 'pending' OR (status = 'failed' AND attempts < 3))
                {campaign_filter}
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE search_queue AS queue
            SET status = 'in_progress',
                attempts = queue.attempts + 1,
                error_message = NULL,
                completed_at = NULL
            FROM next_job
            WHERE queue.id = next_job.id
            RETURNING queue.*
        """.format(campaign_filter=campaign_filter)
        with self._get_connection() as conn:
            row = conn.execute(query, (campaign_id,) if campaign_id is not None else ()).fetchone()

        if not row:
            return None
        return SearchJob(
            id=row["id"],
            campaign_id=row["campaign_id"],
            keyword=row["keyword"],
            location_name=row["location_name"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            zoom_level=row["zoom_level"],
            bounding_box=row["bounding_box"],
            status=SearchJobStatus.IN_PROGRESS,
            attempts=row["attempts"],
        )

    def enqueue_email_checks(self, campaign_id: int, leads: List[Lead]) -> int:
        """Queues newly saved target leads for durable email enrichment."""
        if not leads:
            return 0
        values = [(campaign_id, self.lead_identifier(lead)) for lead in leads]
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO email_queue (campaign_id, place_id)
                    VALUES (%s, %s)
                    ON CONFLICT (campaign_id, place_id) DO NOTHING
                    """,
                    values,
                )
                added = max(cursor.rowcount, 0)
            conn.execute(
                """
                UPDATE email_queue AS queue
                SET status = CASE
                        WHEN extraction.status = 'completed' THEN 'completed'
                        WHEN extraction.status = 'no_email' THEN 'no_email'
                        ELSE queue.status
                    END,
                    emails_found = extraction.emails_found_count,
                    completed_at = CASE
                        WHEN extraction.status IN ('completed', 'no_email')
                        THEN extraction.processed_at
                        ELSE queue.completed_at
                    END
                FROM email_extraction_status AS extraction
                WHERE queue.campaign_id = %s
                  AND queue.place_id = extraction.place_id
                  AND queue.status = 'pending'
                """,
                (campaign_id,),
            )
        return added

    def claim_next_email_job(self, campaign_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Atomically claims one pending/retryable email job without holding locks during HTTP calls."""
        campaign_filter = "AND queue.campaign_id = %s" if campaign_id is not None else ""
        query = """
            WITH next_job AS (
                SELECT queue.id
                FROM email_queue AS queue
                WHERE (queue.status = 'pending' OR (queue.status = 'failed' AND queue.attempts < 3))
                  {campaign_filter}
                ORDER BY queue.id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            ), claimed AS (
                UPDATE email_queue AS queue
                SET status = 'in_progress',
                    attempts = queue.attempts + 1,
                    started_at = CURRENT_TIMESTAMP,
                    error_message = NULL
                FROM next_job
                WHERE queue.id = next_job.id
                RETURNING queue.id, queue.campaign_id, queue.place_id, queue.attempts
            )
            SELECT claimed.id AS email_job_id, claimed.campaign_id, claimed.attempts,
                   lead.place_id, lead.name, lead.category, lead.phone,
                   lead.full_address, lead.city, lead.state
            FROM claimed
            JOIN leads AS lead ON lead.place_id = claimed.place_id
        """.format(campaign_filter=campaign_filter)
        with self._get_connection() as conn:
            return conn.execute(query, (campaign_id,) if campaign_id is not None else ()).fetchone()

    def complete_email_job(
        self,
        email_job_id: int,
        status: str,
        emails_found: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE email_queue
                SET status = %s, emails_found = %s, error_message = %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (status, emails_found, error_message, email_job_id),
            )

    def reset_interrupted_campaign_work(self, campaign_id: int) -> None:
        """Returns interrupted search and email claims to their queues after a restart."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE search_queue SET status = 'pending' WHERE campaign_id = %s AND status = 'in_progress'",
                (campaign_id,),
            )
            conn.execute(
                "UPDATE email_queue SET status = 'pending' WHERE campaign_id = %s AND status = 'in_progress'",
                (campaign_id,),
            )
            conn.execute(
                """
                UPDATE campaigns
                SET status = 'running', completed_at = NULL
                WHERE id = %s
                """,
                (campaign_id,),
            )

    def email_work_remaining(self, campaign_id: Optional[int] = None) -> int:
        campaign_filter = "AND campaign_id = %s" if campaign_id is not None else ""
        with self._get_connection() as conn:
            row = conn.execute(
                f"""
                SELECT count(*) AS remaining
                FROM email_queue
                WHERE (status IN ('pending', 'in_progress') OR (status = 'failed' AND attempts < 3))
                  {campaign_filter}
                """,
                (campaign_id,) if campaign_id is not None else (),
            ).fetchone()
        return row["remaining"]

    def finish_campaign(self, campaign_id: int, status: str = "completed") -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE campaigns
                SET status = %s, completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (status, campaign_id),
            )

    def get_campaign_stats(self, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Returns search and email progress for a campaign, defaulting to the latest."""
        with self._get_connection() as conn:
            if campaign_id is None:
                campaign = conn.execute("SELECT * FROM campaigns ORDER BY id DESC LIMIT 1").fetchone()
            else:
                campaign = conn.execute("SELECT * FROM campaigns WHERE id = %s", (campaign_id,)).fetchone()
            if not campaign:
                raise ValueError("No matching campaign found")
            search = conn.execute(
                """
                SELECT count(*) AS search_total,
                       count(*) FILTER (WHERE status = 'pending') AS search_pending,
                       count(*) FILTER (WHERE status = 'in_progress') AS search_in_progress,
                       count(*) FILTER (WHERE status = 'completed') AS search_completed,
                       count(*) FILTER (WHERE status = 'failed') AS search_failed,
                       coalesce(sum(results_found), 0) AS results_found,
                       coalesce(sum(leads_saved), 0) AS leads_saved
                FROM search_queue WHERE campaign_id = %s
                """,
                (campaign["id"],),
            ).fetchone()
            email = conn.execute(
                """
                SELECT count(*) AS email_total,
                       count(*) FILTER (WHERE status = 'pending') AS email_pending,
                       count(*) FILTER (WHERE status = 'in_progress') AS email_in_progress,
                       count(*) FILTER (WHERE status = 'completed') AS email_completed,
                       count(*) FILTER (WHERE status = 'no_email') AS email_no_email,
                       count(*) FILTER (WHERE status = 'failed') AS email_failed,
                       coalesce(sum(emails_found), 0) AS emails_found
                FROM email_queue WHERE campaign_id = %s
                """,
                (campaign["id"],),
            ).fetchone()
        return {**campaign, **search, **email}

    def complete_job(self, job_id: int, results_found: int, leads_saved: int) -> None:
        """Marks a search job as successfully completed."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE search_queue
                SET status = 'completed', results_found = %s, leads_saved = %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (results_found, leads_saved, job_id),
            )

    def fail_job(self, job_id: int, error_msg: str) -> None:
        """Marks a search job as failed."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE search_queue
                SET status = 'failed', error_message = %s, completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (error_msg, job_id),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Returns a statistical overview of leads and queued work."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    count(*) AS total_leads,
                    count(*) FILTER (WHERE NOT has_website) AS no_website_leads,
                    count(*) FILTER (WHERE website_type = 'social_media') AS social_only_leads,
                    count(*) FILTER (WHERE is_claimed = 'unclaimed') AS unclaimed_leads
                FROM leads
                """
            ).fetchone()
            queue = conn.execute(
                """
                SELECT
                    count(*) AS queue_total,
                    count(*) FILTER (WHERE status = 'pending') AS queue_pending,
                    count(*) FILTER (WHERE status = 'completed') AS queue_completed,
                    count(*) FILTER (WHERE status = 'failed') AS queue_failed
                FROM search_queue
                """
            ).fetchone()

        total_leads = row["total_leads"]
        return {
            **row,
            **queue,
            "percentage_no_website": (
                round((row["no_website_leads"] / total_leads) * 100, 1) if total_leads else 0.0
            ),
        }

    def fetch_leads(
        self,
        no_website_only: bool = True,
        state: Optional[str] = None,
        category: Optional[str] = None,
        min_reviews: int = 0,
        unclaimed_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Queries leads matching the specified export filters."""
        query = "SELECT * FROM leads WHERE TRUE"
        params: List[Any] = []

        if no_website_only:
            query += " AND NOT has_website"
        if state:
            query += " AND state = %s"
            params.append(state.upper())
        if category:
            query += " AND category ILIKE %s"
            params.append(f"%{category}%")
        if min_reviews > 0:
            query += " AND reviews_count >= %s"
            params.append(min_reviews)
        if unclaimed_only:
            query += " AND is_claimed = 'unclaimed'"

        query += " ORDER BY scraped_at DESC"
        with self._get_connection() as conn:
            return list(conn.execute(query, params).fetchall())
