"""Browser management and human-like automation engine using Playwright.

Runs headless by default with anti-detection fingerprinting, proxy support,
and automated Google Maps feed scrolling.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from config import ScraperConfig
from models import Lead, SearchJob
from parser import GoogleMapsParser
from proxy_manager import ProxyManager, ProxyRoute
from captcha_handler import CaptchaHandler

logger = logging.getLogger("gmaps_scraper.browser")

# Anti-detection stealth script injected into every new page context
STEALTH_INJECTION_JS = """
// Overwrite navigator.webdriver to prevent automation flags
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Mock realistic plugins list
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Ensure English locales
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
});

// Mock chrome object
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};
"""


class BrowserEngine:
    """Manages Playwright browser lifecycles, contexts, and stealth interactions."""

    def __init__(
        self,
        config: ScraperConfig,
        proxy_manager: Optional[ProxyManager] = None,
        captcha_handler: Optional[CaptchaHandler] = None,
    ) -> None:
        self.config = config
        self.proxy_manager = proxy_manager
        self.captcha_handler = captcha_handler
        self._playwright = None
        self._browser = None

    async def initialize(self) -> None:
        """Launches the shared Playwright Chromium browser."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--hide-scrollbars",
            "--mute-audio",
            "--lang=en-US,en",
        ]

        # Assign default proxy to browser instance if available
        proxy_dict = None
        if self.proxy_manager and self.config.use_proxies:
            route = self.proxy_manager.get_next_proxy()
            if route:
                proxy_dict = route.to_playwright_dict()

        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            proxy=proxy_dict,
            args=launch_args,
        )
        logger.info(
            "Launched Playwright Chromium instance (headless=%s).",
            self.config.headless,
        )

    async def create_context_and_page(
        self,
        proxy_route: Optional[ProxyRoute] = None,
    ) -> Tuple[Any, Any]:
        """Creates an isolated browser context with proxy and stealth injections."""
        context_kwargs: Dict[str, Any] = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "user_agent": self.config.user_agent,
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 37.7749, "longitude": -122.4194},
        }

        # Apply proxy if provided or available
        if proxy_route:
            context_kwargs["proxy"] = proxy_route.to_playwright_dict()
        elif self.proxy_manager and self.config.use_proxies:
            assigned_proxy = self.proxy_manager.get_next_proxy()
            if assigned_proxy:
                context_kwargs["proxy"] = assigned_proxy.to_playwright_dict()

        context = await self._browser.new_context(**context_kwargs)
        page = await context.new_page()

        # Block heavy map tile images, fonts, and media to speed up loads by 10x
        async def _block_heavy_assets(route):
            if route.request.resource_type in ["image", "media", "font"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", _block_heavy_assets)
        await page.add_init_script(STEALTH_INJECTION_JS)
        return context, page

    async def handle_consent_dialog(self, page: Any) -> None:
        """Dismisses Google cookie consent / terms modals if they appear."""
        try:
            consent_btn = page.locator("form[action*='consent.google.com'] button, button[aria-label*='Accept all']")
            if await consent_btn.count() > 0:
                await consent_btn.first.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

    async def check_and_solve_captcha(
        self,
        page: Any,
        proxy_url: Optional[str] = None,
    ) -> bool:
        """Checks if the page triggered a bot challenge and delegates to CapSolver."""
        if not self.captcha_handler or not self.captcha_handler.enabled:
            return False

        url = page.url
        title = await page.title()
        content = await page.content()

        if self.captcha_handler.is_challenge_page(url, title, content):
            logger.warning("Bot challenge detected on %s! Invoking CapSolver...", url)
            sitekey = self.captcha_handler.extract_sitekey(content, url)
            token = self.captcha_handler.solve_recaptcha(url, sitekey, proxy_url=proxy_url)
            if token:
                # Inject token into response field and submit
                await page.evaluate(
                    f"""(token) => {{
                        const responseEl = document.getElementById('g-recaptcha-response') || document.querySelector('textarea[name="g-recaptcha-response"]');
                        if (responseEl) {{
                            responseEl.value = token;
                            responseEl.innerHTML = token;
                            responseEl.style.display = 'block';
                        }}
                        const form = document.querySelector('form#captcha-form') || document.querySelector('form');
                        if (form) form.submit();
                    }}""",
                    token,
                )
                await page.wait_for_timeout(4000)
                return True
            return False
        return True

    async def scroll_feed_to_end(
        self,
        page: Any,
        max_results: int = 120,
    ) -> List[str]:
        """Smoothly scrolls the Google Maps results feed container to load all listings."""
        feed_selector = "div[role='feed']"
        try:
            await page.wait_for_selector(feed_selector, timeout=12000)
        except Exception:
            # If no feed found, might be a single result or zero results
            return []

        feed_locator = page.locator(feed_selector)
        card_selector = "div[role='feed'] > div > div[role='article'], div[role='feed'] a.hfpxzc"

        consecutive_no_growth = 0
        last_card_count = 0

        while True:
            cards = await page.locator(card_selector).count()
            if cards >= max_results:
                break

            # Scroll inside feed element
            await page.evaluate(
                """(selector) => {
                    const el = document.querySelector(selector);
                    if (el) {
                        el.scrollTop += 1200;
                    }
                }""",
                feed_selector,
            )

            # Random human-like micro delay
            delay = random.uniform(self.config.scroll_delay_min, self.config.scroll_delay_max)
            await asyncio.sleep(delay)

            # Check if end-of-list banner appears
            end_banner = page.locator("text=\"You've reached the end of the list.\"")
            if await end_banner.count() > 0:
                break

            current_cards = await page.locator(card_selector).count()
            if current_cards == last_card_count:
                consecutive_no_growth += 1
                if consecutive_no_growth >= self.config.max_scroll_attempts_without_growth:
                    break
            else:
                consecutive_no_growth = 0
                last_card_count = current_cards

        # Collect outerHTML of all discovered cards in a single atomic JS call (instant and timeout-proof)
        card_htmls: List[str] = await page.evaluate(
            """() => {
                const articles = Array.from(document.querySelectorAll("div[role='feed'] > div > div[role='article']"));
                if (articles.length > 0) {
                    return articles.map(el => el.outerHTML);
                }
                const links = Array.from(document.querySelectorAll("div[role='feed'] a.hfpxzc"));
                return links.map(el => {
                    const parent = el.closest("div[role='article']") || el.parentElement.parentElement;
                    return parent ? parent.outerHTML : el.outerHTML;
                });
            }"""
        )
        return card_htmls

    async def execute_search_on_page(
        self,
        page: Any,
        job: SearchJob,
        proxy_route: Optional[ProxyRoute] = None,
    ) -> List[Lead]:
        """Executes search on an existing persistent page, reusing HTTP/2 connections and cookies."""
        leads: List[Lead] = []

        if job.latitude is not None and job.longitude is not None:
            encoded_keyword = job.keyword.replace(" ", "+")
            url = f"https://www.google.com/maps/search/{encoded_keyword}/@{job.latitude},{job.longitude},{job.zoom_level}z"
        else:
            query = f"{job.keyword} in {job.location_name}".replace(" ", "+")
            url = f"https://www.google.com/maps/search/{query}"

        logger.info("Navigating to: %s", url)
        # Transient network retry loop
        max_nav_retries = 2
        for nav_attempt in range(max_nav_retries + 1):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.config.page_timeout_seconds * 1000)
                break
            except Exception as nav_err:
                if nav_attempt < max_nav_retries:
                    logger.warning("Transient error on navigation (%s), retrying attempt %d in 1.5s...", nav_err, nav_attempt + 1)
                    await asyncio.sleep(1.5)
                else:
                    raise nav_err

        await self.handle_consent_dialog(page)
        proxy_url = proxy_route.raw_url if proxy_route else None
        await self.check_and_solve_captcha(page, proxy_url=proxy_url)

        # Check if direct detail page loaded (single exact match)
        if "/maps/place/" in page.url:
            detail_html = await page.content()
            lead = GoogleMapsParser.parse_detail_page_html(
                detail_html,
                current_url=page.url,
                keyword=job.keyword,
                location=job.location_name,
            )
            if lead:
                leads.append(lead)
            return leads

        # Scroll through feed and extract card HTMLs
        card_htmls = await self.scroll_feed_to_end(page, max_results=self.config.max_results_per_query)
        logger.info("Found %d raw card items for job '%s'.", len(card_htmls), job.location_name)

        for html in card_htmls:
            lead = GoogleMapsParser.parse_card_element_html(
                html,
                keyword=job.keyword,
                location=job.location_name,
            )
            if lead:
                leads.append(lead)

        return leads

    async def execute_search_job(
        self,
        job: SearchJob,
        proxy_route: Optional[ProxyRoute] = None,
    ) -> List[Lead]:
        """Executes a single search job on a temporary context."""
        context, page = await self.create_context_and_page(proxy_route=proxy_route)
        try:
            return await self.execute_search_on_page(page, job, proxy_route=proxy_route)
        finally:
            await context.close()

    async def close(self) -> None:
        """Shuts down the browser instance."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
