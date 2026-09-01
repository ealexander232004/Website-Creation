from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import UTC, date, datetime
from pathlib import Path

import psycopg


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
DEFAULT_CSV = (
    WORKSPACE
    / "FMCSA"
    / "SMS_Input_-_Motor_Carrier_Census_Information_20260901.csv"
)
DEFAULT_ENV = WORKSPACE / "Google Maps Scraping" / ".env"
DEFAULT_PROGRESS = SCRIPT_DIR / "fmcsa_import.progress.json"
DEFAULT_DATABASE = "lead_warehouse"

CSV_COLUMNS = [
    "dot_number",
    "legal_name",
    "dba_name",
    "carrier_operation",
    "hm_flag",
    "pc_flag",
    "phy_street",
    "phy_city",
    "phy_state",
    "phy_zip",
    "phy_country",
    "mailing_street",
    "mailing_city",
    "mailing_state",
    "mailing_zip",
    "mailing_country",
    "telephone",
    "fax",
    "email_address",
    "mcs150_date",
    "mcs150_mileage",
    "mcs150_mileage_year",
    "add_date",
    "oic_state",
    "nbr_power_unit",
    "driver_total",
    "recent_mileage",
    "recent_mileage_year",
    "vmt_source_id",
    "private_only",
    "authorized_for_hire",
    "exempt_for_hire",
    "private_property",
    "private_passenger_business",
    "private_passenger_nonbusiness",
    "migrant",
    "us_mail",
    "federal_government",
    "state_government",
    "local_government",
    "indian_tribe",
    "op_other",
]

BOOLEAN_COLUMNS = {
    "hm_flag",
    "pc_flag",
    "private_only",
    "authorized_for_hire",
    "exempt_for_hire",
    "private_property",
    "private_passenger_business",
    "private_passenger_nonbusiness",
    "migrant",
    "us_mail",
    "federal_government",
    "state_government",
    "local_government",
    "indian_tribe",
}

INTEGER_TYPES = {
    "dot_number": "bigint",
    "mcs150_mileage": "bigint",
    "mcs150_mileage_year": "smallint",
    "nbr_power_unit": "integer",
    "driver_total": "integer",
    "recent_mileage": "bigint",
    "recent_mileage_year": "smallint",
    "vmt_source_id": "smallint",
}

DATE_COLUMNS = {"mcs150_date", "add_date"}


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a filtered FMCSA SMS census CSV into the lead warehouse."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--force", action="store_true")
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
    temporary = DEFAULT_PROGRESS.with_suffix(DEFAULT_PROGRESS.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, DEFAULT_PROGRESS)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_header(path: Path) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        header = next(csv.reader(source))
    normalized = [column.strip().lower() for column in header]
    if normalized != CSV_COLUMNS:
        raise ValueError(
            "Unexpected FMCSA CSV header. "
            f"Expected {CSV_COLUMNS!r}, received {normalized!r}."
        )


def snapshot_date_from_name(path: Path) -> date:
    match = re.search(r"(20\d{6})", path.stem)
    if not match:
        raise ValueError(f"No YYYYMMDD snapshot date found in {path.name}")
    return datetime.strptime(match.group(1), "%Y%m%d").date()


def run_sql_file(connection: psycopg.Connection, path: Path) -> None:
    connection.execute(path.read_text(encoding="utf-8"))
    connection.commit()


def create_stage(connection: psycopg.Connection) -> None:
    columns = ",\n".join(f"    {column} text" for column in CSV_COLUMNS)
    connection.execute("drop table if exists raw_fmcsa.carriers_stage")
    connection.execute(
        f"create unlogged table raw_fmcsa.carriers_stage (\n{columns}\n)"
    )
    connection.commit()


def copy_csv(connection: psycopg.Connection, path: Path) -> None:
    column_list = ", ".join(CSV_COLUMNS)
    copy_sql = (
        f"copy raw_fmcsa.carriers_stage ({column_list}) "
        "from stdin with (format csv, header true, encoding 'UTF8')"
    )
    started = time.monotonic()
    with path.open("rb") as source, connection.cursor() as cursor:
        with cursor.copy(copy_sql) as copy:
            while chunk := source.read(8 * 1024 * 1024):
                copy.write(chunk)
    connection.commit()
    print(f"Staged CSV in {time.monotonic() - started:.1f}s", flush=True)


