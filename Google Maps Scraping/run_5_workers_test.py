"""Multi-worker test runner with 5 concurrent workers processing the 5,000-task queue.

Monitors real-time extraction throughput, proxy rotation, and small business
lead categorization across multiple US cities and trade categories.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from browser_engine import BrowserEngine
from config import DEFAULT_CONFIG, PROXIES_DIR, ScraperConfig
from database import Database
from export import LeadExporter
from models import Lead, SearchJob, WebsiteType
from proxy_manager import ProxyManager
from website_analyzer import is_target_lead

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


async def run_multi_worker_test(max_batches: int = 25) -> None:
    """Runs 5 concurrent workers across the 10 proxy pool."""
    config = ScraperConfig(
        workers=5,
        headless=True,
        max_results_per_query=20,
        scroll_delay_min=0.8,
        scroll_delay_max=1.5,
        detail_extraction=False,
    )

    db = Database(config.database_url)
    proxy_manager = ProxyManager(proxy_urls_file=PROXIES_DIR / "proxy-urls.txt")
    
    stats_init = db.get_stats()
    console.print(
        Panel.fit(
            f"[bold green]5-Worker Multi-Category Lead Scraper[/bold green]\n"
            f"[cyan]Queue Size:[/cyan] {stats_init['queue_pending']:,} pending search jobs (5,000 total)\n"
            f"[cyan]Workers:[/cyan] 5 Parallel Async Browser Engines\n"
            f"[cyan]Proxy Pool:[/cyan] 10 Dedicated Oxylabs ISP Routes (Round-Robin)\n"
            f"[cyan]Target Presets:[/cyan] All Small Business (50 Trade Categories × 100 Cities)",
            title="Execution Parameters",
            border_style="green",
        )
    )

    # Initialize 5 independent browser engines, each bound to distinct proxy routes
    engines: List[BrowserEngine] = []
    for i in range(config.workers):
        eng = BrowserEngine(config=config, proxy_manager=proxy_manager)
        await eng.initialize()
        engines.append(eng)

    t_start = time.time()
    processed_jobs = 0
    total_leads_batch = 0
    target_leads_batch = 0
    is_running = True

    async def worker_task(worker_id: int, engine: BrowserEngine) -> None:
        nonlocal processed_jobs, total_leads_batch, target_leads_batch
        while is_running:
            job = db.claim_next_job()
            if not job:
                break

            t0 = time.time()
            try:
                leads = await engine.execute_search_job(job)
                target_leads = [
                    l for l in leads
                    if is_target_lead(
                        l.website_type,
                        no_website_only=config.no_website_only,
                        include_social=config.include_social_media_as_no_website,
                        include_deprecated_google=config.include_deprecated_google_sites,
                        include_free_builders=config.include_free_builders_as_no_website,
                    )
                ]

                saved = db.save_leads_batch(leads)
                if job.id:
                    db.complete_job(job.id, results_found=len(leads), leads_saved=saved)

                processed_jobs += 1
                total_leads_batch += len(leads)
                target_leads_batch += len(target_leads)

                console.print(
                    f"  [cyan][Worker #{worker_id}][/cyan] Finished Job #{job.id}: "
                    f"'{job.keyword}' in '{job.location_name}' "
                    f"-> [green]{len(leads)} found[/green] ([bold yellow]{len(target_leads)} no-website[/bold yellow]) in {time.time()-t0:.2f}s"
                )

            except Exception as e:
                console.print(f"  [red][Worker #{worker_id}] Error on job #{job.id}: {e}[/red]")
                if job.id:
                    db.fail_job(job.id, str(e))

            if max_batches and processed_jobs >= max_batches:
                break

            await asyncio.sleep(0.5)

    try:
        tasks = [
            asyncio.create_task(worker_task(i + 1, engines[i]))
            for i in range(config.workers)
        ]
        await asyncio.gather(*tasks)
    finally:
        for eng in engines:
            await eng.close()

    total_time = time.time() - t_start
    final_stats = db.get_stats()

    # Summary Report
    console.print("\n[bold green]5-Worker Performance Report[/bold green]")
    table = Table(title="Execution Metrics", border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Jobs Processed", f"{processed_jobs:,}")
    table.add_row("Total Businesses Discovered", f"{total_leads_batch:,}")
    table.add_row("Target Leads Without Website", f"{target_leads_batch:,} ({round((target_leads_batch/total_leads_batch)*100, 1) if total_leads_batch else 0}%)")
    table.add_row("Total Elapsed Time", f"{total_time:.2f} seconds")
    table.add_row("Throughput (Leads / Minute)", f"{round((total_leads_batch / total_time) * 60, 1):,}")
    table.add_row("Throughput (Searches / Minute)", f"{round((processed_jobs / total_time) * 60, 1):,}")
    table.add_row("Remaining Queue Tasks", f"{final_stats['queue_pending']:,} / 5,000")

    console.print(table)

    # Sample Extracted Leads
    console.print("\n[bold green]Sample Extracted Leads Across Categories & Cities:[/bold green]")
    sample_table = Table(title="Latest Multi-Category Small Business Leads", border_style="magenta")
    sample_table.add_column("Business Name", style="bold")
    sample_table.add_column("Category", style="cyan")
    sample_table.add_column("Location")
    sample_table.add_column("Phone")
    sample_table.add_column("Rating / Revs")
    sample_table.add_column("Web Presence Status", style="yellow")

    all_target_leads = db.fetch_leads(no_website_only=True)
    for lead in all_target_leads[:15]:
        sample_table.add_row(
            lead["name"],
            lead["category"] or "N/A",
            f"{lead['city'] or ''}, {lead['state'] or ''}",
            lead["phone"] or "N/A",
            f"{lead['rating'] or 'N/A'} ({lead['reviews_count']})",
            (lead["website_explanation"] or lead["website_type"])[:35],
        )

    console.print(sample_table)

    # Export
    exporter = LeadExporter(db)
    export_path = config.export_dir / "leads_5000_campaign_no_website.csv"
    count = exporter.export_to_csv(export_path, no_website_only=True)
    console.print(f"\n[bold green]Exported {count} unique no-website leads to:[/bold green] {export_path}")


if __name__ == "__main__":
    asyncio.run(run_multi_worker_test(max_batches=20))
