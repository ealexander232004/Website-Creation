"""Run the read-only email funnel audit and save a timestamped logical snapshot."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from config import DEFAULT_CONFIG


SQL_PATH = HERE / "email_funnel_audit.sql"
OUTPUT_PATH = HERE / "email_funnel_snapshot.json"


EXTRA_QUERIES = {
    "campaigns": """
        SELECT id, name, status, target_jobs, search_workers, email_workers,
               started_at, completed_at
        FROM campaigns
        ORDER BY id
    """,
    "first_campaign_cohort_quality": """
        WITH first_queue AS (
            SELECT DISTINCT ON (place_id) place_id, campaign_id
            FROM email_queue
            ORDER BY place_id, created_at, id
        )
        SELECT
            first_queue.campaign_id,
            count(*) AS businesses,
            round(100.0 * count(*) FILTER (
                WHERE lead.phone IS NOT NULL AND btrim(lead.phone) <> ''
            ) / count(*), 2) AS phone_coverage_pct,
            round(100.0 * count(*) FILTER (
                WHERE lead.city IS NOT NULL AND btrim(lead.city) <> ''
            ) / count(*), 2) AS city_coverage_pct,
            round(avg(lead.reviews_count), 1) AS mean_reviews,
            count(*) FILTER (WHERE lead.website_type = 'social_media') AS social_profile_businesses,
            count(*) FILTER (WHERE lead.website_type = 'none') AS true_no_website_businesses
        FROM first_queue
        JOIN leads AS lead USING (place_id)
        GROUP BY first_queue.campaign_id
        ORDER BY first_queue.campaign_id
    """,
    "hourly_extraction_outcomes": """
        SELECT
            date_trunc('hour', processed_at AT TIME ZONE 'America/Los_Angeles') AS hour_pt,
            count(*) AS processed_businesses,
            count(*) FILTER (WHERE status = 'completed') AS businesses_with_email,
            round(100.0 * count(*) FILTER (WHERE status = 'completed') / count(*), 2) AS hit_rate_pct
        FROM email_extraction_status
        GROUP BY 1
        ORDER BY 1
    """,
    "email_source_by_first_campaign": """
        WITH first_queue AS (
            SELECT DISTINCT ON (place_id) place_id, campaign_id
            FROM email_queue
            ORDER BY place_id, created_at, id
        )
        SELECT
            first_queue.campaign_id,
            email.source_type,
            count(*) AS email_rows,
            count(DISTINCT email.place_id) AS businesses
        FROM first_queue
        JOIN lead_emails AS email USING (place_id)
        GROUP BY first_queue.campaign_id, email.source_type
        ORDER BY first_queue.campaign_id, email.source_type
    """,
    "status_consistency": """
        WITH saved AS (
            SELECT place_id, count(*) AS saved_email_rows
            FROM lead_emails
            GROUP BY place_id
        )
        SELECT
            count(*) FILTER (WHERE status.status = 'completed' AND saved.place_id IS NULL)
                AS completed_without_saved_email,
            count(*) FILTER (WHERE status.status = 'no_email' AND saved.place_id IS NOT NULL)
                AS no_email_with_saved_email,
            count(*) FILTER (
                WHERE status.status = 'completed'
                  AND status.emails_found_count <> saved.saved_email_rows
            ) AS completed_count_mismatches
        FROM email_extraction_status AS status
        LEFT JOIN saved USING (place_id)
    """,
    "highest_reuse_patterns": """
        SELECT
            lower(split_part(email.email, '@', 2)) AS email_domain,
            email.source_type,
            lower(split_part(split_part(email.source_url, '://', 2), '/', 1)) AS source_host,
            count(DISTINCT email.place_id) AS businesses_using_exact_address
        FROM lead_emails AS email
        GROUP BY lower(btrim(email.email)), email_domain, email.source_type, source_host
        HAVING count(DISTINCT email.place_id) > 1
        ORDER BY businesses_using_exact_address DESC, email_domain
        LIMIT 20
    """,
}


def sql_statements() -> list[str]:
    raw = SQL_PATH.read_text(encoding="utf-8")
    without_comments = "\n".join(
        line for line in raw.splitlines() if not line.lstrip().startswith("--")
    )
    return [statement.strip() for statement in without_comments.split(";") if statement.strip()]


def main() -> None:
    snapshot: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timezone_for_hourly_rows": "America/Los_Angeles",
        "source_tables": [
            "public.leads",
            "public.email_queue",
            "public.email_extraction_status",
            "public.lead_emails",
            "public.campaigns",
        ],
        "audit_queries": [],
        "supplemental_queries": {},
    }

    with psycopg.connect(DEFAULT_CONFIG.database_url, row_factory=dict_row) as connection:
        for query_index, statement in enumerate(sql_statements(), start=1):
            rows = connection.execute(statement).fetchall()
            snapshot["audit_queries"].append(
                {"query_index": query_index, "rows": rows}
            )

        for name, statement in EXTRA_QUERIES.items():
            snapshot["supplemental_queries"][name] = connection.execute(statement).fetchall()

    OUTPUT_PATH.write_text(
        json.dumps(snapshot, default=str, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(snapshot, default=str, indent=2))


if __name__ == "__main__":
    main()
