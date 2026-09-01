"""Scraper orchestrator managing async worker pools and pipeline execution.

Supports dual execution modes:
1. 'rpc' (default): Lower-overhead direct Maps JSON payload queries with no DOM rendering.
2. 'browser': Headless Playwright Chromium browser automation.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Optional

from browser_engine import BrowserEngine
from captcha_handler import CaptchaHandler
from config import ScraperConfig
from database import Database
from email_extractor import EmailFootprintExtractor
from geo_grid import (
    generate_city_jobs,
    generate_grid_jobs,
    generate_multi_category_city_jobs,
    generate_multi_category_state_jobs,
    generate_state_grid_jobs,
)
from models import Lead, SearchJob, SearchJobStatus
from proxy_manager import ProxyManager, ProxyRoute
from rpc_client import GoogleMapsRpcClient
from website_analyzer import is_target_lead

logger = logging.getLogger("gmaps_scraper.orchestrator")


class ScraperOrchestrator:
    """Coordinates search job queue consumption and lead extraction across RPC or Browser engines."""

    def __init__(self, config: ScraperConfig, campaign_id: Optional[int] = None) -> None:
        self.config = config
        self.campaign_id = campaign_id
        self.db = Database(config.database_url)
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
        self._search_done = asyncio.Event()
        # Maps RPC calls and email discovery are both blocking network workloads.
        # Dedicated pools prevent one pipeline stage from consuming the other's
        # slots in asyncio's comparatively small default thread pool.
        self._search_executor = ThreadPoolExecutor(
            max_workers=max(1, config.workers),
            thread_name_prefix="maps-search",
        )
        self.email_extractor = (
            EmailFootprintExtractor(
                database=self.db,
                config=config,
                proxy_manager=self.proxy_manager,
                concurrency=config.email_workers,
            )
            if config.email_extraction_enabled
            else None
        )
        self._email_executor = (
            ThreadPoolExecutor(
                max_workers=max(1, config.email_workers),
                thread_name_prefix="email-search",
            )
            if self.email_extractor
            else None
        )

    async def _execute_job_rpc(
        self,
        job: SearchJob,
        proxy_route: Optional[ProxyRoute],
    ) -> List[Lead]:
        """Executes a browserless search through the worker's dedicated proxy."""
        if proxy_route is None:
            raise RuntimeError("Direct Google Maps mode requires a configured proxy route")

        # Fallback default coordinates to central US or lat/lng
        lat = job.latitude if job.latitude is not None else 39.8283
        lng = job.longitude if job.longitude is not None else -98.5795

        client = GoogleMapsRpcClient(
            proxy_url=proxy_route.raw_url,
            timeout=self.config.page_timeout_seconds,
            zoom_level=job.zoom_level,
        )
        # Execute in thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        try:
            leads = await loop.run_in_executor(
                self._search_executor,
                client.scrape_viewport_all,
                job.keyword,
                lat,
                lng,
                self.config.max_results_per_query,
            )
        finally:
            client.close()

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

            job = self.db.claim_next_job(self.campaign_id)
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
                    leads = await self._execute_job_rpc(job, proxy_route=proxy_route)
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
                email_queued = 0
                if self.email_extractor and job.campaign_id:
                    email_queued = self.db.enqueue_email_checks(job.campaign_id, target_leads)
                if job.id:
                    self.db.complete_job(job.id, results_found=len(leads), leads_saved=saved_count)

                if proxy_route:
                    proxy_route.mark_success()
                self.proxy_manager.record_global_success()

                logger.info(
                    "Worker #%d finished job #%s: %d total found, %d target saved, %d email checks queued.",
                    worker_id,
                    job.id,
                    len(leads),
                    saved_count,
                    email_queued,
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

    async def _email_worker_loop(self, worker_id: int) -> None:
        """Consumes durable email jobs while search workers continue producing leads."""
        logger.info("Email worker #%d started.", worker_id)
        while self._is_running:
            job = self.db.claim_next_email_job(self.campaign_id)
            if not job:
                if self._search_done.is_set() and self.db.email_work_remaining(self.campaign_id) == 0:
                    logger.info("Email worker #%d: enrichment queue complete.", worker_id)
                    return
                await asyncio.sleep(self.config.email_poll_seconds)
                continue

            try:
                loop = asyncio.get_running_loop()
                emails = await loop.run_in_executor(
                    self._email_executor,
                    self.email_extractor.search_lead_footprint,
                    job,
                )
                if emails:
                    saved = self.email_extractor.save_extracted_emails(emails)
                    if saved:
                        self.email_extractor.mark_lead_status(job["place_id"], "completed", saved)
                        self.db.complete_email_job(job["email_job_id"], "completed", saved)
                        logger.info(
                            "Email worker #%d retained %d email(s) for %s.",
                            worker_id,
                            saved,
                            job["name"],
                        )
                    else:
                        self.email_extractor.mark_lead_status(job["place_id"], "no_email", 0)
                        self.db.complete_email_job(job["email_job_id"], "no_email")
                        logger.info(
                            "Email worker #%d rejected all candidate emails for %s.",
                            worker_id,
                            job["name"],
                        )
                else:
                    self.email_extractor.mark_lead_status(job["place_id"], "no_email", 0)
                    self.db.complete_email_job(job["email_job_id"], "no_email")
                    logger.info("Email worker #%d found no email for %s.", worker_id, job["name"])
            except Exception as exc:
                logger.exception("Email worker #%d failed for %s: %s", worker_id, job["name"], exc)
                self.email_extractor.mark_lead_status(job["place_id"], "error", 0)
                self.db.complete_email_job(job["email_job_id"], "failed", error_message=str(exc))

    async def run(self) -> None:
        """Runs search and email worker pools together until both durable queues are exhausted."""
        self._is_running = True
        self._search_done.clear()
        if self.campaign_id:
            self.db.reset_interrupted_campaign_work(self.campaign_id)
        if self.browser_engine:
            await self.browser_engine.initialize()

        try:
            search_workers = [
                asyncio.create_task(self._worker_loop(worker_id=i + 1))
                for i in range(self.config.workers)
            ]
            email_workers = [
                asyncio.create_task(self._email_worker_loop(worker_id=i + 1))
                for i in range(self.config.email_workers)
            ] if self.email_extractor else []
            await asyncio.gather(*search_workers)
            self._search_done.set()
            if email_workers:
                await asyncio.gather(*email_workers)
            if self.campaign_id:
                self.db.finish_campaign(self.campaign_id)
        finally:
            self._search_done.set()
            self._is_running = False
            if self.browser_engine:
                await self.browser_engine.close()
            self._search_executor.shutdown(wait=True, cancel_futures=False)
            if self._email_executor:
                self._email_executor.shutdown(wait=True, cancel_futures=False)

    def _ensure_campaign(self, target_jobs: int) -> int:
        if self.campaign_id is None:
            name = f"integrated-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            self.campaign_id = self.db.create_campaign(
                name=name,
                target_jobs=target_jobs,
                search_workers=self.config.workers,
                email_workers=self.config.email_workers,
            )
        return self.campaign_id

    def enqueue_state_campaign(self, keyword: str, state_code: str, step_deg: float = 0.10) -> int:
        """Enqueues coordinate grid search jobs for an entire U.S. state."""
        jobs = generate_state_grid_jobs(keyword=keyword, state_code=state_code, step_deg=step_deg)
        campaign_id = self._ensure_campaign(len(jobs))
        added = self.db.enqueue_jobs(jobs, campaign_id=campaign_id)
        self.db.update_campaign_target(campaign_id, added)
        return added

    def enqueue_cities_campaign(
        self,
        keyword: str,
        state_filter: Optional[str] = None,
        custom_cities: Optional[List[str]] = None,
    ) -> int:
        """Enqueues major cities search jobs."""
        jobs = generate_city_jobs(keyword=keyword, state_filter=state_filter, custom_cities=custom_cities)
        campaign_id = self._ensure_campaign(len(jobs))
        added = self.db.enqueue_jobs(jobs, campaign_id=campaign_id)
        self.db.update_campaign_target(campaign_id, added)
        return added

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
        campaign_id = self._ensure_campaign(len(jobs))
        added = self.db.enqueue_jobs(jobs, campaign_id=campaign_id)
        self.db.update_campaign_target(campaign_id, added)
        return added
