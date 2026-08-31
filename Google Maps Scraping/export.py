"""Export module for Google Maps leads with Excel, CSV, and JSON formatting."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from database import Database

logger = logging.getLogger("gmaps_scraper.export")


class LeadExporter:
    """Exports scraped leads from SQLite database into structured data files."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def export_to_csv(
        self,
        output_path: Path,
        no_website_only: bool = True,
        state: Optional[str] = None,
        category: Optional[str] = None,
        min_reviews: int = 0,
        unclaimed_only: bool = False,
    ) -> int:
        """Exports filtered leads into a standard CSV file."""
        leads = self.db.fetch_leads(
            no_website_only=no_website_only,
            state=state,
            category=category,
            min_reviews=min_reviews,
            unclaimed_only=unclaimed_only,
        )

        if not leads:
            logger.warning("No leads matched the export filter criteria.")
            return 0

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "name",
            "category",
            "phone",
            "full_address",
            "street",
            "city",
            "state",
            "zip_code",
            "has_website",
            "website_type",
            "website_raw",
            "website_explanation",
            "is_claimed",
            "rating",
            "reviews_count",
            "price_level",
            "maps_url",
            "search_keyword",
            "search_location",
            "scraped_at",
        ]

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for lead in leads:
                writer.writerow(lead)

        logger.info("Exported %d leads to CSV: %s", len(leads), output_path)
        return len(leads)

    def export_to_excel(
        self,
        output_path: Path,
        state: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """Exports categorized leads into a multi-tab Excel workbook with summary sheets."""
        all_leads = self.db.fetch_leads(no_website_only=False, state=state, category=category)
        if not all_leads:
            logger.warning("No leads found in database to export.")
            return 0

        df_all = pd.DataFrame(all_leads)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create filtered slices
        df_no_website = df_all[df_all["has_website"] == 0]
        df_social_only = df_all[df_all["website_type"] == "social_media"]
        df_unclaimed = df_all[df_all["is_claimed"] == "unclaimed"]

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_no_website.to_excel(writer, sheet_name="No Website Leads", index=False)
            df_social_only.to_excel(writer, sheet_name="Social Media Only", index=False)
            df_unclaimed.to_excel(writer, sheet_name="Unclaimed GBP", index=False)
            df_all.to_excel(writer, sheet_name="All Scraped Leads", index=False)

        logger.info("Exported %d total leads across tabs to Excel: %s", len(df_all), output_path)
        return len(df_all)

    def export_to_jsonl(
        self,
        output_path: Path,
        no_website_only: bool = True,
    ) -> int:
        """Exports leads as JSON lines format."""
        leads = self.db.fetch_leads(no_website_only=no_website_only)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for lead in leads:
                f.write(json.dumps(lead, default=str) + "\n")

        logger.info("Exported %d leads to JSONL: %s", len(leads), output_path)
        return len(leads)
