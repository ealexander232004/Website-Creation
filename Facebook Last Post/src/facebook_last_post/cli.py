"""Command-line interface for migration, queueing, probing, and enrichment."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .config import DatabaseConfig
from .database import FacebookActivityStore
from .extractor import FacebookPublicDocumentClient
from .models import FetchResult, FetchStatus
from .proxy import load_proxy_urls, proxy_label, validate_proxy_url
from .runner import run_queue


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _print_json(value: Any) -> None:
    print(json.dumps(value, default=_json_default, sort_keys=True))


def _load_environment(paths: list[str]) -> None:
    if paths:
        for path in paths:
            load_dotenv(Path(path), override=False)
    else:
        load_dotenv(override=False)


def _resolve_proxy(args: argparse.Namespace) -> tuple[str, str]:
    if getattr(args, "proxy_url", None):
        value = validate_proxy_url(args.proxy_url)
        return value, proxy_label(value)
    if getattr(args, "proxy_file", None):
        values = load_proxy_urls(args.proxy_file)
        index = args.proxy_index
        if index < 1 or index > len(values):
            raise ValueError(f"proxy index {index} is outside 1..{len(values)}")
        value = values[index - 1]
        return value, proxy_label(value, index)
    environment_value = os.getenv("FACEBOOK_PROXY_URL")
    if environment_value:
        value = validate_proxy_url(environment_value)
        return value, proxy_label(value)
    raise ValueError(
        "a proxy is required: pass --proxy-file/--proxy-index, --proxy-url, "
        "or set FACEBOOK_PROXY_URL; direct fallback is disabled"
    )


def _add_proxy_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--proxy-file", help="File containing one authenticated proxy URL per line")
    group.add_argument("--proxy-url", help="One fixed proxy URL (prefer FACEBOOK_PROXY_URL to hide credentials)")
    parser.add_argument("--proxy-index", type=int, default=1, help="One-based route in --proxy-file")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="facebook-last-post",
        description="Enrich warehouse Facebook business profiles from anonymous public documents.",
    )
    parser.add_argument(
        "--env-file",
        action="append",
        default=[],
        help="Private dotenv file to load; may be repeated and must precede the subcommand",
    )
    parser.add_argument("--database", help="Override the target Postgres database name")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("migrate", help="Create the durable queue/result schema")

    enqueue = subparsers.add_parser("enqueue", help="Queue Facebook profiles from warehouse.entity_socials")
    enqueue.add_argument("--source-schema", default="warehouse")
    enqueue.add_argument("--source-table", default="entity_socials")
    enqueue.add_argument("--batch-size", type=int, default=2_000)
    enqueue.add_argument("--limit", type=int)

    stats = subparsers.add_parser("stats", help="Show durable queue counts by state")
    stats.set_defaults(command="stats")

    probe = subparsers.add_parser("probe", help="Fetch one public account through one fixed proxy")
    probe.add_argument("--url", default="https://www.facebook.com/Meta/")
    probe.add_argument("--timeout-seconds", type=float, default=35.0)
    probe.add_argument("--max-document-bytes", type=int, default=5_000_000)
    _add_proxy_arguments(probe)

    run = subparsers.add_parser("run", help="Process queued accounts through one fixed proxy route")
    run.add_argument("--workers", type=int, default=1, choices=range(1, 5))
    run.add_argument("--max-jobs", type=int, help="Bound this run; omit to drain the ready queue")
    run.add_argument("--max-attempts", type=int, default=3)
    run.add_argument("--max-consecutive-no-data", type=int, default=20)
    run.add_argument("--timeout-seconds", type=float, default=35.0)
    run.add_argument("--delay-seconds", type=float, default=5.0)
    run.add_argument("--max-document-bytes", type=int, default=5_000_000)
    _add_proxy_arguments(run)

    return parser


def _store(args: argparse.Namespace) -> FacebookActivityStore:
    config = DatabaseConfig.from_environment(database=args.database)
    return FacebookActivityStore(config.conninfo)


def _result_dict(result: FetchResult) -> dict[str, Any]:
    value = asdict(result)
    value["status"] = result.status.value
    return value


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _load_environment(args.env_file)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        if args.command == "migrate":
            _store(args).migrate()
            _print_json({"status": "ok", "migration": "001_facebook_activity"})
            return 0

        if args.command == "enqueue":
            summary = _store(args).enqueue_from_socials(
                source_schema=args.source_schema,
                source_table=args.source_table,
                batch_size=args.batch_size,
                limit=args.limit,
            )
            _print_json(asdict(summary))
            return 0

        if args.command == "stats":
            _print_json(_store(args).stats())
            return 0

        if args.command == "probe":
            proxy_url, route_name = _resolve_proxy(args)
            with FacebookPublicDocumentClient(
                proxy_url=proxy_url,
                route_name=route_name,
                timeout_seconds=args.timeout_seconds,
                min_interval_seconds=0,
                max_document_bytes=args.max_document_bytes,
            ) as client:
                result = client.fetch(args.url)
            _print_json(_result_dict(result))
            successful_probe_states = {
                FetchStatus.OK,
                FetchStatus.NO_POST_TIMESTAMP,
                FetchStatus.NOT_FOUND,
                FetchStatus.UNAVAILABLE,
            }
            return 0 if result.status in successful_probe_states else 3

        if args.command == "run":
            proxy_url, route_name = _resolve_proxy(args)
            summary = run_queue(
                store=_store(args),
                proxy_url=proxy_url,
                route_label=route_name,
                workers=args.workers,
                max_jobs=args.max_jobs,
                max_attempts=args.max_attempts,
                max_consecutive_no_data=args.max_consecutive_no_data,
                timeout_seconds=args.timeout_seconds,
                delay_seconds=args.delay_seconds,
                max_document_bytes=args.max_document_bytes,
            )
            _print_json(asdict(summary))
            return 3 if summary.halted_reason else 0
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
