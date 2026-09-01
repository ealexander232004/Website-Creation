"""Keep launching fresh integrated campaigns until the email-lead goal is met.

The supervisor runs one campaign at a time, keeps the proven Maps/email worker
allocation, gives terminal proxy failures one recovery pass, and persists its
state so an interrupted run can resume without creating duplicate work.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from config import DEFAULT_CONFIG
from database import Database
from prepare_integrated_campaign import prepare


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
STATE_PATH = LOG_DIR / "overnight_supervisor.state.json"
SUPERVISOR_LOG = LOG_DIR / "overnight_supervisor.log"


def _configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(SUPERVISOR_LOG, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )
    return logging.getLogger("gmaps_scraper.overnight")


def _load_state() -> dict[str, Any] | None:
    if not STATE_PATH.is_file():
        return None
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or "campaign_id" not in state or "round_index" not in state:
            raise RuntimeError(f"Invalid supervisor state in {STATE_PATH}")
        return state
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read supervisor state {STATE_PATH}: {exc}") from exc


def _save_state(state: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = STATE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(STATE_PATH)


def _pid_is_alive(campaign_id: int) -> bool:
    pid_path = LOG_DIR / f"campaign_{campaign_id}.pid"
    if not pid_path.is_file():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except PermissionError:
            return True
        return True
    except (OSError, ValueError):
        return False


def _launch_runner(campaign_id: int, search_workers: int, email_workers: int, logger: logging.Logger):
    if _pid_is_alive(campaign_id):
        logger.info("Campaign #%d runner is already alive; not starting a duplicate.", campaign_id)
        return None
    command = [
        sys.executable,
        str(BASE_DIR / "run_integrated_campaign.py"),
        "--campaign-id",
        str(campaign_id),
        "--mode",
        "rpc",
        "--search-workers",
        str(search_workers),
        "--email-workers",
        str(email_workers),
    ]
    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    process = subprocess.Popen(
        command,
        cwd=BASE_DIR,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=os.name != "nt",
    )
    logger.info(
        "Started campaign #%d runner with %d Maps workers and %d email workers.",
        campaign_id,
        search_workers,
        email_workers,
    )
    return process


def _requeue_terminal_failures(db: Database, campaign_id: int) -> tuple[int, int]:
    with db._get_connection() as conn:
        with conn.transaction():
            conn.execute("SET LOCAL lock_timeout = '10s'")
            search_rows = conn.execute(
                """
                UPDATE search_queue
                SET status = 'pending', attempts = 0, error_message = NULL, completed_at = NULL
                WHERE campaign_id = %s AND status = 'failed' AND attempts >= 3
                RETURNING id
                """,
                (campaign_id,),
            ).fetchall()
            email_rows = conn.execute(
                """
                UPDATE email_queue
                SET status = 'pending', attempts = 0, error_message = NULL,
                    started_at = NULL, completed_at = NULL
                WHERE campaign_id = %s AND status = 'failed' AND attempts >= 3
                RETURNING id
                """,
                (campaign_id,),
            ).fetchall()
            if search_rows or email_rows:
                conn.execute(
                    "UPDATE campaigns SET status = 'running', completed_at = NULL WHERE id = %s",
                    (campaign_id,),
                )
    return len(search_rows), len(email_rows)


def _valid_email_businesses(db: Database) -> int:
    with db._get_connection() as conn:
        row = conn.execute(
            """
            SELECT count(DISTINCT le.place_id) AS businesses
            FROM lead_emails AS le
            JOIN leads AS l ON l.place_id = le.place_id
            WHERE NOT l.has_website
            """
        ).fetchone()
    return int(row["businesses"])


def _campaign_stats(db: Database, campaign_id: int) -> dict[str, Any]:
    return db.get_campaign_stats(campaign_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id", type=int, required=True, help="Campaign to monitor first")
    parser.add_argument("--round", dest="round_index", type=int, required=True,
                        help="Round index for the next campaign if the starting campaign is terminal")
    parser.add_argument("--jobs-per-campaign", type=int, default=20_000)
    parser.add_argument("--target-businesses", type=int, default=100_000)
    parser.add_argument("--search-workers", type=int, default=6)
    parser.add_argument("--email-workers", type=int, default=26)
    parser.add_argument("--poll-seconds", type=float, default=30.0)
    args = parser.parse_args()
    if args.round_index < 0 or args.jobs_per_campaign < 1 or args.target_businesses < 1:
        parser.error("round must be >= 0 and job/target counts must be positive")

    logger = _configure_logging()
    db = Database(DEFAULT_CONFIG.database_url, initialize_schema=False)
    state = _load_state()
    if state is None:
        state = {"campaign_id": args.campaign_id, "round_index": args.round_index - 1, "retry_done": False}
        _save_state(state)
    else:
        logger.info("Resuming state: %s", state)

    last_logged = None
    runner_process = None
    while True:
        campaign_id = int(state["campaign_id"])
        stats = _campaign_stats(db, campaign_id)
        status = stats["status"]
        progress = (
            status,
            stats["search_completed"],
            stats["search_pending"],
            stats["search_in_progress"],
            stats["search_failed"],
            stats["email_completed"],
            stats["email_no_email"],
            stats["email_pending"],
            stats["email_in_progress"],
            stats["email_failed"],
        )
        if progress != last_logged:
            logger.info(
                "Campaign #%d [%s]: Maps %d/%d done (%d pending, %d running, %d failed); "
                "email %d done + %d no-email (%d pending, %d running, %d failed); "
                "cumulative businesses with fetched emails=%d.",
                campaign_id,
                status,
                stats["search_completed"],
                stats["search_total"],
                stats["search_pending"],
                stats["search_in_progress"],
                stats["search_failed"],
                stats["email_completed"],
                stats["email_no_email"],
                stats["email_pending"],
                stats["email_in_progress"],
                stats["email_failed"],
                _valid_email_businesses(db),
            )
            last_logged = progress

        if status == "running":
            if runner_process is not None and runner_process.poll() is not None:
                runner_process = None
            if runner_process is None and not _pid_is_alive(campaign_id):
                logger.warning("Campaign #%d is marked running but its runner is absent; resuming it.", campaign_id)
                runner_process = _launch_runner(campaign_id, args.search_workers, args.email_workers, logger)
            time.sleep(max(args.poll_seconds, 5.0))
            continue

        if not bool(state.get("retry_done", False)) and (stats["search_failed"] or stats["email_failed"]):
            search_retry, email_retry = _requeue_terminal_failures(db, campaign_id)
            state["retry_done"] = True
            _save_state(state)
            if search_retry or email_retry:
                logger.warning(
                    "Campaign #%d recovery pass: requeued %d Maps and %d email failures.",
                    campaign_id,
                    search_retry,
                    email_retry,
                )
                runner_process = _launch_runner(campaign_id, args.search_workers, args.email_workers, logger)
                last_logged = None
                continue

        cumulative = _valid_email_businesses(db)
        if cumulative >= args.target_businesses:
            logger.info("Target reached: %d businesses with fetched emails.", cumulative)
            return

        next_round = int(state["round_index"]) + 1
        next_campaign = prepare(
            target_jobs=args.jobs_per_campaign,
            search_workers=args.search_workers,
            email_workers=args.email_workers,
            name=f"nationwide-{args.jobs_per_campaign}-overnight-r{next_round}",
        )
        state = {"campaign_id": next_campaign, "round_index": next_round, "retry_done": False}
        _save_state(state)
        logger.info("Prepared next campaign #%d using coordinate round %d.", next_campaign, next_round)
        runner_process = _launch_runner(next_campaign, args.search_workers, args.email_workers, logger)
        last_logged = None


if __name__ == "__main__":
    main()
