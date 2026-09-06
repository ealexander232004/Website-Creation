"""Show live search and email progress for the latest integrated campaign."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from rich.console import Console
from rich.live import Live
from rich.table import Table

from config import DEFAULT_CONFIG
from database import Database


def render(stats: dict) -> Table:
    now = datetime.now(timezone.utc)
    started = stats["started_at"]
    elapsed_seconds = max((now - started).total_seconds(), 1.0)
    search_done = stats["search_completed"] + stats["search_failed"]
    email_done = stats["email_completed"] + stats["email_no_email"] + stats["email_failed"]
    search_total = stats["search_total"] or stats["target_jobs"]
    email_total = stats["email_total"]

    table = Table(title=f"Campaign #{stats['id']}: {stats['name']} [{stats['status']}]")
    table.add_column("Pipeline")
    table.add_column("Done", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Pending", justify="right")
    table.add_column("Running", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Rate", justify="right")
    table.add_row(
        "Google Maps searches",
        f"{search_done:,}",
        f"{search_total:,}",
        f"{stats['search_pending']:,}",
        f"{stats['search_in_progress']:,}",
        f"{stats['search_failed']:,}",
        f"{search_done / (elapsed_seconds / 60):.1f}/min",
    )
    table.add_row(
        "Email checks",
        f"{email_done:,}",
        f"{email_total:,}",
        f"{stats['email_pending']:,}",
        f"{stats['email_in_progress']:,}",
        f"{stats['email_failed']:,}",
        f"{email_done / (elapsed_seconds / 60):.1f}/min",
    )
    table.caption = (
        f"Listings found: {stats['results_found']:,} | Target leads saved: {stats['leads_saved']:,} | "
        f"Emails discovered: {stats['emails_found']:,} | Elapsed: {elapsed_seconds / 3600:.2f}h"
    )
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id", type=int)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=float, default=10.0)
    args = parser.parse_args()

    # Monitoring is read-only. Replaying schema DDL here can request
    # AccessExclusiveLock while active workers hold write locks and deadlock.
    db = Database(DEFAULT_CONFIG.database_url, initialize_schema=False)
    console = Console()
    if not args.watch:
        console.print(render(db.get_campaign_stats(args.campaign_id)))
        return

    with Live(console=console, refresh_per_second=2) as live:
        while True:
            stats = db.get_campaign_stats(args.campaign_id)
            live.update(render(stats), refresh=True)
            if stats["status"] != "running":
                break
            time.sleep(max(args.interval, 1.0))


if __name__ == "__main__":
    main()
