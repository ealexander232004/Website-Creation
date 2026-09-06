"""Production 10-Worker Campaign Runner with Live Monitoring and Proxy Health Protection.

Maps 10 parallel browser workers to the 10 Oxylabs dedicated ISP proxy routes,
monitoring real-time scrape throughput and protecting proxy reputation via
automated circuit breaking.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from browser_engine import BrowserEngine
from captcha_handler import CaptchaHandler
from config import DEFAULT_CONFIG, PROXIES_DIR, ScraperConfig
from database import Database
from export import LeadExporter
from models import Lead, SearchJob, WebsiteType
from proxy_manager import ProxyManager, ProxyRoute
from website_analyzer import is_target_lead

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


class CampaignRunner:
    def __init__(self, workers_count: int = 10) -> None:
        self.workers_count = workers_count
        self.config = ScraperConfig(
            workers=workers_count,
            headless=True,
            max_results_per_query=20,
            scroll_delay_min=0.8,
            scroll_delay_max=1.5,
            detail_extraction=False,
        )
        self.db = Database(self.config.database_url)
        self.proxy_manager = ProxyManager(proxy_urls_file=PROXIES_DIR / "proxy-urls.txt")
        self.captcha_handler = CaptchaHandler(api_key=self.config.capsolver_api_key)
        self.exporter = LeadExporter(self.db)
        self.is_running = True
        self.processed_count = 0
        self.total_found_count = 0
        self.target_leads_count = 0
        self.start_time = time.time()
        self.engines: List[BrowserEngine] = []

    async def initialize(self) -> None:
        """Initializes 10 independent browser engines, each bound to a dedicated proxy route."""
        # Reset any interrupted or failed tasks back to pending for automatic recovery
        with self.db._get_connection() as conn:
            conn.execute("UPDATE search_queue SET status = 'pending', error_message = NULL WHERE status IN ('failed', 'in_progress')")
        stats = self.db.get_stats()
        console.print(
            Panel.fit(
                f"[bold green]Google Maps 10-Worker Lead Campaign[/bold green]\n"
                f"[cyan]Database Queue:[/cyan] {stats['queue_pending']:,} pending tasks ({stats['queue_total']:,} total)\n"
                f"[cyan]Workers:[/cyan] {self.workers_count} Concurrent Browser Engines\n"
                f"[cyan]Proxy Pool:[/cyan] {self.proxy_manager.total_proxies} Dedicated ISP Routes\n"
                f"[cyan]CapSolver Integration:[/cyan] {'Enabled' if self.captcha_handler.enabled else 'Disabled'}\n"
                f"[cyan]Circuit Breaker:[/cyan] Active (Auto-halts on repeated failures)",
                title="Campaign Engine Initialized",
                border_style="green",
            )
        )

        for i in range(self.workers_count):
            eng = BrowserEngine(
                config=self.config,
                proxy_manager=self.proxy_manager,
                captcha_handler=self.captcha_handler,
            )
            await eng.initialize()
            self.engines.append(eng)

    async def worker_loop(self, worker_id: int, engine: BrowserEngine) -> None:
        """Individual worker pulling tasks with persistent page reuse to avoid SSL churn."""
        proxy_route = self.proxy_manager.get_route_for_worker(worker_id)
        proxy_label = f"{proxy_route.host}:{proxy_route.port}" if proxy_route else "Direct"

        # Stagger initial worker start to prevent synchronized traffic burst
        await asyncio.sleep((worker_id - 1) * 0.4)

        # Initialize ONE persistent context and page for this worker
        context, page = await engine.create_context_and_page(proxy_route=proxy_route)

        try:
            while self.is_running:
                # 1. Circuit Breaker Protection
                if self.proxy_manager.is_circuit_tripped():
                    console.print(f"  [bold red][Worker #{worker_id}] Circuit breaker active! Pausing for 5s...[/bold red]")
                    await asyncio.sleep(5.0)
                    continue

                # 2. Check Proxy Cooldown
                if proxy_route and not proxy_route.is_available():
                    await asyncio.sleep(3.0)
                    continue

                # 3. Pull Next Search Task
                job = self.db.claim_next_job()
                if not job:
                    console.print(f"  [cyan][Worker #{worker_id}][/cyan] Queue empty. Worker completed.")
                    break

                t0 = time.time()
                try:
                    leads = await engine.execute_search_on_page(page, job, proxy_route=proxy_route)
                    target_leads = [
                        l for l in leads
                        if is_target_lead(
                            l.website_type,
                            no_website_only=self.config.no_website_only,
                            include_social=self.config.include_social_media_as_no_website,
                            include_deprecated_google=self.config.include_deprecated_google_sites,
                            include_free_builders=self.config.include_free_builders_as_no_website,
                        )
                    ]

                    saved_count = self.db.save_leads_batch(leads)
                    if job.id:
                        self.db.complete_job(job.id, results_found=len(leads), leads_saved=saved_count)

                    if proxy_route:
                        proxy_route.mark_success()
                    self.proxy_manager.record_global_success()

                    self.processed_count += 1
                    self.total_found_count += len(leads)
                    self.target_leads_count += len(target_leads)
                    elapsed = time.time() - t0

                    console.print(
                        f"  [cyan][Worker #{worker_id:02d} | Port {proxy_route.port if proxy_route else 'N/A'}][/cyan] "
                        f"Task #{job.id}: [bold white]{job.keyword}[/bold white] in [bold yellow]{job.location_name}[/bold yellow] "
                        f"-> [green]{len(leads)} found[/green] ([bold red]{len(target_leads)} no-website[/bold red]) "
                        f"in {elapsed:.2f}s"
                    )

                    # Periodic auto-export every 100 jobs
                    if self.processed_count % 100 == 0:
                        export_file = self.config.export_dir / "leads_5000_campaign_live.csv"
                        self.exporter.export_to_csv(export_file, no_website_only=True)

                except Exception as e:
                    console.print(f"  [red][Worker #{worker_id:02d} | Error on Task #{job.id}]: {e}[/red]")
                    if proxy_route:
                        proxy_route.mark_failure(base_cooldown=30.0)
                    self.proxy_manager.record_global_failure()

                    if job.id:
                        self.db.fail_job(job.id, str(e))

                    # If page crashed, reload page
                    try:
                        await page.close()
                        page = await context.new_page()
                    except Exception:
                        pass

                # Gentle human-like pacing per worker (1.2s - 2.0s)
                await asyncio.sleep(1.5)
        finally:
            await context.close()
    async def run(self) -> None:
        """Runs the 10 concurrent worker loops until queue is exhausted or stopped."""
        await self.initialize()

        try:
            tasks = [
                asyncio.create_task(self.worker_loop(i + 1, self.engines[i]))
                for i in range(self.workers_count)
            ]
            await asyncio.gather(*tasks)
        finally:
            for eng in self.engines:
                await eng.close()

            total_elapsed = time.time() - self.start_time
            export_file = self.config.export_dir / "leads_5000_campaign_final.csv"
            exported = self.exporter.export_to_csv(export_file, no_website_only=True)
            console.print(f"\n[bold green]Campaign Export Complete! {exported} unique no-website leads saved to:[/bold green] {export_file}")


if __name__ == "__main__":
    runner = CampaignRunner(workers_count=10)
    asyncio.run(runner.run())
