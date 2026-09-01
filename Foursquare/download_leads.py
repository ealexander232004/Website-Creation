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
from typing import Iterable

import duckdb
import requests
from huggingface_hub import HfApi, get_token, hf_hub_url


REPO_ID = "foursquare/fsq-os-places"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = SCRIPT_DIR / "foursquare_email_no_website.duckdb"
DEFAULT_PROGRESS = SCRIPT_DIR / "foursquare_email_no_website.progress.json"
DEFAULT_OVERTURE_DATABASE = SCRIPT_DIR.parent / "Overture" / "overture_smb_leads.duckdb"

# Foursquare's official non-commercial category exclusion list:
# https://docs.foursquare.com/data-products/docs/access-fsq-os-places
NONCOMMERCIAL_CATEGORIES = (
    ("4bf58dd8d48988d1f0931735", "Airport Gate"),
    ("62d587aeda6648532de2b88c", "Beer Festival"),
    ("4bf58dd8d48988d12b951735", "Bus Line"),
    ("52f2ab2ebcbc57f1066b8b3b", "Christmas Market"),
    ("50aa9e094b90af0d42d5de0d", "City"),
    ("5267e4d9e4b0ec79466e48c6", "Conference"),
    ("5267e4d9e4b0ec79466e48c9", "Convention"),
    ("530e33ccbcbc57f1066bbff7", "Country"),
    ("5345731ebcbc57f1066c39b2", "County"),
    ("63be6904847c3692a84b9bb7", "Entertainment Event"),
    ("4d4b7105d754a06373d81259", "Event"),
    ("5267e4d9e4b0ec79466e48c7", "Festival"),
    ("4bf58dd8d48988d132951735", "Hotel Pool"),
    ("52f2ab2ebcbc57f1066b8b4c", "Intersection"),
    ("50aaa4314b90af0d42d5de10", "Island"),
    ("58daa1558bbb0b01f18ec1fa", "Line"),
    ("63be6904847c3692a84b9bb8", "Marketplace"),
    ("4f2a23984b9023bd5841ed2c", "Moving Target"),
    ("5267e4d9e4b0ec79466e48d1", "Music Festival"),
    ("4f2a25ac4b909258e854f55f", "Neighborhood"),
    ("5267e4d9e4b0ec79466e48c8", "Other Event"),
    ("52741d85e4b0d5d1e3c6a6d9", "Parade"),
    ("4bf58dd8d48988d1f7931735", "Plane"),
    ("4f4531504b9074f6e4fb0102", "Platform"),
    ("4cae28ecbf23941eb1190695", "Polling Place"),
    ("4bf58dd8d48988d1f9931735", "Road"),
    ("5bae9231bedf3950379f89c5", "Sporting Event"),
    ("530e33ccbcbc57f1066bbff8", "State"),
    ("530e33ccbcbc57f1066bbfe4", "States and Municipalities"),
    ("52f2ab2ebcbc57f1066b8b54", "Stoop Sale"),
    ("5267e4d8e4b0ec79466e48c5", "Street Fair"),
    ("53e0feef498e5aac066fd8a9", "Street Food Gathering"),
    ("4bf58dd8d48988d130951735", "Taxi"),
    ("530e33ccbcbc57f1066bbff3", "Town"),
    ("5bae9231bedf3950379f89c3", "Trade Fair"),
    ("4bf58dd8d48988d12a951735", "Train"),
    ("52e81612bcbc57f1066b7a24", "Tree"),
    ("530e33ccbcbc57f1066bbff9", "Village"),
)

