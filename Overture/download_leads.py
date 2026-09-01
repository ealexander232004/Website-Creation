from __future__ import annotations

import argparse
import json
import os
import re
import signal
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import duckdb


RELEASE = "2026-08-19.0"
S3_REGION = "us-west-2"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = SCRIPT_DIR / "overture_smb_leads.duckdb"
DEFAULT_PROGRESS = SCRIPT_DIR / "overture_smb_leads.progress.json"

# Overture does not publish a native small-business flag. These are the taxonomy
# groups that can reasonably contain commercial operators. Government/community,
# cultural/historic, and geographic entities are deliberately excluded from the
# probable-small-business view, but remain in contact_places for audit/review.
COMMERCIAL_TAXONOMY_GROUPS = (
    "arts_and_entertainment",
    "education",
    "food_and_drink",
    "health_care",
    "lifestyle_services",
    "lodging",
    "services_and_business",
    "shopping",
    "sports_and_recreation",
    "travel_and_transportation",
)

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
ROLE_LOCAL_PARTS = (
    "admin",
    "billing",
    "bookings",
    "contact",
    "customerservice",
    "hello",
    "help",
    "info",
    "office",
    "orders",
    "reservations",
    "sales",
    "service",
    "support",
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a resumable local DuckDB of Overture places that have at least "
            "one email and no website."
        )
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--progress-file", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--release", default=RELEASE)
    parser.add_argument(
        "--country",
        default="US",
        help="ISO alpha-2 country code, or ALL for the global dataset (default: US)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Process at most this many not-yet-completed source files.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Source partitions scanned concurrently per transaction (default: 4).",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the progress file without opening the DuckDB database.",
    )
    return parser.parse_args()


def write_progress(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temp_path, path)


def show_status(path: Path) -> int:
    if not path.exists():
        print(f"No progress file exists yet: {path}")
        return 1
    progress = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(progress, indent=2))
    return 0


def validate_country(value: str) -> str | None:
    country = value.strip().upper()
    if country == "ALL":
        return None
    if not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError("--country must be a two-letter ISO code or ALL")
    return country


def configure_connection(database: Path) -> duckdb.DuckDBPyConnection:
    database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database))
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute(f"SET s3_region='{S3_REGION}'")
    con.execute("SET http_timeout=120000")
    con.execute("SET enable_progress_bar=false")
    con.execute("SET threads=12")
    con.execute("SET enable_object_cache=true")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET checkpoint_threshold='1GB'")
    return con


