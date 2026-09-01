from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import duckdb
import psycopg
from psycopg import sql


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
DEFAULT_OVERTURE = WORKSPACE / "Overture" / "overture_smb_leads.duckdb"
DEFAULT_FOURSQUARE = WORKSPACE / "Foursquare" / "foursquare_email_no_website.duckdb"
DEFAULT_ENV = WORKSPACE / "Google Maps Scraping" / ".env"
DEFAULT_PROGRESS = SCRIPT_DIR / "lead_warehouse.progress.json"
TARGET_DATABASE = "lead_warehouse"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the unified lead warehouse in PostgreSQL.")
    parser.add_argument("--overture", type=Path, default=DEFAULT_OVERTURE)
    parser.add_argument("--foursquare", type=Path, default=DEFAULT_FOURSQUARE)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--database", default=TARGET_DATABASE)
    parser.add_argument("--status", action="store_true")
    return parser.parse_args()


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def connection_info(env: dict[str, str], database: str) -> dict[str, str | int]:
    return {
        "host": env.get("POSTGRES_HOST", "localhost"),
        "port": int(env.get("POSTGRES_PORT", "5432")),
        "user": env.get("POSTGRES_USER", "gmaps_scraper"),
        "password": env.get("POSTGRES_PASSWORD", "gmaps_scraper"),
        "dbname": database,
    }


def write_progress(payload: dict) -> None:
    temp = DEFAULT_PROGRESS.with_suffix(DEFAULT_PROGRESS.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temp, DEFAULT_PROGRESS)


