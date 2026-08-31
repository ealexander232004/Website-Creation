"""Configuration module for Google Maps Scraping Engine.

Handles environment loading, proxy discovery, CapSolver integration paths,
and scraper runtime parameters.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Base directory references
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
PROXIES_DIR = WORKSPACE_DIR / "Proxies"
CAPTCHA_DIR = WORKSPACE_DIR / "Captcha Solver"

# Attempt loading environment variables from known sibling bundles if available
if (PROXIES_DIR / "proxies.env").is_file():
    load_dotenv(PROXIES_DIR / "proxies.env")

if (CAPTCHA_DIR / "capsolver.env").is_file():
    load_dotenv(CAPTCHA_DIR / "capsolver.env")

if (BASE_DIR / ".env").is_file():
    load_dotenv(BASE_DIR / ".env")


@dataclass
class ScraperConfig:
    """Master configuration for the Google Maps Lead Extraction Engine."""

    # Engine Mode: 'rpc' (direct fast HTTP endpoint) or 'browser' (headless Playwright)
    mode: str = "rpc"
    headless: bool = True
    browser_type: str = "chromium"
    workers: int = 3
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

    # Scrape Limits & Scrolling Behavior
    max_results_per_query: int = 120  # Google Maps cap per viewport
    scroll_delay_min: float = 1.0
    scroll_delay_max: float = 2.2
    max_scroll_attempts_without_growth: int = 5
    page_timeout_seconds: int = 45
    detail_extraction: bool = True  # Click each result for full metadata if needed

    # Filtering Criteria
    no_website_only: bool = True
    include_social_media_as_no_website: bool = True
    include_deprecated_google_sites: bool = True
    include_free_builders_as_no_website: bool = True
    min_reviews: int = 0
    min_rating: float = 0.0
    unclaimed_only: bool = False

    # Proxy Configuration
    use_proxies: bool = True
    proxy_urls_file: Optional[Path] = field(
        default_factory=lambda: (
            PROXIES_DIR / "proxy-urls.txt"
            if (PROXIES_DIR / "proxy-urls.txt").is_file()
            else (BASE_DIR / "proxy-urls.txt" if (BASE_DIR / "proxy-urls.txt").is_file() else None)
        )
    )
    custom_proxy_url: Optional[str] = os.getenv("STATIC_ISP_PROXY_URL") or os.getenv("HTTP_PROXY")

    # Captcha Configuration
    capsolver_api_key: Optional[str] = os.getenv("CAPSOLVER_API_KEY")
    auto_solve_captchas: bool = True

    # Database & Storage
    database_path: Path = BASE_DIR / "gmaps_leads.db"
    export_dir: Path = BASE_DIR / "exports"

    def __post_init__(self) -> None:
        self.export_dir.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = ScraperConfig()