def initialize_schema(
    con: duckdb.DuckDBPyConnection, release: str, country: str | None
) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS build_metadata (
            key VARCHAR PRIMARY KEY,
            value VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS processed_partitions (
            source_file VARCHAR PRIMARY KEY,
            status VARCHAR NOT NULL,
            rows_inserted BIGINT DEFAULT 0,
            emails_inserted BIGINT DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            elapsed_seconds DOUBLE,
            error VARCHAR
        );

        CREATE TABLE IF NOT EXISTS contact_places (
            id VARCHAR PRIMARY KEY,
            business_name VARCHAR,
            primary_category VARCHAR,
            basic_category VARCHAR,
            industry_group VARCHAR,
            taxonomy_hierarchy VARCHAR[],
            alternate_categories VARCHAR[],
            emails VARCHAR[],
            phones VARCHAR[],
            socials VARCHAR[],
            websites VARCHAR[],
            street_address VARCHAR,
            city VARCHAR,
            region VARCHAR,
            postcode VARCHAR,
            country VARCHAR,
            longitude DOUBLE,
            latitude DOUBLE,
            brand_name VARCHAR,
            is_known_brand BOOLEAN NOT NULL,
            is_probable_small_business BOOLEAN NOT NULL,
            confidence DOUBLE,
            quality_tier VARCHAR,
            operating_status VARCHAR,
            all_names JSON,
            all_addresses JSON,
            brand JSON,
            source_records JSON,
            overture_release VARCHAR NOT NULL,
            source_file VARCHAR NOT NULL,
            ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        );

        CREATE TABLE IF NOT EXISTS lead_emails (
            place_id VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            email_domain VARCHAR,
            is_syntax_valid BOOLEAN NOT NULL,
            is_role_account BOOLEAN NOT NULL,
            source_file VARCHAR NOT NULL,
            PRIMARY KEY (place_id, email)
        );
        """
    )

    expected = {
        "overture_release": release,
        "country_scope": country or "ALL",
        "no_website_rule": "websites IS NULL OR len(websites) = 0; socials do not count as websites",
        "small_business_rule": (
            "no Overture native flag; no known brand and taxonomy L0 is in the configured "
            "commercial group list"
        ),
    }
    existing = dict(con.execute("SELECT key, value FROM build_metadata").fetchall())
    for key in ("overture_release", "country_scope"):
        if key in existing and existing[key] != expected[key]:
            raise RuntimeError(
                f"Database metadata mismatch for {key}: database has "
                f"{existing[key]!r}, requested {expected[key]!r}. Use a different "
                "--database path for a different scope."
            )
    con.executemany(
        "INSERT OR REPLACE INTO build_metadata (key, value) VALUES (?, ?)",
        list(expected.items()),
    )

    groups = ", ".join(f"'{group}'" for group in COMMERCIAL_TAXONOMY_GROUPS)
    con.execute(
        f"""
        CREATE OR REPLACE VIEW usable_emails AS
        SELECT
            e.place_id,
            e.email,
            e.email_domain,
            e.is_role_account,
            count(*) OVER (PARTITION BY e.email) AS places_using_email
        FROM lead_emails e
        WHERE e.is_syntax_valid;

        CREATE OR REPLACE VIEW small_business_leads AS
        SELECT
            p.*,
            (SELECT count(*) FROM usable_emails e WHERE e.place_id = p.id)
                AS usable_email_count
        FROM contact_places p
        WHERE p.is_probable_small_business
          AND coalesce(p.operating_status, 'open') <> 'permanently_closed'
          AND EXISTS (
              SELECT 1 FROM usable_emails e WHERE e.place_id = p.id
          );

        CREATE OR REPLACE VIEW database_summary AS
        SELECT
            (SELECT count(*) FROM processed_partitions WHERE status = 'completed')
                AS completed_partitions,
            (SELECT count(*) FROM contact_places) AS contact_places,
            (SELECT count(*) FROM small_business_leads) AS small_business_leads,
            (SELECT count(*) FROM lead_emails) AS email_records,
            (SELECT count(*) FROM usable_emails) AS syntax_valid_email_records,
            (SELECT count(DISTINCT email) FROM usable_emails) AS unique_usable_emails,
            (SELECT count(*) FROM contact_places WHERE industry_group IN ({groups}))
                AS commercial_taxonomy_places;
        """
    )


def source_files(con: duckdb.DuckDBPyConnection, release: str) -> list[str]:
    path = (
        f"s3://overturemaps-us-west-2/release/{release}/"
        "theme=places/type=place/*.parquet"
    )
    return [
        row[0]
        for row in con.execute(
            "SELECT file FROM glob(?) ORDER BY file", [path]
        ).fetchall()
    ]


def country_expressions(country: str | None) -> tuple[str, str]:
    if country is None:
        return "TRUE", "addresses[1]"

    # The list_filter expression keeps the selected address consistent with the
    # country predicate even when a place has multiple addresses.
    escaped = country.replace("'", "''")
    address = f"list_filter(addresses, a -> a.country = '{escaped}')[1]"
    predicate = (
        "addresses IS NOT NULL AND EXISTS ("
        "SELECT 1 FROM unnest(addresses) AS address_row(address) "
        f"WHERE address.country = '{escaped}')"
    )
    return predicate, address


def ingest_partitions(
    con: duckdb.DuckDBPyConnection,
    source_files: list[str],
    release: str,
    country: str | None,
) -> tuple[dict[str, tuple[int, int]], float]:
    country_predicate, address = country_expressions(country)
    groups = ", ".join(f"'{group}'" for group in COMMERCIAL_TAXONOMY_GROUPS)
    started = time.monotonic()

    con.execute("BEGIN TRANSACTION")
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO processed_partitions (
                source_file, status, rows_inserted, emails_inserted,
                started_at, completed_at, elapsed_seconds, error
            ) VALUES (?, 'processing', 0, 0, current_timestamp, NULL, NULL, NULL)
            """,
            [(source_file,) for source_file in source_files],
        )

        con.execute(
            f"""
            INSERT OR IGNORE INTO contact_places
            SELECT
                id,
                names.primary AS business_name,
                taxonomy.primary AS primary_category,
                basic_category,
                taxonomy.hierarchy[1] AS industry_group,
                taxonomy.hierarchy,
                taxonomy.alternates AS alternate_categories,
                emails,
                phones,
                socials,
                websites,
                ({address}).freeform AS street_address,
                ({address}).locality AS city,
                ({address}).region AS region,
                ({address}).postcode AS postcode,
                ({address}).country AS country,
                bbox.xmin::DOUBLE AS longitude,
                bbox.ymin::DOUBLE AS latitude,
                brand.names.primary AS brand_name,
                coalesce(
                    brand IS NOT NULL AND (
                        brand.wikidata IS NOT NULL OR brand.names.primary IS NOT NULL
                    ),
                    false
                ) AS is_known_brand,
                coalesce(
                    NOT coalesce(
                        brand IS NOT NULL AND (
                            brand.wikidata IS NOT NULL OR brand.names.primary IS NOT NULL
                        ),
                        false
                    )
                    AND coalesce(taxonomy.hierarchy[1] IN ({groups}), false),
                    false
                ) AS is_probable_small_business,
                confidence,
                CASE
                    WHEN confidence >= 0.80 THEN 'high'
                    WHEN confidence >= 0.50 THEN 'medium'
                    WHEN confidence IS NULL THEN 'unknown'
                    ELSE 'low'
                END AS quality_tier,
                operating_status,
                to_json(names) AS all_names,
                to_json(addresses) AS all_addresses,
                to_json(brand) AS brand,
                to_json(sources) AS source_records,
                ? AS overture_release,
                filename AS source_file,
                current_timestamp AS ingested_at
            FROM read_parquet(?, filename=true)
            WHERE coalesce(len(emails), 0) > 0
              AND coalesce(len(websites), 0) = 0
              AND {country_predicate}
            """,
            [release, source_files],
        )

        role_values = ", ".join(f"'{value}'" for value in ROLE_LOCAL_PARTS)
        con.execute(
            f"""
            INSERT OR IGNORE INTO lead_emails
            WITH normalized AS (
                SELECT
                    p.id AS place_id,
                    lower(trim(regexp_replace(raw_email, '(?i)^mailto:', '')))
                        AS email,
                    p.source_file
                FROM contact_places p,
                     unnest(p.emails) AS email_row(raw_email)
                WHERE list_contains(?, p.source_file)
                  AND raw_email IS NOT NULL
            )
            SELECT
                place_id,
                email,
                CASE WHEN contains(email, '@')
                    THEN split_part(email, '@', 2)
                    ELSE NULL
                END AS email_domain,
                regexp_full_match(email, '{EMAIL_REGEX}') AS is_syntax_valid,
                split_part(email, '@', 1) IN ({role_values}) AS is_role_account,
                source_file
            FROM normalized
            WHERE email <> ''
            """,
            [source_files],
        )

        place_counts = dict(
            con.execute(
                """
                SELECT source_file, count(*)
                FROM contact_places
                WHERE list_contains(?, source_file)
                GROUP BY source_file
                """,
                [source_files],
            ).fetchall()
        )
        email_counts = dict(
            con.execute(
                """
                SELECT source_file, count(*)
                FROM lead_emails
                WHERE list_contains(?, source_file)
                GROUP BY source_file
                """,
                [source_files],
            ).fetchall()
        )
        elapsed = time.monotonic() - started

        con.executemany(
            """
            UPDATE processed_partitions
            SET status = 'completed', rows_inserted = ?, emails_inserted = ?,
                completed_at = current_timestamp, elapsed_seconds = ?, error = NULL
            WHERE source_file = ?
            """,
            [
                (
                    place_counts.get(source_file, 0),
                    email_counts.get(source_file, 0),
                    elapsed,
                    source_file,
                )
                for source_file in source_files
            ],
        )
        con.execute("COMMIT")
        return {
            source_file: (
                place_counts.get(source_file, 0),
                email_counts.get(source_file, 0),
            )
            for source_file in source_files
        }, elapsed
    except BaseException:
        con.execute("ROLLBACK")
        raise


def counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    completed, places, probable, email_rows, valid, unique = con.execute(
        """
        SELECT
            (SELECT count(*) FROM processed_partitions WHERE status = 'completed'),
            (SELECT count(*) FROM contact_places),
            (SELECT count(*) FROM small_business_leads),
            (SELECT count(*) FROM lead_emails),
            (SELECT count(*) FROM usable_emails),
            (SELECT count(DISTINCT email) FROM usable_emails)
        """
    ).fetchone()
    return {
        "completed_partitions": completed,
        "contact_places": places,
        "probable_small_business_leads": probable,
        "email_records": email_rows,
        "syntax_valid_email_records": valid,
        "unique_syntax_valid_emails": unique,
    }


def main() -> int:
    args = parse_args()
    if args.status:
        return show_status(args.progress_file.resolve())

    country = validate_country(args.country)
    database = args.database.resolve()
    progress_path = args.progress_file.resolve()
    con = configure_connection(database)
    initialize_schema(con, args.release, country)

    files = source_files(con, args.release)
    completed = {
        row[0]
        for row in con.execute(
            "SELECT source_file FROM processed_partitions WHERE status = 'completed'"
        ).fetchall()
    }
    pending = [source_file for source_file in files if source_file not in completed]
    if args.max_files is not None:
        if args.max_files < 1:
            raise ValueError("--max-files must be at least 1")
        pending = pending[: args.max_files]
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    batches = [
        pending[index : index + args.batch_size]
        for index in range(0, len(pending), args.batch_size)
    ]

    progress = {
        "status": "running",
        "database": str(database),
        "release": args.release,
        "country": country or "ALL",
        "total_partitions": len(files),
        "partitions_selected_this_run": len(pending),
        "batch_size": args.batch_size,
        "batches_selected_this_run": len(batches),
        "started_at": utc_now(),
        "updated_at": utc_now(),
        **counts(con),
    }
    write_progress(progress_path, progress)

    interrupted = False

    def handle_signal(_signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = True
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)

    print(f"Database: {database}", flush=True)
    print(f"Overture release: {args.release}", flush=True)
    print(f"Country scope: {country or 'ALL'}", flush=True)
    print(
        f"Source partitions: {len(files)} total, {len(completed)} already complete, "
        f"{len(pending)} selected",
        flush=True,
    )

    try:
        for batch_index, batch_files in enumerate(batches, start=1):
            global_indices = [files.index(source_file) + 1 for source_file in batch_files]
            partition_names = [
                source_file.rsplit("/", 1)[-1] for source_file in batch_files
            ]
            progress.pop("error", None)
            progress.update(
                {
                    "status": "running",
                    "current_partitions": global_indices,
                    "current_partition_names": partition_names,
                    "current_batch_started_at": utc_now(),
                    "updated_at": utc_now(),
                }
            )
            write_progress(progress_path, progress)
            print(
                f"[batch {batch_index}/{len(batches)}; partitions "
                f"{global_indices[0]}-{global_indices[-1]}/{len(files)}] "
                f"{len(batch_files)} files",
                flush=True,
            )

            try:
                batch_counts, elapsed = ingest_partitions(
                    con, batch_files, args.release, country
                )
            except Exception as exc:
                if interrupted:
                    raise KeyboardInterrupt from exc
                con.executemany(
                    """
                    INSERT OR REPLACE INTO processed_partitions (
                        source_file, status, rows_inserted, emails_inserted,
                        started_at, completed_at, elapsed_seconds, error
                    ) VALUES (?, 'failed', 0, 0, current_timestamp,
                              current_timestamp, NULL, ?)
                    """,
                    [(source_file, str(exc)) for source_file in batch_files],
                )
                progress.update(
                    {
                        "status": "failed",
                        "error": str(exc),
                        "updated_at": utc_now(),
                        **counts(con),
                    }
                )
                write_progress(progress_path, progress)
                print(f"  FAILED: {exc}", file=sys.stderr, flush=True)
                continue

            place_count = sum(value[0] for value in batch_counts.values())
            email_count = sum(value[1] for value in batch_counts.values())
            progress.update(
                {
                    "last_batch_partitions": global_indices,
                    "last_batch_places": place_count,
                    "last_batch_emails": email_count,
                    "last_batch_seconds": round(elapsed, 1),
                    "updated_at": utc_now(),
                    **counts(con),
                }
            )
            write_progress(progress_path, progress)
            print(
                f"  committed {len(batch_files)} files: {place_count:,} contact "
                f"places; {email_count:,} email rows; {elapsed:.1f}s",
                flush=True,
            )
    except KeyboardInterrupt:
        interrupted = True
    finally:
        final_counts = counts(con)
        all_completed = final_counts["completed_partitions"] == len(files)
        final_status = "complete" if all_completed else ("stopped" if interrupted else "paused")
        progress.update(
            {
                "status": final_status,
                "current_partitions": None,
                "current_partition_names": None,
                "updated_at": utc_now(),
                "finished_at": utc_now(),
                **final_counts,
            }
        )
        write_progress(progress_path, progress)
        con.close()

    print(json.dumps(progress, indent=2), flush=True)
    return 130 if interrupted else 0


if __name__ == "__main__":
    raise SystemExit(main())