def ensure_database(env: dict[str, str], database: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", database):
        raise ValueError("Database name must be lowercase snake_case")
    admin_db = env.get("POSTGRES_DB", "gmaps_scraper")
    with psycopg.connect(**connection_info(env, admin_db), autocommit=True) as con:
        exists = con.execute(
            "select 1 from pg_database where datname = %s", (database,)
        ).fetchone()
        if not exists:
            con.execute(sql.SQL("create database {}").format(sql.Identifier(database)))


def run_sql_file(con: psycopg.Connection, path: Path) -> None:
    con.execute(path.read_text(encoding="utf-8"))
    con.commit()


def copy_query(
    pg: psycopg.Connection,
    source: duckdb.DuckDBPyConnection,
    target: str,
    columns: list[str],
    query: str,
    batch_size: int = 10_000,
) -> int:
    started = time.monotonic()
    total = 0
    cursor = source.execute(query)
    copy_sql = sql.SQL("copy {} ({}) from stdin").format(
        sql.SQL(target),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    with pg.cursor() as pg_cursor:
        with pg_cursor.copy(copy_sql) as copy:
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    copy.write_row(row)
                total += len(rows)
                print(f"  {target}: {total:,}", flush=True)
    pg.commit()
    print(f"  {target}: complete in {time.monotonic() - started:.1f}s", flush=True)
    return total


def import_raw(
    pg: psycopg.Connection,
    overture_path: Path,
    foursquare_path: Path,
    progress: dict,
) -> None:
    overture = duckdb.connect(str(overture_path), read_only=True)
    foursquare = duckdb.connect(str(foursquare_path), read_only=True)
    try:
        pg.execute(
            """
            truncate table
                raw_foursquare.overture_matches,
                raw_foursquare.categories,
                raw_foursquare.emails,
                raw_foursquare.places,
                raw_overture.emails,
                raw_overture.places
            cascade
            """
        )
        pg.commit()

        jobs = [
            (
                overture,
                "raw_overture.places",
                [
                    "place_id", "business_name", "primary_category", "basic_category",
                    "industry_group", "taxonomy_hierarchy", "alternate_categories",
                    "emails", "phones", "socials", "websites", "street_address",
                    "city", "region", "postcode", "country", "longitude", "latitude",
                    "brand_name", "is_known_brand", "is_probable_small_business",
                    "confidence", "quality_tier", "operating_status", "all_names",
                    "all_addresses", "brand", "source_records", "overture_release",
                    "source_file", "ingested_at",
                ],
                """
                select id, business_name, primary_category, basic_category,
                       industry_group, taxonomy_hierarchy, alternate_categories,
                       emails, phones, socials, websites, street_address,
                       city, region, postcode, country, longitude, latitude,
                       brand_name, is_known_brand, is_probable_small_business,
                       confidence, quality_tier, operating_status,
                       all_names::varchar, all_addresses::varchar, brand::varchar,
                       source_records::varchar, overture_release, source_file,
                       ingested_at
                from contact_places order by id
                """,
            ),
            (
                overture,
                "raw_overture.emails",
                ["place_id", "email", "email_domain", "is_syntax_valid", "is_role_account", "source_file"],
                "select place_id, email, email_domain, is_syntax_valid, is_role_account, source_file from lead_emails order by place_id, email",
            ),
            (
                foursquare,
                "raw_foursquare.places",
                [
                    "place_id", "name", "latitude", "longitude", "address", "locality",
                    "region", "postcode", "admin_region", "post_town", "po_box",
                    "country", "date_created", "date_refreshed", "date_closed",
                    "telephone", "website", "email", "facebook_id", "instagram",
                    "twitter", "category_ids", "category_labels", "placemaker_url",
                    "unresolved_flags", "has_noncommercial_category",
                    "has_disqualifying_flag", "source_file", "foursquare_release",
                    "ingested_at",
                ],
                """
                select fsq_place_id, name, latitude, longitude, address, locality,
                       region, postcode, admin_region, post_town, po_box, country,
                       date_created, date_refreshed, date_closed, tel, website, email,
                       facebook_id, instagram, twitter, fsq_category_ids,
                       fsq_category_labels, placemaker_url, unresolved_flags,
                       has_noncommercial_category, has_disqualifying_flag,
                       source_file, fsq_release, ingested_at
                from contact_places order by fsq_place_id
                """,
            ),
            (
                foursquare,
                "raw_foursquare.emails",
                [
                    "place_id", "email", "normalized_email", "email_domain",
                    "is_syntax_valid", "is_placeholder", "is_role_account", "is_usable",
                ],
                "select fsq_place_id, email, normalized_email, email_domain, is_syntax_valid, is_placeholder, is_role_account, is_usable from lead_emails order by fsq_place_id",
            ),
            (
                foursquare,
                "raw_foursquare.categories",
                [
                    "category_id", "category_level", "category_name", "category_label",
                    "level1_category_id", "level1_category_name", "level2_category_id",
                    "level2_category_name", "level3_category_id", "level3_category_name",
                    "level4_category_id", "level4_category_name", "level5_category_id",
                    "level5_category_name", "level6_category_id", "level6_category_name",
                ],
                "select * from fsq_categories order by category_id",
            ),
            (
                foursquare,
                "raw_foursquare.overture_matches",
                [
                    "foursquare_place_id", "overture_place_id", "email_match",
                    "phone_match", "name_match", "postcode_match",
                    "is_high_confidence_duplicate",
                ],
                "select fsq_place_id, overture_place_id, email_match, phone_match, name_match, postcode_match, is_high_confidence_duplicate from overture_matches order by fsq_place_id, overture_place_id",
            ),
        ]
        for source, target, columns, query in jobs:
            progress["current_table"] = target
            progress["updated_at"] = utc_now()
            write_progress(progress)
            progress.setdefault("rows", {})[target] = copy_query(
                pg, source, target, columns, query
            )
    finally:
        overture.close()
        foursquare.close()


def validate(pg: psycopg.Connection) -> dict:
    summary_row = pg.execute("select * from warehouse.lead_summary").fetchone()
    summary_columns = [description.name for description in pg.execute("select * from warehouse.lead_summary").description]
    summary = dict(zip(summary_columns, summary_row, strict=True))
    checks = {
        "orphan_source_places": pg.execute(
            """
            select count(*) from warehouse.source_places sp
            left join warehouse.entities e using (entity_id)
            where e.entity_id is null
            """
        ).fetchone()[0],
        "entities_without_email": pg.execute(
            """
            select count(*) from warehouse.qualified_no_website_email_leads q
            where not exists (
                select 1 from warehouse.entity_emails e
                where e.entity_id = q.entity_id and e.is_usable
            )
            """
        ).fetchone()[0],
        "duplicate_source_keys": pg.execute(
            """
            select count(*) from (
                select source, source_place_id
                from warehouse.source_places
                group by source, source_place_id having count(*) > 1
            ) duplicates
            """
        ).fetchone()[0],
        "non_us_qualified": pg.execute(
            "select count(*) from warehouse.qualified_no_website_email_leads where country <> 'US'"
        ).fetchone()[0],
    }
    return {"summary": summary, "checks": checks}


def main() -> int:
    args = parse_args()
    if args.status:
        if not DEFAULT_PROGRESS.exists():
            print(f"No progress file exists: {DEFAULT_PROGRESS}")
            return 1
        print(DEFAULT_PROGRESS.read_text(encoding="utf-8"))
        return 0

    overture_path = args.overture.resolve()
    foursquare_path = args.foursquare.resolve()
    env_path = args.env_file.resolve()
    for path in (overture_path, foursquare_path, env_path):
        if not path.exists():
            raise FileNotFoundError(path)

    env = read_env(env_path)
    progress = {
        "status": "starting",
        "database": args.database,
        "overture": str(overture_path),
        "foursquare": str(foursquare_path),
        "started_at": utc_now(),
        "updated_at": utc_now(),
    }
    write_progress(progress)

    ensure_database(env, args.database)
    with psycopg.connect(**connection_info(env, args.database)) as pg:
        progress.update(status="migrating", updated_at=utc_now())
        write_progress(progress)
        run_sql_file(pg, SCRIPT_DIR / "postgres" / "001_schema.sql")

        progress.update(status="importing_raw", updated_at=utc_now())
        write_progress(progress)
        import_raw(pg, overture_path, foursquare_path, progress)

        progress.update(status="building_canonical", current_table=None, updated_at=utc_now())
        write_progress(progress)
        run_sql_file(pg, SCRIPT_DIR / "postgres" / "002_build_canonical.sql")

        result = validate(pg)
        progress.update(
            status="complete",
            updated_at=utc_now(),
            finished_at=utc_now(),
            **result,
        )
        write_progress(progress)
        print(json.dumps(progress, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
