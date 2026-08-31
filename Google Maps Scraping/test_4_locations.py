"""Live test runner across 4 distinct US geographic locations with a single proxy and single worker.

Tests Google Maps extraction for small businesses without websites across:
1. Austin, TX
2. Miami, FL
3. Denver, CO
4. Seattle, WA
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from browser_engine import BrowserEngine
from config import DEFAULT_CONFIG, PROXIES_DIR, ScraperConfig
from database import Database
from export import LeadExporter
from models import Lead, SearchJob, WebsiteType
from proxy_manager import ProxyManager
from website_analyzer import classify_website, is_target_lead

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# 4 Distinct U.S. Geographic Locations
TEST_LOCATIONS = [
    {"city": "Austin", "state": "TX", "lat": 30.2672, "lng": -97.7431},
    {"city": "Miami", "state": "FL", "lat": 25.7617, "lng": -80.1918},
    {"city": "Denver", "state": "CO", "lat": 39.7392, "lng": -104.9903},
    {"city": "Seattle", "state": "WA", "lat": 47.6062, "lng": -122.3321},
]

KEYWORD = "auto repair"


async def run_live_test() -> None:
    """Executes live scraper test across 4 locations with single proxy and single worker."""
    console.print(
        Panel.fit(
            f"[bold green]Google Maps Lead Scraper - Live Test[/bold green]\n"
            f"[cyan]Target Keyword:[/cyan] {KEYWORD}\n"
            f"[cyan]Locations (4):[/cyan] Austin TX, Miami FL, Denver CO, Seattle WA\n"
            f"[cyan]Workers:[/cyan] 1 (Single Worker)\n"
            f"[cyan]Browser Mode:[/cyan] Headless (Fast Asset-Blocked Chromium)\n"
            f"[cyan]Proxy:[/cyan] Single Dedicated ISP Route",
            title="Test Parameters",
            border_style="green",
        )
    )

    # 1. Load single proxy
    proxy_manager = ProxyManager(proxy_urls_file=PROXIES_DIR / "proxy-urls.txt")
    if proxy_manager.total_proxies == 0:
        console.print("[bold red]ERROR: No proxy found in Proxies/proxy-urls.txt![/bold red]")
        sys.exit(1)

    single_proxy = proxy_manager.get_next_proxy()
    console.print(f"[green]Using Single Proxy Route:[/green] {single_proxy.host}:{single_proxy.port}")

    # 2. Configure headless engine
    config = ScraperConfig(
        headless=True,
        workers=1,
        max_results_per_query=30,  # Grab first batch per location for test
        scroll_delay_min=0.8,
        scroll_delay_max=1.5,
        detail_extraction=False,   # Fast feed extraction
    )
    
    test_db_path = Path(__file__).resolve().parent / "test_leads.db"
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass

    db = Database(test_db_path)
    engine = BrowserEngine(config=config, proxy_manager=proxy_manager)
    await engine.initialize()

    location_summaries = []
    total_found = 0
    total_no_website = 0

    try:
        # 3. Process each location sequentially
        for idx, loc in enumerate(TEST_LOCATIONS, 1):
            loc_label = f"{loc['city']}, {loc['state']}"
            console.print(f"\n[bold yellow]({idx}/4) Scraping Location: {loc_label}...[/bold yellow]")

            job = SearchJob(
                keyword=KEYWORD,
                location_name=loc_label,
                latitude=loc["lat"],
                longitude=loc["lng"],
                zoom_level=13,
            )

            t0 = time.time()
            leads: List[Lead] = await engine.execute_search_job(job)
            elapsed = time.time() - t0

            # Classify leads
            no_web_count = 0
            social_count = 0
            custom_count = 0

            for lead in leads:
                lead.search_location = loc_label
                lead.search_keyword = KEYWORD
                if lead.website_type == WebsiteType.NO_WEBSITE:
                    no_web_count += 1
                elif lead.website_type == WebsiteType.SOCIAL_MEDIA:
                    social_count += 1
                else:
                    custom_count += 1

            saved_count = db.save_leads_batch(leads)
            total_found += len(leads)
            total_no_website += (no_web_count + social_count)

            location_summaries.append({
                "location": loc_label,
                "leads_found": len(leads),
                "no_website": no_web_count,
                "social_only": social_count,
                "has_custom_web": custom_count,
                "elapsed_sec": round(elapsed, 2),
            })

            console.print(
                f"   [cyan]Extracted:[/cyan] {len(leads)} businesses in {elapsed:.2f}s "
                f"([red]No Website: {no_web_count}[/red], [yellow]Social Only: {social_count}[/yellow], [green]Custom Web: {custom_count}[/green])"
            )

            await asyncio.sleep(1.0)

    finally:
        await engine.close()

    # 4. Results Summary Table
    console.print("\n[bold green]Location Summary Matrix[/bold green]")
    table = Table(title="Live Test Results (Single Proxy, Single Worker)", border_style="cyan")
    table.add_column("Location", style="bold")
    table.add_column("Total Found", justify="right")
    table.add_column("True No-Website", justify="right", style="red")
    table.add_column("Social Media Only", justify="right", style="yellow")
    table.add_column("Custom Website", justify="right", style="green")
    table.add_column("Target Leads (%)", justify="right", style="bold cyan")
    table.add_column("Speed (sec)", justify="right")

    for s in location_summaries:
        target_sum = s["no_website"] + s["social_only"]
        pct = round((target_sum / s["leads_found"]) * 100, 1) if s["leads_found"] > 0 else 0.0
        table.add_row(
            s["location"],
            str(s["leads_found"]),
            str(s["no_website"]),
            str(s["social_only"]),
            str(s["has_custom_web"]),
            f"{pct}%",
            f"{s['elapsed_sec']}s",
        )

    console.print(table)

    # 5. Display Sample Extracted Leads (No Website Leads)
    console.print("\n[bold green]Sample Extracted Small Business Leads Without Websites:[/bold green]")
    sample_table = Table(title="Discovered Target Leads", border_style="magenta")
    sample_table.add_column("Business Name", style="bold")
    sample_table.add_column("Location")
    sample_table.add_column("Phone", style="cyan")
    sample_table.add_column("Rating / Reviews")
    sample_table.add_column("Web Presence Status", style="yellow")

    all_target_leads = db.fetch_leads(no_website_only=True)
    for lead in all_target_leads[:12]:
        status_desc = lead["website_explanation"] or lead["website_type"]
        sample_table.add_row(
            lead["name"],
            f"{lead['city'] or ''}, {lead['state'] or ''}",
            lead["phone"] or "N/A",
            f"{lead['rating'] or 'N/A'} ({lead['reviews_count']} revs)",
            status_desc[:40],
        )

    console.print(sample_table)

    # 6. Export to CSV
    exporter = LeadExporter(db)
    export_file = Path(__file__).resolve().parent / "exports" / "test_4_locations_leads.csv"
    exported_count = exporter.export_to_csv(export_file, no_website_only=True)
    console.print(f"\n[bold green]Successfully exported {exported_count} no-website leads to:[/bold green] {export_file}")


if __name__ == "__main__":
    asyncio.run(run_live_test())