def validate_stage(connection: psycopg.Connection) -> dict[str, int]:
    row = connection.execute(
        """
        select
            count(*)::bigint as row_count,
            count(distinct dot_number)::bigint as distinct_dot_numbers,
            count(*) filter (
                where dot_number is null or dot_number !~ '^[0-9]+$'
            )::bigint as invalid_dot_numbers,
            count(*) filter (
                where email_address is null or btrim(email_address) = ''
            )::bigint as blank_emails,
            count(*) filter (
                where nbr_power_unit !~ '^[0-9]+$'
                   or driver_total !~ '^[0-9]+$'
            )::bigint as invalid_size_values,
            count(*) filter (
                where phy_country <> 'US'
                   or nbr_power_unit not in ('1','2','3','4','5','6','7','8','9','10')
                   or driver_total not in (
                       '1','2','3','4','5','6','7','8','9','10',
                       '11','12','13','14','15','16','17','18','19','20'
                   )
                   or federal_government <> 'false'
                   or state_government <> 'false'
                   or local_government <> 'false'
                   or private_passenger_nonbusiness <> 'false'
                   or not (
                       authorized_for_hire = 'true'
                       or exempt_for_hire = 'true'
                       or private_property = 'true'
                       or private_passenger_business = 'true'
                   )
                   or position('@' in email_address) = 0
            )::bigint as filter_violations
        from raw_fmcsa.carriers_stage
        """
    ).fetchone()
    result = {
        "row_count": int(row[0]),
        "distinct_dot_numbers": int(row[1]),
        "invalid_dot_numbers": int(row[2]),
        "blank_emails": int(row[3]),
        "invalid_size_values": int(row[4]),
        "filter_violations": int(row[5]),
    }
    if result["row_count"] != result["distinct_dot_numbers"]:
        raise ValueError(f"Duplicate DOT numbers found: {result}")
    for key in (
        "invalid_dot_numbers",
        "blank_emails",
        "invalid_size_values",
        "filter_violations",
    ):
        if result[key] != 0:
            raise ValueError(f"FMCSA staging validation failed: {result}")
    return result


def select_expression(column: str) -> str:
    if column in INTEGER_TYPES:
        return f"nullif(btrim({column}), '')::{INTEGER_TYPES[column]}"
    if column in BOOLEAN_COLUMNS:
        return f"nullif(btrim({column}), '')::boolean"
    if column in DATE_COLUMNS:
        return f"to_date(nullif(btrim({column}), ''), 'DD-MON-YY')"
    return f"nullif(btrim({column}), '')"


def upsert_raw(
    connection: psycopg.Connection,
    snapshot_date: date,
    source_file: str,
    source_sha256: str,
) -> None:
    target_columns = CSV_COLUMNS + [
        "snapshot_date",
        "is_current",
        "source_file",
        "source_sha256",
        "ingested_at",
    ]
    select_values = [select_expression(column) for column in CSV_COLUMNS] + [
        "%s::date",
        "true",
        "%s",
        "%s",
        "current_timestamp",
    ]
    update_columns = [column for column in target_columns if column != "dot_number"]
    assignments = ",\n    ".join(
        f"{column} = excluded.{column}" for column in update_columns
    )
    connection.execute(
        "update raw_fmcsa.carriers set is_current = false where is_current"
    )
    query = f"""
        insert into raw_fmcsa.carriers as target (
            {', '.join(target_columns)}
        )
        select
            {', '.join(select_values)}
        from raw_fmcsa.carriers_stage
        on conflict (dot_number) do update
        set {assignments};
    """
    connection.execute(query, (snapshot_date, source_file, source_sha256))
    connection.execute(
        r"""
        insert into raw_fmcsa.emails (
            dot_number,
            email,
            normalized_email,
            email_domain,
            is_syntax_valid,
            is_role_account,
            source_file
        )
        select
            carrier.dot_number,
            carrier.email_address,
            lower(btrim(carrier.email_address)),
            lower(split_part(btrim(carrier.email_address), '@', 2)),
            btrim(carrier.email_address) ~* '^[A-Z0-9.!#$%&''*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$',
            lower(split_part(btrim(carrier.email_address), '@', 1)) ~
                '^(info|sales|office|admin|contact|support|billing|dispatch|operations|hello|service|customerservice)([._+-]|$)',
            carrier.source_file
        from raw_fmcsa.carriers carrier
        where carrier.is_current
        on conflict (dot_number) do update
        set email = excluded.email,
            normalized_email = excluded.normalized_email,
            email_domain = excluded.email_domain,
            is_syntax_valid = excluded.is_syntax_valid,
            is_role_account = excluded.is_role_account,
            source_file = excluded.source_file
        """
    )
    connection.commit()


def import_metrics(connection: psycopg.Connection) -> dict[str, int]:
    row = connection.execute(
        """
        select
            (select count(*) from raw_fmcsa.carriers where is_current),
            (select count(*) from raw_fmcsa.emails email
             join raw_fmcsa.carriers carrier using (dot_number)
             where carrier.is_current and email.is_syntax_valid),
            (select count(*) from warehouse.source_places source_place
             join warehouse.entities entity using (entity_id)
             where source_place.source = 'fmcsa'
               and entity.primary_source <> 'fmcsa'),
            (select count(*) from warehouse.entities
             where primary_source = 'fmcsa')
        """
    ).fetchone()
    return {
        "row_count": int(row[0]),
        "valid_email_count": int(row[1]),
        "matched_existing_entities": int(row[2]),
        "new_entities": int(row[3]),
    }


