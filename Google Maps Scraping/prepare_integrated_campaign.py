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


def _sample_points_for_round(round_index: int) -> tuple[tuple[float, float], ...]:
    """Return a deterministic coordinate sample that is unique per campaign round.

    The first round keeps the original coordinates for reproducibility. Later
    rounds shift the same low-density sample by a deterministic amount so the
    database's (keyword, location) uniqueness constraint yields new jobs while
    preserving nationwide state coverage.
    """
    if round_index < 0:
        raise ValueError("round_index must be non-negative")
    if round_index == 0:
        return SAMPLE_POINTS

    # Keep every fraction away from the boundary and use a different modular
    # offset for latitude/longitude. The per-point nudge prevents accidental
    # collisions when a later round wraps around the unit interval.
    lat_shift = (0.137 * round_index) % 0.84
    lng_shift = (0.223 * round_index) % 0.84
    return tuple(
        (
            0.08 + ((lat + lat_shift + (index * 0.011)) % 0.84),
            0.08 + ((lng + lng_shift + (index * 0.017)) % 0.84),
        )
        for index, (lat, lng) in enumerate(SAMPLE_POINTS)
    )


def nationwide_candidates(round_index: int = 0) -> Iterator[SearchJob]:
    """Yields category/state-balanced coordinates in deterministic rounds."""
    keywords = CATEGORY_PRESETS["all_small_business"]
    states = sorted(US_STATE_BOUNDS)
    for lat_fraction, lng_fraction in _sample_points_for_round(round_index):
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


def prepare(
    target_jobs: int,
    search_workers: int,
    email_workers: int,
    name: str | None,
    round_index: int = 0,
) -> int:
    db = Database(DEFAULT_CONFIG.database_url)
    campaign_name = name or (
        f"nationwide-{target_jobs}-integrated-r{round_index}-"
        f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    )
    campaign_id = db.create_campaign(campaign_name, 0, search_workers, email_workers)

    added = 0
    batch: list[SearchJob] = []
    try:
        for job in nationwide_candidates(round_index=round_index):
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
    parser.add_argument(
        "--round",
        dest="round_index",
        type=int,
        default=0,
        help="Deterministic nationwide coordinate round (use a new value for a fresh job set)",
    )
    args = parser.parse_args()
    prepare(args.jobs, args.search_workers, args.email_workers, args.name, args.round_index)


if __name__ == "__main__":
    main()