DISQUALIFYING_FLAGS = ("closed", "duplicate", "delete", "doesnt_exist", "privatevenue")
ROLE_LOCAL_PARTS = (
    "admin", "billing", "bookings", "contact", "customerservice", "hello",
    "help", "info", "office", "orders", "reservations", "sales", "service",
    "support",
)
PLACEHOLDER_LOCAL_PARTS = (
    "email", "example", "fake", "invalid", "na", "noreply", "no-reply",
    "none", "null", "sample", "test", "yourname",
)
PLACEHOLDER_DOMAINS = (
    "domain.com", "email.com", "example.com", "example.org", "invalid.com",
    "localhost", "test.com",
)
EMAIL_REGEX = r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a resumable Foursquare email/no-website lead database."
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--progress-file", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument(
        "--release",
        default="LATEST",
        help="Release date (YYYY-MM-DD), or LATEST (default).",
    )
    parser.add_argument("--country", default="US", help="ISO alpha-2 code (default: US).")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--finalize-only", action="store_true")
    parser.add_argument(
        "--overture-database", type=Path, default=DEFAULT_OVERTURE_DATABASE
    )
    parser.add_argument(
        "--skip-overture-dedupe", action="store_true",
        help="Do not create cross-source Overture match tables/views.",
    )
    return parser.parse_args()


def write_progress(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def show_status(path: Path) -> int:
    if not path.exists():
        print(f"No progress file exists yet: {path}")
        return 1
    print(path.read_text(encoding="utf-8"))
    return 0


def normalized_country(value: str) -> str:
    result = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", result):
        raise ValueError("--country must be a two-letter ISO country code")
    return result


def configure_connection(database: Path) -> duckdb.DuckDBPyConnection:
    database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database))
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute("SET http_timeout=120000")
    # Hugging Face/Xet signed URLs include literal asterisks in query parameters.
    # They are URL data, not a DuckDB filename glob.
    con.execute("SET allow_asterisks_in_http_paths=true")
    con.execute("SET threads=12")
    con.execute("SET enable_object_cache=true")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET checkpoint_threshold='1GB'")
    return con


