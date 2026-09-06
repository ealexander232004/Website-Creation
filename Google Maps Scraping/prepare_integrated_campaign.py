"""Create a balanced nationwide search campaign with durable email enrichment."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Iterator

from categories import CATEGORY_PRESETS
from config import DEFAULT_CONFIG
from database import Database
from geo_grid import US_STATE_BOUNDS
from models import SearchJob


SAMPLE_POINTS = (
    (0.18, 0.22),
    (0.32, 0.72),
    (0.48, 0.42),
    (0.64, 0.82),
    (0.78, 0.28),
    (0.24, 0.54),
    (0.55, 0.14),
    (0.84, 0.62),
    (0.40, 0.90),
    (0.70, 0.50),
)


def nationwide_candidates() -> Iterator[SearchJob]:
    """Yields category/state-balanced coordinates in deterministic rounds."""
    keywords = CATEGORY_PRESETS["all_small_business"]
    states = sorted(US_STATE_BOUNDS)
    for lat_fraction, lng_fraction in SAMPLE_POINTS:
        for keyword in keywords:
            for state in states:
                bounds = US_STATE_BOUNDS[state]
                latitude = bounds.min_lat + ((bounds.max_lat - bounds.min_lat) * lat_fraction)
                longitude = bounds.min_lng + ((bounds.max_lng - bounds.min_lng) * lng_fraction)
                latitude = round(latitude, 5)
                longitude = round(longitude, 5)
                yield SearchJob(
                    keyword=keyword,
                    location_name=f"Grid ({latitude:.4f}, {longitude:.4f})",
                    latitude=latitude,
                    longitude=longitude,
                    zoom_level=14,
                    bounding_box=(
                        f"{bounds.min_lat:.4f},{bounds.min_lng:.4f},"
                        f"{bounds.max_lat:.4f},{bounds.max_lng:.4f}"
                    ),
                )


def prepare(target_jobs: int, search_workers: int, email_workers: int, name: str | None) -> int:
    db = Database(DEFAULT_CONFIG.database_url)
    campaign_name = name or f"nationwide-{target_jobs}-integrated-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    campaign_id = db.create_campaign(campaign_name, 0, search_workers, email_workers)

    added = 0
    batch: list[SearchJob] = []
    try:
        for job in nationwide_candidates():
            if added + len(batch) >= target_jobs:
                break
            batch.append(job)
            if len(batch) == 500:
                added += db.enqueue_jobs(batch, campaign_id=campaign_id)
                batch.clear()
        if batch and added < target_jobs:
            added += db.enqueue_jobs(batch[: target_jobs - added], campaign_id=campaign_id)
        if added != target_jobs:
            raise RuntimeError(f"Expected {target_jobs:,} unique jobs, but enqueued {added:,}")
        db.update_campaign_target(campaign_id, added)
    except Exception:
        db.finish_campaign(campaign_id, status="failed")
        raise

    print(campaign_id)
    return campaign_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=20_000)
    parser.add_argument("--search-workers", type=int, default=10)
    parser.add_argument("--email-workers", type=int, default=10)
    parser.add_argument("--name")
    args = parser.parse_args()
    prepare(args.jobs, args.search_workers, args.email_workers, args.name)


if __name__ == "__main__":
    main()
