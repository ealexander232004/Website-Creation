"""Reset email-only state and queue every saved no-website lead for one campaign.

Maps leads and search progress are preserved. This command is intentionally
guarded by --execute because it deletes derived email results before reprocessing.
"""

from __future__ import annotations

import argparse
import json

from config import DEFAULT_CONFIG
from database import Database


def reset_email_enrichment(campaign_id: int, *, execute: bool) -> dict[str, int]:
    db = Database(DEFAULT_CONFIG.database_url)
    with db._get_connection() as conn:
        campaign = conn.execute(
            "SELECT id FROM campaigns WHERE id = %s",
            (campaign_id,),
        ).fetchone()
        if campaign is None:
            raise ValueError(f"Campaign #{campaign_id} does not exist")

        before = conn.execute(
            """
            SELECT
                (SELECT count(*) FROM leads WHERE NOT has_website) AS eligible_leads,
                (SELECT count(*) FROM lead_emails) AS email_rows,
                (SELECT count(*) FROM email_extraction_status) AS status_rows,
                (SELECT count(*) FROM quarantined_emails) AS quarantine_rows,
                (SELECT count(*) FROM email_queue WHERE campaign_id = %s) AS campaign_queue_rows
            """,
            (campaign_id,),
        ).fetchone()
        if not execute:
            return {f"before_{key}": int(value) for key, value in before.items()}

        conn.execute("SET LOCAL lock_timeout = '10s'")
        conn.execute("TRUNCATE TABLE lead_emails, email_extraction_status, quarantined_emails")
        conn.execute("DELETE FROM email_queue WHERE campaign_id = %s", (campaign_id,))
        queued = conn.execute(
            """
            WITH inserted AS (
                INSERT INTO email_queue (campaign_id, place_id)
                SELECT %s, place_id
                FROM leads
                WHERE NOT has_website
                ORDER BY place_id
                ON CONFLICT (campaign_id, place_id) DO NOTHING
                RETURNING 1
            )
            SELECT count(*) AS queued_count FROM inserted
            """,
            (campaign_id,),
        ).fetchone()["queued_count"]
        conn.execute(
            """
            UPDATE search_queue
            SET status = 'pending', error_message = NULL, completed_at = NULL
            WHERE campaign_id = %s AND status = 'in_progress'
            """,
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

    result = {f"before_{key}": int(value) for key, value in before.items()}
    result["requeued_leads"] = int(queued)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id", type=int, required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete derived email rows and rebuild the campaign email queue.",
    )
    args = parser.parse_args()
    print(json.dumps(reset_email_enrichment(args.campaign_id, execute=args.execute), indent=2))


if __name__ == "__main__":
    main()
