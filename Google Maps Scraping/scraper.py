"""Scraper orchestrator managing async worker pools and pipeline execution.

Supports dual execution modes:
1. 'rpc' (default): High-performance direct Protobuf HTTP queries (~100x faster, zero DOM overhead).
2. 'browser': Headless Playwright Chromium browser automation.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import List, Optional

from browser_engine import BrowserEngine
from captcha_handler import CaptchaHandler
from config import ScraperConfig
from database import Database
from geo_grid import (
    generate_city_jobs,
    generate_grid_jobs,
    generate_multi_category_city_jobs,
    generate_multi_category_state_jobs,
    generate_state_grid_jobs,
)
from models import Lead, SearchJob, SearchJobStatus
from proxy_manager import ProxyManager
from rpc_client import GoogleMapsRpcClient
from website_analyzer import is_target_lead

logger = logging.getLogger("gmaps_scraper.orchestrator")


class ScraperOrchestrator:
    """Coordinates search job queue consumption and lead extraction across RPC or Browser engines."""

    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self.db = Database(config.database_path)
        self.proxy_manager = ProxyManager(proxy_urls_file=config.proxy_urls_file)
        self.captcha_handler = CaptchaHandler(api_key=config.capsolver_api_key)
        self.browser_engine = (
            BrowserEngine(
                config=config,
                proxy_manager=self.proxy_manager,
                captcha_handler=self.captcha_handler,
            )
            if config.mode == "browser"
            else None
        )
        self._is_running = False

    async def _execute_job_rpc(self, job: SearchJob) -> List[Lead]:
        """Executes a search job using direct HTTP RPC queries."""
        proxy_route = self.proxy_manager.get_next_proxy() if self.config.use_proxies else None
        proxy_url = proxy_route.raw_url if proxy_route else None

        # Fallback default coordinates to central US or lat/lng
        lat = job.latitude if job.latitude is not None else 39.8283
        lng = job.longitude if job.longitude is not None else -98.5795

        client = GoogleMapsRpcClient(proxy_url=proxy_url, timeout=self.config.page_timeout_seconds)
        # Execute in thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        leads = await loop.run_in_executor(
            None,
            client.scrape_viewport_all,
            job.keyword,
            lat,
            lng,
            self.config.max_results_per_query,
        )

        if proxy_route:
            if leads:
                proxy_route.mark_success()
            else:
                proxy_route.mark_failure(cooldown_seconds=30.0)

        return leads

    async def _worker_loop(self, worker_id: int) -> None:
        """Individual async worker consuming tasks from the search queue."""
        proxy_route = self.proxy_manager.get_route_for_worker(worker_id)
        proxy_desc = f"{proxy_route.host}:{proxy_route.port}" if proxy_route else "Direct"
        logger.info("Worker #%d started with proxy: %s", worker_id, proxy_desc)

        while self._is_running:
            # Check global circuit breaker to protect proxy pool reputation
            if self.proxy_manager.is_circuit_tripped():
                logger.warning("Worker #%d: Circuit breaker active. Pausing for 5s...", worker_id)
                await asyncio.sleep(5.0)
                continue

            # Check if assigned proxy is in backoff cooldown
            if proxy_route and not proxy_route.is_available():
                logger.debug("Worker #%d: Proxy %s cooling down. Waiting 3s...", worker_id, proxy_desc)
                await asyncio.sleep(3.0)
                continue

            job = self.db.claim_next_job()
            if not job:
                logger.info("Worker #%d: No more pending jobs in queue. Idling.", worker_id)
                break

            logger.info(
                "Worker #%d processing job #%s: '%s' in '%s' [Proxy: %s]",
                worker_id,
                job.id,
                job.keyword,
                job.location_name,
                proxy_desc,
            )

            try:
                if self.config.mode == "rpc":
                    leads = await self._execute_job_rpc(job)
                else:
                    leads = await self.browser_engine.execute_search_job(job, proxy_route=proxy_route)

                # Filter leads based on configuration
                target_leads: List[Lead] = []
                for lead in leads:
                    if is_target_lead(
                        lead.website_type,
                        no_website_only=self.config.no_website_only,
                        include_social=self.config.include_social_media_as_no_website,
                        include_deprecated_google=self.config.include_deprecated_google_sites,
                        include_free_builders=self.config.include_free_builders_as_no_website,
                    ):
                        target_leads.append(lead)

                # Save leads to database
                saved_count = self.db.save_leads_batch(target_leads)
                if job.id:
                    self.db.complete_job(job.id, results_found=len(leads), leads_saved=saved_count)

                if proxy_route:
                    proxy_route.mark_success()
                self.proxy_manager.record_global_success()

                logger.info(
                    "Worker #%d finished job #%s: %d total found, %d target saved.",
                    worker_id,
                    job.id,
                    len(leads),
                    saved_count,
                )

            except Exception as e:
                logger.error("Worker #%d failed job #%s on %s: %s", worker_id, job.id, proxy_desc, e)
                if proxy_route:
                    proxy_route.mark_failure(base_cooldown=30.0)
                self.proxy_manager.record_global_failure()

                if job.id:
                    self.db.fail_job(job.id, str(e))

            # Adaptive jitter delay between searches per worker (1.0s - 2.0s)
            delay = random.uniform(1.0, 2.0)
            await asyncio.sleep(delay)
        """Spawns worker coroutines and waits for completion."""
        self._is_running = True
        if self.browser_engine:
            await self.browser_engine.initialize()

        try:
            workers = [
                asyncio.create_task(self._worker_loop(worker_id=i + 1))
                for i in range(self.config.workers)
            ]
            await asyncio.gather(*workers)
        finally:
            self._is_running = False
            if self.browser_engine:
                await self.browser_engine.close()

    def enqueue_state_campaign(self, keyword: str, state_code: str, step_deg: float = 0.10) -> int:
        """Enqueues coordinate grid search jobs for an entire U.S. state."""
        jobs = generate_state_grid_jobs(keyword=keyword, state_code=state_code, step_deg=step_deg)
        return self.db.enqueue_jobs(jobs)

    def enqueue_cities_campaign(
        self,
        keyword: str,
        state_filter: Optional[str] = None,
        custom_cities: Optional[List[str]] = None,
    ) -> int:
        """Enqueues major cities search jobs."""
        jobs = generate_city_jobs(keyword=keyword, state_filter=state_filter, custom_cities=custom_cities)
        return self.db.enqueue_jobs(jobs)

    def enqueue_taxonomy_campaign(
        self,
        keywords: List[str],
        state_code: Optional[str] = None,
        custom_cities: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> int:
        """Enqueues multi-category Cartesian product search tasks."""
        if state_code:
            jobs = generate_multi_category_state_jobs(
                keywords=keywords,
                state_code=state_code,
                limit_jobs=limit,
            )
        else:
            jobs = generate_multi_category_city_jobs(
                keywords=keywords,
                custom_cities=custom_cities,
                limit_jobs=limit,
            )
        return self.db.enqueue_jobs(jobs)