def raw_snapshot_ready(
    connection: psycopg.Connection, source_sha256: str
) -> tuple[bool, int]:
    row = connection.execute(
        """
        select
            count(*) filter (
                where carrier.is_current and carrier.source_sha256 = %s
            ),
            count(*) filter (where carrier.is_current),
            count(email.dot_number) filter (where carrier.is_current)
        from raw_fmcsa.carriers carrier
        left join raw_fmcsa.emails email using (dot_number)
        """,
        (source_sha256,),
    ).fetchone()
    matching_rows, current_rows, email_rows = map(int, row)
    return (
        matching_rows > 0
        and matching_rows == current_rows
        and matching_rows == email_rows,
        matching_rows,
    )


def main() -> int:
    args = parse_args()
    if args.status:
        if not DEFAULT_PROGRESS.exists():
            print(f"No progress file exists: {DEFAULT_PROGRESS}")
            return 1
        print(DEFAULT_PROGRESS.read_text(encoding="utf-8"))
        return 0

    csv_path = args.csv.resolve()
    env_path = args.env_file.resolve()
    for path in (csv_path, env_path):
        if not path.exists():
            raise FileNotFoundError(path)

    validate_header(csv_path)
    snapshot_date = snapshot_date_from_name(csv_path)
    source_sha256 = sha256_file(csv_path)
    env = read_env(env_path)
    progress = {
        "status": "starting",
        "database": args.database,
        "source_file": str(csv_path),
        "source_sha256": source_sha256,
        "snapshot_date": snapshot_date.isoformat(),
        "started_at": utc_now(),
        "updated_at": utc_now(),
    }
    write_progress(progress)

    run_id: int | None = None
    with psycopg.connect(**connection_info(env, args.database)) as connection:
        connection.execute("set statement_timeout = 0")
        run_sql_file(connection, SCRIPT_DIR / "postgres" / "004_fmcsa_schema.sql")

        existing = connection.execute(
            """
            select run_id, row_count, valid_email_count,
                   matched_existing_entities, new_entities, finished_at
            from raw_fmcsa.import_runs
            where source_sha256 = %s and status = 'completed'
            order by run_id desc limit 1
            """,
            (source_sha256,),
        ).fetchone()
        if existing and not args.force:
            progress.update(
                status="already_imported",
                run_id=existing[0],
                row_count=existing[1],
                valid_email_count=existing[2],
                matched_existing_entities=existing[3],
                new_entities=existing[4],
                finished_at=existing[5].isoformat(),
                updated_at=utc_now(),
            )
            write_progress(progress)
            print(json.dumps(progress, indent=2, default=str))
            return 0

        run_id = connection.execute(
            """
            insert into raw_fmcsa.import_runs (
                source_file, source_sha256, snapshot_date, status
            ) values (%s, %s, %s, 'running')
            returning run_id
            """,
            (csv_path.name, source_sha256, snapshot_date),
        ).fetchone()[0]
        connection.commit()
        progress.update(status="staging", run_id=run_id, updated_at=utc_now())
        write_progress(progress)

        try:
            raw_ready, raw_row_count = raw_snapshot_ready(connection, source_sha256)
            if raw_ready:
                progress.update(
                    status="resuming_from_raw",
                    row_count=raw_row_count,
                    updated_at=utc_now(),
                )
                write_progress(progress)
            else:
                create_stage(connection)
                copy_csv(connection, csv_path)

                stage_checks = validate_stage(connection)
                progress.update(
                    status="loading_raw",
                    stage_checks=stage_checks,
                    updated_at=utc_now(),
                )
                write_progress(progress)
                upsert_raw(connection, snapshot_date, csv_path.name, source_sha256)

            progress.update(status="integrating_canonical", updated_at=utc_now())
            write_progress(progress)
            run_sql_file(connection, SCRIPT_DIR / "postgres" / "005_integrate_fmcsa.sql")

            progress.update(status="deduplicating_canonical", updated_at=utc_now())
            write_progress(progress)
            run_sql_file(connection, SCRIPT_DIR / "postgres" / "006_deduplicate_canonical.sql")

            metrics = import_metrics(connection)
            connection.execute(
                """
                update raw_fmcsa.import_runs
                set status = 'completed',
                    row_count = %s,
                    valid_email_count = %s,
                    matched_existing_entities = %s,
                    new_entities = %s,
                    finished_at = current_timestamp
                where run_id = %s
                """,
                (
                    metrics["row_count"],
                    metrics["valid_email_count"],
                    metrics["matched_existing_entities"],
                    metrics["new_entities"],
                    run_id,
                ),
            )
            connection.execute("drop table if exists raw_fmcsa.carriers_stage")
            connection.commit()

            progress.update(
                status="complete",
                **metrics,
                updated_at=utc_now(),
                finished_at=utc_now(),
            )
            write_progress(progress)
            print(json.dumps(progress, indent=2, default=str))
            return 0
        except Exception as error:
            connection.rollback()
            if run_id is not None:
                connection.execute(
                    """
                    update raw_fmcsa.import_runs
                    set status = 'failed', error = %s, finished_at = current_timestamp
                    where run_id = %s
                    """,
                    (str(error)[:4000], run_id),
                )
                connection.commit()
            progress.update(
                status="failed",
                error=str(error),
                updated_at=utc_now(),
                finished_at=utc_now(),
            )
            write_progress(progress)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
