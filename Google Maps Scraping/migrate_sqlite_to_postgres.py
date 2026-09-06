"""One-time, idempotent migration from the legacy SQLite database to PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Sequence

from psycopg.types.json import Jsonb

from config import DEFAULT_CONFIG
from database import Database


TABLES = ("leads", "search_queue", "lead_emails", "email_extraction_status")


def batches(cursor: sqlite3.Cursor, size: int = 1000) -> Iterable[list[sqlite3.Row]]:
    while rows := cursor.fetchmany(size):
        yield rows


def migrate(sqlite_path: Path, database_url: str) -> None:
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"SQLite source not found: {sqlite_path}")

    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    destination = Database(database_url)
    inserted = {table: 0 for table in TABLES}

    lead_columns = (
        "place_id", "cid", "name", "category", "all_categories", "phone",
        "full_address", "street", "city", "state", "zip_code", "country",
        "latitude", "longitude", "plus_code", "website_raw", "website_type",
        "website_explanation", "has_website", "rating", "reviews_count",
        "is_claimed", "price_level", "business_status", "maps_url",
        "search_keyword", "search_location", "scraped_at",
    )
    queue_columns = (
        "id", "keyword", "location_name", "latitude", "longitude", "zoom_level",
        "bounding_box", "status", "results_found", "leads_saved", "error_message",
        "attempts", "created_at", "completed_at",
    )
    email_columns = (
        "id", "place_id", "email", "source_url", "source_type", "confidence",
        "is_free_provider", "discovered_at",
    )
    status_columns = ("place_id", "status", "emails_found_count", "processed_at")

    def placeholders(columns: Sequence[str]) -> str:
        return ", ".join(["%s"] * len(columns))

    def insert_sql(table: str, columns: Sequence[str]) -> str:
        return (
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({placeholders(columns)}) ON CONFLICT DO NOTHING"
        )

    try:
        with destination._get_connection() as target:
            with target.cursor() as target_cursor:
                cursor = source.execute(f"SELECT {', '.join(lead_columns)} FROM leads")
                for rows in batches(cursor):
                    values = []
                    for row in rows:
                        item = [row[column] for column in lead_columns]
                        item[4] = Jsonb(json.loads(item[4] or "[]"))
                        item[18] = bool(item[18])
                        values.append(tuple(item))
                    target_cursor.executemany(insert_sql("leads", lead_columns), values)
                    inserted["leads"] += max(target_cursor.rowcount, 0)

                existing_tables = {
                    row["name"]
                    for row in source.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
                }
                for table, columns in (
                    ("search_queue", queue_columns),
                    ("lead_emails", email_columns),
                    ("email_extraction_status", status_columns),
                ):
                    if table not in existing_tables:
                        continue
                    cursor = source.execute(f"SELECT {', '.join(columns)} FROM {table}")
                    for rows in batches(cursor):
                        values = []
                        for row in rows:
                            item = [row[column] for column in columns]
                            if table == "lead_emails":
                                item[6] = bool(item[6])
                            values.append(tuple(item))
                        target_cursor.executemany(insert_sql(table, columns), values)
                        inserted[table] += max(target_cursor.rowcount, 0)

                for table in ("search_queue", "lead_emails"):
                    target.execute(
                        f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table}', 'id'),
                            greatest(coalesce(max(id), 1), 1),
                            EXISTS (SELECT 1 FROM {table})
                        )
                        FROM {table}
                        """
                    )
    finally:
        source.close()

    source = sqlite3.connect(sqlite_path)
    try:
        source_counts = {
            table: source.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in TABLES
            if source.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
            ).fetchone()
        }
    finally:
        source.close()

    with destination._get_connection() as target:
        destination_counts = {
            table: target.execute(f"SELECT count(*) AS count FROM {table}").fetchone()["count"]
            for table in TABLES
        }

    print(f"Source: {sqlite_path}")
    print(f"Destination: {destination.display_url}")
    for table in TABLES:
        print(
            f"{table}: source={source_counts.get(table, 0):,}, "
            f"destination={destination_counts[table]:,}, inserted_this_run={inserted[table]:,}"
        )

    mismatches = [
        table for table, count in source_counts.items() if destination_counts[table] < count
    ]
    if mismatches:
        raise RuntimeError(f"Migration verification failed for: {', '.join(mismatches)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path(__file__).resolve().parent / "gmaps_leads.db",
        help="Path to the legacy SQLite database",
    )
    parser.add_argument(
        "--database-url",
        default=DEFAULT_CONFIG.database_url,
        help="PostgreSQL connection URL (defaults to scraper environment settings)",
    )
    args = parser.parse_args()
    migrate(args.sqlite_path, args.database_url)


if __name__ == "__main__":
    main()
