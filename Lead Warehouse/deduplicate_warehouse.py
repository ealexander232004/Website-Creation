from __future__ import annotations

import argparse
import json
from pathlib import Path

import psycopg

from import_fmcsa import (
    DEFAULT_DATABASE,
    DEFAULT_ENV,
    connection_info,
    read_env,
    run_sql_file,
)


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge strong cross-source duplicate entities to a fixed point."
    )
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--max-passes", type=int, default=3)
    return parser.parse_args()


def scalar(connection: psycopg.Connection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])


def main() -> int:
    args = parse_args()
    if args.max_passes < 1:
        raise ValueError("--max-passes must be at least 1")

    env_path = args.env_file.resolve()
    if not env_path.exists():
        raise FileNotFoundError(env_path)
    env = read_env(env_path)

    with psycopg.connect(**connection_info(env, args.database)) as connection:
        connection.execute("set statement_timeout = 0")
        entities_before = scalar(connection, "select count(*) from warehouse.entities")
        log_before = scalar(
            connection,
            "select count(*) from warehouse.entity_merge_log"
            if connection.execute("select to_regclass('warehouse.entity_merge_log')").fetchone()[0]
            else "select 0",
        )

        passes: list[dict[str, int]] = []
        for pass_number in range(1, args.max_passes + 1):
            pass_log_before = scalar(
                connection,
                "select count(*) from warehouse.entity_merge_log"
                if connection.execute("select to_regclass('warehouse.entity_merge_log')").fetchone()[0]
                else "select 0",
            )
            run_sql_file(
                connection,
                SCRIPT_DIR / "postgres" / "006_deduplicate_canonical.sql",
            )
            pass_log_after = scalar(
                connection, "select count(*) from warehouse.entity_merge_log"
            )
            merged = pass_log_after - pass_log_before
            passes.append({"pass": pass_number, "merged_entities": merged})
            print(f"Dedup pass {pass_number}: merged {merged:,} entities", flush=True)
            if merged == 0:
                break

        entities_after = scalar(connection, "select count(*) from warehouse.entities")
        log_after = scalar(connection, "select count(*) from warehouse.entity_merge_log")
        checks = {
            "orphan_source_places": scalar(
                connection,
                """
                select count(*)
                from warehouse.source_places source_place
                left join warehouse.entities entity using (entity_id)
                where entity.entity_id is null
                """,
            ),
            "duplicate_source_keys": scalar(
                connection,
                """
                select count(*) from (
                    select source, source_place_id
                    from warehouse.source_places
                    group by source, source_place_id
                    having count(*) > 1
                ) duplicate
                """,
            ),
            "source_count_mismatches": scalar(
                connection,
                """
                select count(*)
                from warehouse.entities entity
                join (
                    select entity_id, count(*)::smallint as actual_source_count
                    from warehouse.source_places
                    group by entity_id
                ) source_count using (entity_id)
                where entity.source_count <> source_count.actual_source_count
                """,
            ),
        }
        if any(checks.values()):
            raise RuntimeError(f"Post-dedup validation failed: {checks}")

        result = {
            "database": args.database,
            "entities_before": entities_before,
            "entities_after": entities_after,
            "merged_this_run": log_after - log_before,
            "passes": passes,
            "checks": checks,
        }
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
