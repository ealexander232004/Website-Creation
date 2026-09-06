"""Run one prepared search campaign and its email-enrichment queue."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

from config import ScraperConfig
from database import Database
from scraper import ScraperOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id", type=int, required=True)
    parser.add_argument(
        "--mode",
        choices=("rpc", "browser"),
        default="browser",
        help="Search transport: direct proxied JSON payloads or Playwright browser",
    )
    parser.add_argument("--search-workers", type=int, default=10)
    parser.add_argument("--email-workers", type=int, default=10)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"campaign_{args.campaign_id}.log"
    pid_path = logs_dir / f"campaign_{args.campaign_id}.pid"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )
    logger = logging.getLogger("gmaps_scraper.campaign")
    pid_path.write_text(str(os.getpid()), encoding="utf-8")

    config = ScraperConfig(
        mode=args.mode,
        workers=args.search_workers,
        email_extraction_enabled=True,
        email_workers=args.email_workers,
        headless=True,
        max_results_per_query=20,
        detail_extraction=False,
        scroll_delay_min=0.8,
        scroll_delay_max=1.5,
    )
    db = Database(config.database_url)
    logger.info(
        "Starting integrated campaign #%d in %s mode with %d search workers and %d email workers.",
        args.campaign_id,
        args.mode,
        args.search_workers,
        args.email_workers,
    )
    try:
        asyncio.run(ScraperOrchestrator(config, campaign_id=args.campaign_id).run())
        logger.info("Integrated campaign #%d completed.", args.campaign_id)
    except Exception:
        db.finish_campaign(args.campaign_id, status="failed")
        logger.exception("Integrated campaign #%d stopped with a fatal error.", args.campaign_id)
        raise


if __name__ == "__main__":
    main()