def initialize_schema(
    con: duckdb.DuckDBPyConnection, release: str, country: str
) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS build_metadata (
            key VARCHAR PRIMARY KEY,
            value VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_manifest (
            source_file VARCHAR PRIMARY KEY,
            size_bytes BIGINT NOT NULL,
            file_type VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS processed_files (
            source_file VARCHAR PRIMARY KEY,
            status VARCHAR NOT NULL,
            rows_inserted BIGINT DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            elapsed_seconds DOUBLE,
            error VARCHAR
        );

        CREATE TABLE IF NOT EXISTS noncommercial_categories (
            category_id VARCHAR PRIMARY KEY,
            category_name VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contact_places (
            fsq_place_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            address VARCHAR,
            locality VARCHAR,
            region VARCHAR,
            postcode VARCHAR,
            admin_region VARCHAR,
            post_town VARCHAR,
            po_box VARCHAR,
            country VARCHAR,
            date_created DATE,
            date_refreshed DATE,
            date_closed DATE,
            tel VARCHAR,
            website VARCHAR,
            email VARCHAR,
            facebook_id VARCHAR,
            instagram VARCHAR,
            twitter VARCHAR,
            fsq_category_ids VARCHAR[],
            fsq_category_labels VARCHAR[],
            placemaker_url VARCHAR,
            unresolved_flags VARCHAR[],
            has_noncommercial_category BOOLEAN NOT NULL DEFAULT false,
            has_disqualifying_flag BOOLEAN NOT NULL DEFAULT false,
            source_file VARCHAR NOT NULL,
            fsq_release VARCHAR NOT NULL,
            ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        );

        CREATE TABLE IF NOT EXISTS lead_emails (
            fsq_place_id VARCHAR PRIMARY KEY,
            email VARCHAR NOT NULL,
            normalized_email VARCHAR NOT NULL,
            email_domain VARCHAR,
            is_syntax_valid BOOLEAN NOT NULL,
            is_placeholder BOOLEAN NOT NULL,
            is_role_account BOOLEAN NOT NULL,
            is_usable BOOLEAN NOT NULL
        );
        """
    )
    con.executemany(
        "INSERT OR REPLACE INTO noncommercial_categories VALUES (?, ?)",
        NONCOMMERCIAL_CATEGORIES,
    )

    expected = {
        "repository": REPO_ID,
        "release": release,
        "country_scope": country,
        "date_refreshed_rule": "none; all source refresh dates retained",
        "candidate_rule": "email nonblank; website null/blank; country matches scope",
        "business_rule": (
            "date_closed null; no official noncommercial category; no disqualifying "
            "unresolved flag; syntax-valid non-placeholder email"
        ),
    }
    existing = dict(con.execute("SELECT key, value FROM build_metadata").fetchall())
    for key in ("repository", "release", "country_scope"):
        if key in existing and existing[key] != expected[key]:
            raise RuntimeError(
                f"Database metadata mismatch for {key}: {existing[key]!r} vs "
                f"{expected[key]!r}. Use a different --database path."
            )
    con.executemany(
        "INSERT OR REPLACE INTO build_metadata VALUES (?, ?)", expected.items()
    )
    create_views(con)


def create_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE VIEW qualified_leads AS
        SELECT p.*, e.normalized_email, e.email_domain, e.is_role_account
        FROM contact_places p
        JOIN lead_emails e USING (fsq_place_id)
        WHERE p.date_closed IS NULL
          AND NOT p.has_noncommercial_category
          AND NOT p.has_disqualifying_flag
          AND e.is_usable;

        CREATE OR REPLACE VIEW database_summary AS
        SELECT
            (SELECT count(*) FROM source_manifest WHERE file_type = 'place') AS source_files,
            (SELECT coalesce(sum(size_bytes), 0) FROM source_manifest WHERE file_type = 'place') AS source_bytes,
            (SELECT count(*) FROM processed_files WHERE status = 'completed') AS completed_files,
            (SELECT count(*) FROM contact_places) AS contact_candidates,
            (SELECT count(*) FROM contact_places WHERE date_closed IS NOT NULL) AS closed_candidates,
            (SELECT count(*) FROM contact_places WHERE has_noncommercial_category) AS noncommercial_candidates,
            (SELECT count(*) FROM contact_places WHERE has_disqualifying_flag) AS flagged_candidates,
            (SELECT count(*) FROM lead_emails WHERE is_syntax_valid) AS syntax_valid_emails,
            (SELECT count(*) FROM lead_emails WHERE is_usable) AS usable_emails,
            (SELECT count(*) FROM qualified_leads) AS qualified_leads;
        """
    )


def discover_release(api: HfApi, requested: str) -> str:
    if requested.upper() != "LATEST":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", requested):
            raise ValueError("--release must be YYYY-MM-DD or LATEST")
        return requested
    releases = [
        item.path.split("dt=", 1)[1]
        for item in api.list_repo_tree(
            REPO_ID, path_in_repo="release", repo_type="dataset", recursive=False
        )
        if "dt=" in item.path
    ]
    if not releases:
        raise RuntimeError("No Foursquare releases were found")
    return max(releases)


def list_manifest(api: HfApi, release: str) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    def files(path: str) -> list[tuple[str, int]]:
        return sorted(
            (
                (item.path, int(item.size or 0))
                for item in api.list_repo_tree(
                    REPO_ID, path_in_repo=path, repo_type="dataset", recursive=False
                )
                if item.path.endswith(".parquet")
            ),
            key=lambda row: row[0],
        )

    places = files(f"release/dt={release}/places/parquet")
    categories = files(f"release/dt={release}/categories/parquet")
    if not places:
        raise RuntimeError(f"No Places Parquet files found for release {release}")
    return places, categories


def resolved_token() -> str | None:
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or get_token()


def signed_download_url(source_file: str, token: str) -> str:
    source_url = hf_hub_url(REPO_ID, source_file, repo_type="dataset")
    response = requests.get(
        source_url,
        headers={"Authorization": f"Bearer {token}"},
        allow_redirects=True,
        stream=True,
        timeout=60,
    )
    try:
        if response.status_code in (401, 403):
            raise PermissionError(
                "Hugging Face denied this token. Log in, accept the Foursquare "
                "dataset conditions, and use a read token in HF_TOKEN."
            )
        response.raise_for_status()
        return response.url
    finally:
        response.close()


def insert_manifest(
    con: duckdb.DuckDBPyConnection,
    places: Iterable[tuple[str, int]],
    categories: Iterable[tuple[str, int]],
) -> None:
    rows = [(path, size, "place") for path, size in places]
    rows.extend((path, size, "category") for path, size in categories)
    con.executemany(
        "INSERT OR REPLACE INTO source_manifest VALUES (?, ?, ?)", rows
    )


def import_categories(
    con: duckdb.DuckDBPyConnection,
    category_files: list[tuple[str, int]],
    token: str,
) -> None:
    if not category_files:
        return
    urls = [signed_download_url(path, token) for path, _ in category_files]
    con.execute(
        "CREATE OR REPLACE TABLE fsq_categories AS SELECT * FROM read_parquet(?)",
        [urls],
    )


def sql_values(values: Iterable[str]) -> str:
    return ", ".join("'" + value.replace("'", "''") + "'" for value in values)


def ingest_batch(
    con: duckdb.DuckDBPyConnection,
    batch: list[tuple[str, int]],
    release: str,
    country: str,
    token: str,
) -> tuple[int, float]:
    started = time.monotonic()
    paths = [path for path, _ in batch]
    basenames = [path.rsplit("/", 1)[-1] for path in paths]
    urls = [signed_download_url(path, token) for path in paths]
    filename_expression = "regexp_extract(filename, 'places_[0-9]+\\.parquet')"
    flags = sql_values(DISQUALIFYING_FLAGS)
    roles = sql_values(ROLE_LOCAL_PARTS)
    placeholders = sql_values(PLACEHOLDER_LOCAL_PARTS)
    placeholder_domains = sql_values(PLACEHOLDER_DOMAINS)

    con.execute("BEGIN TRANSACTION")
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO processed_files
            VALUES (?, 'processing', 0, current_timestamp, NULL, NULL, NULL)
            """,
            [(path,) for path in paths],
        )
        before = con.execute("SELECT count(*) FROM contact_places").fetchone()[0]
        con.execute(
            f"""
            INSERT OR IGNORE INTO contact_places
            SELECT
                fsq_place_id, name, latitude::DOUBLE, longitude::DOUBLE,
                address, locality, region, postcode, admin_region, post_town,
                po_box, upper(country), date_created::DATE, date_refreshed::DATE,
                date_closed::DATE, tel, website, email, facebook_id, instagram,
                twitter, fsq_category_ids, fsq_category_labels, placemaker_url,
                unresolved_flags, false, false, {filename_expression}, ?,
                current_timestamp
            FROM read_parquet(?, filename=true)
            WHERE upper(country) = ?
              AND email IS NOT NULL
              AND trim(email) <> ''
              AND (website IS NULL OR trim(website) = '')
            """,
            [release, urls, country],
        )
        inserted = con.execute("SELECT count(*) FROM contact_places").fetchone()[0] - before

        con.execute(
            f"""
            UPDATE contact_places p
            SET has_noncommercial_category = EXISTS (
                    SELECT 1
                    FROM unnest(coalesce(p.fsq_category_ids, [])) AS ids(category_id)
                    JOIN noncommercial_categories n USING (category_id)
                ),
                has_disqualifying_flag = EXISTS (
                    SELECT 1
                    FROM unnest(coalesce(p.unresolved_flags, [])) AS f(flag)
                    WHERE lower(flag) IN ({flags})
                )
            WHERE list_contains(?, p.source_file)
            """,
            [basenames],
        )

        con.execute(
            f"""
            INSERT OR REPLACE INTO lead_emails
            WITH normalized AS (
                SELECT
                    fsq_place_id,
                    email,
                    lower(trim(regexp_replace(email, '(?i)^mailto:', ''))) AS n
                FROM contact_places
                WHERE list_contains(?, source_file)
            ), assessed AS (
                SELECT
                    fsq_place_id, email, n,
                    split_part(n, '@', 1) AS local_part,
                    split_part(n, '@', 2) AS domain,
                    regexp_full_match(n, ?)
                        AND length(n) <= 254
                        AND length(split_part(n, '@', 1)) <= 64 AS syntax_valid
                FROM normalized
            )
            SELECT
                fsq_place_id,
                email,
                n,
                domain,
                syntax_valid,
                local_part IN ({placeholders}) OR domain IN ({placeholder_domains}),
                local_part IN ({roles}),
                syntax_valid
                    AND NOT (local_part IN ({placeholders}) OR domain IN ({placeholder_domains}))
            FROM assessed
            """,
            [basenames, EMAIL_REGEX],
        )

        elapsed = time.monotonic() - started
        con.executemany(
            """
            UPDATE processed_files
            SET status='completed', completed_at=current_timestamp,
                elapsed_seconds=?, error=NULL,
                rows_inserted=(SELECT count(*) FROM contact_places p
                               WHERE p.source_file=regexp_extract(?, 'places_[0-9]+\\.parquet'))
            WHERE source_file=?
            """,
            [(elapsed, path, path) for path in paths],
        )
        con.execute("COMMIT")
        return inserted, elapsed
    except BaseException:
        con.execute("ROLLBACK")
        raise


def counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    row = con.execute("SELECT * FROM database_summary").fetchone()
    columns = [item[0] for item in con.description]
    return dict(zip(columns, row, strict=True))


def finalize_overture_dedupe(
    con: duckdb.DuckDBPyConnection, overture_database: Path
) -> None:
    if not overture_database.exists():
        raise FileNotFoundError(f"Overture database not found: {overture_database}")
    escaped = str(overture_database.resolve()).replace("'", "''")
    attached = {row[0] for row in con.execute("PRAGMA database_list").fetchall()}
    if "overture" not in attached:
        con.execute(f"ATTACH '{escaped}' AS overture (READ_ONLY)")
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE fsq_match_keys AS
        SELECT
            q.fsq_place_id,
            q.normalized_email,
            regexp_replace(lower(coalesce(q.name, '')), '[^a-z0-9]', '', 'g') AS norm_name,
            left(regexp_replace(coalesce(q.postcode, ''), '[^0-9]', '', 'g'), 5) AS norm_postcode,
            right(regexp_replace(coalesce(q.tel, ''), '[^0-9]', '', 'g'), 10) AS norm_phone
        FROM qualified_leads q;

        CREATE OR REPLACE TEMP TABLE overture_match_keys AS
        SELECT
            p.id AS overture_place_id,
            lower(trim(e.email)) AS normalized_email,
            regexp_replace(lower(coalesce(p.business_name, '')), '[^a-z0-9]', '', 'g') AS norm_name,
            left(regexp_replace(coalesce(p.postcode, ''), '[^0-9]', '', 'g'), 5) AS norm_postcode
        FROM overture.contact_places p
        JOIN overture.lead_emails e ON e.place_id = p.id AND e.is_syntax_valid;

        CREATE OR REPLACE TEMP TABLE overture_phone_keys AS
        SELECT DISTINCT
            p.id AS overture_place_id,
            right(regexp_replace(phone, '[^0-9]', '', 'g'), 10) AS norm_phone
        FROM overture.contact_places p,
             unnest(coalesce(p.phones, [])) AS phones(phone)
        WHERE length(regexp_replace(phone, '[^0-9]', '', 'g')) >= 10;

        CREATE OR REPLACE TABLE overture_matches AS
        WITH candidates AS (
            SELECT DISTINCT
                f.fsq_place_id, o.overture_place_id,
                true AS email_match, false AS phone_match,
                true AS name_match,
                f.norm_postcode <> '' AND f.norm_postcode = o.norm_postcode AS postcode_match
            FROM fsq_match_keys f
            JOIN overture_match_keys o
              ON f.normalized_email = o.normalized_email
             AND f.norm_name = o.norm_name
            WHERE length(f.norm_name) >= 4

            UNION ALL

            SELECT DISTINCT
                f.fsq_place_id, o.overture_place_id,
                false, true, false, false
            FROM fsq_match_keys f
            JOIN overture_phone_keys o USING (norm_phone)
            WHERE length(f.norm_phone) = 10

            UNION ALL

            SELECT DISTINCT
                f.fsq_place_id, o.overture_place_id,
                false, false, true, true
            FROM fsq_match_keys f
            JOIN overture_match_keys o
              ON f.norm_name = o.norm_name
             AND f.norm_postcode = o.norm_postcode
            WHERE length(f.norm_name) >= 4
              AND length(f.norm_postcode) = 5
        )
        SELECT
            fsq_place_id,
            overture_place_id,
            bool_or(email_match) AS email_match,
            bool_or(phone_match) AS phone_match,
            bool_or(name_match) AS name_match,
            bool_or(postcode_match) AS postcode_match,
            bool_or(phone_match OR (name_match AND postcode_match)
                    OR (email_match AND name_match)) AS is_high_confidence_duplicate
        FROM candidates
        GROUP BY fsq_place_id, overture_place_id;

        CREATE OR REPLACE VIEW best_overture_match AS
        SELECT * EXCLUDE (match_rank)
        FROM (
            SELECT *, row_number() OVER (
                PARTITION BY fsq_place_id
                ORDER BY is_high_confidence_duplicate DESC, phone_match DESC,
                         name_match DESC, postcode_match DESC, email_match DESC,
                         overture_place_id
            ) AS match_rank
            FROM overture_matches
        )
        WHERE match_rank = 1;

        CREATE OR REPLACE VIEW foursquare_unique_vs_overture AS
        SELECT q.*
        FROM qualified_leads q
        LEFT JOIN best_overture_match m USING (fsq_place_id)
        WHERE coalesce(m.is_high_confidence_duplicate, false) = false;
        """
    )


def export_results(con: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    exports = {
        "qualified_leads.parquet": "SELECT * FROM qualified_leads",
        "foursquare_unique_vs_overture.parquet": (
            "SELECT * FROM foursquare_unique_vs_overture"
            if con.execute(
                "SELECT count(*) FROM information_schema.views WHERE table_name='foursquare_unique_vs_overture'"
            ).fetchone()[0]
            else "SELECT * FROM qualified_leads"
        ),
    }
    for filename, query in exports.items():
        target = str((output_dir / filename).resolve()).replace("'", "''")
        con.execute(
            f"COPY ({query}) TO '{target}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )


def main() -> int:
    args = parse_args()
    progress_path = args.progress_file.resolve()
    if args.status:
        return show_status(progress_path)
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    if args.max_files is not None and args.max_files < 1:
        raise ValueError("--max-files must be at least 1")

    api = HfApi()
    release = discover_release(api, args.release)
    country = normalized_country(args.country)
    places, categories = list_manifest(api, release)
    database = args.database.resolve()
    con = configure_connection(database)
    initialize_schema(con, release, country)
    insert_manifest(con, places, categories)

    if args.finalize_only:
        if not args.skip_overture_dedupe:
            finalize_overture_dedupe(con, args.overture_database.resolve())
        export_results(con, SCRIPT_DIR / "exports")
        summary = counts(con)
        match_count = con.execute(
            "SELECT count(*) FROM overture_matches"
        ).fetchone()[0] if not args.skip_overture_dedupe else 0
        unique_count = con.execute(
            "SELECT count(*) FROM foursquare_unique_vs_overture"
        ).fetchone()[0] if not args.skip_overture_dedupe else summary["qualified_leads"]
        progress = {
            "status": "complete",
            "database": str(database),
            "release": release,
            "country": country,
            "total_place_files": len(places),
            "total_place_bytes": sum(size for _, size in places),
            "overture_match_pairs": match_count,
            "unique_vs_overture": unique_count,
            "updated_at": utc_now(),
            "finished_at": utc_now(),
            **summary,
        }
        write_progress(progress_path, progress)
        print(json.dumps(progress, indent=2))
        con.close()
        return 0

    token = resolved_token()
    if not token:
        progress = {
            "status": "blocked_auth",
            "message": (
                "Log in to Hugging Face, accept access at "
                "https://huggingface.co/datasets/foursquare/fsq-os-places, "
                "then set HF_TOKEN to a read token and rerun."
            ),
            "database": str(database),
            "release": release,
            "country": country,
            "total_place_files": len(places),
            "total_place_bytes": sum(size for _, size in places),
            "updated_at": utc_now(),
            **counts(con),
        }
        write_progress(progress_path, progress)
        print(json.dumps(progress, indent=2))
        con.close()
        return 2

    # Fail fast before starting a long run.
    signed_download_url(places[0][0], token)
    import_categories(con, categories, token)

    completed = {
        row[0]
        for row in con.execute(
            "SELECT source_file FROM processed_files WHERE status='completed'"
        ).fetchall()
    }
    pending = [item for item in places if item[0] not in completed]
    if args.max_files is not None:
        pending = pending[: args.max_files]
    batches = [pending[i : i + args.batch_size] for i in range(0, len(pending), args.batch_size)]

    progress = {
        "status": "running",
        "database": str(database),
        "release": release,
        "country": country,
        "total_place_files": len(places),
        "total_place_bytes": sum(size for _, size in places),
        "selected_files_this_run": len(pending),
        "batch_size": args.batch_size,
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

    try:
        for index, batch in enumerate(batches, start=1):
            names = [path.rsplit("/", 1)[-1] for path, _ in batch]
            progress.update(
                status="running",
                current_batch=index,
                total_batches=len(batches),
                current_files=names,
                updated_at=utc_now(),
            )
            write_progress(progress_path, progress)
            print(f"[batch {index}/{len(batches)}] {', '.join(names)}", flush=True)
            try:
                inserted, elapsed = ingest_batch(con, batch, release, country, token)
            except Exception as exc:
                con.executemany(
                    """
                    INSERT OR REPLACE INTO processed_files
                    VALUES (?, 'failed', 0, current_timestamp, current_timestamp, NULL, ?)
                    """,
                    [(path, str(exc)) for path, _ in batch],
                )
                progress.update(status="failed", error=str(exc), updated_at=utc_now())
                write_progress(progress_path, progress)
                raise
            progress.update(
                last_batch_rows=inserted,
                last_batch_seconds=round(elapsed, 1),
                updated_at=utc_now(),
                **counts(con),
            )
            write_progress(progress_path, progress)
            print(f"  committed {inserted:,} candidates in {elapsed:.1f}s", flush=True)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        finished_all = counts(con)["completed_files"] == len(places)
        if finished_all and not interrupted:
            if not args.skip_overture_dedupe:
                finalize_overture_dedupe(con, args.overture_database.resolve())
            export_results(con, SCRIPT_DIR / "exports")
        progress.update(
            status="complete" if finished_all else ("stopped" if interrupted else "paused"),
            current_files=None,
            updated_at=utc_now(),
            finished_at=utc_now(),
            **counts(con),
        )
        write_progress(progress_path, progress)
        con.close()

    print(json.dumps(progress, indent=2))
    return 130 if interrupted else 0


if __name__ == "__main__":
    raise SystemExit(main())
