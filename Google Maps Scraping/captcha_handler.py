"""CapSolver Integration and Google Bot Challenge Handler.

Detects and resolves Google reCAPTCHA / bot challenge pages using the
provided CapSolver client bundle.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Dynamically link the sibling Captcha Solver bundle
BASE_DIR = Path(__file__).resolve().parent
CAPTCHA_SOLVER_DIR = BASE_DIR.parent / "Captcha Solver"

if str(CAPTCHA_SOLVER_DIR) not in sys.path and CAPTCHA_SOLVER_DIR.is_dir():
    sys.path.insert(0, str(CAPTCHA_SOLVER_DIR))

try:
    from capsolver_client import CapSolverClient, CapSolverError, recaptcha_v2_task
    CAPSOLVER_AVAILABLE = True
except ImportError:
    CAPSOLVER_AVAILABLE = False

logger = logging.getLogger("gmaps_scraper.captcha")

# Known fallback Google sorry page sitekey
DEFAULT_GOOGLE_SITEKEY = "6LfwuyUTAAAAAOAmoS0fdqijDnHHifav7ujJgauto"


class CaptchaHandler:
    """Manages automated detection and solving of Google bot challenge gates."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client: Optional[CapSolverClient] = None
        self.enabled: bool = False

        if not CAPSOLVER_AVAILABLE:
            logger.warning("CapSolver module not found in sibling directory. Captcha solving disabled.")
            return

        try:
            if api_key:
                self.client = CapSolverClient(api_key=api_key)
            elif (CAPTCHA_SOLVER_DIR / "capsolver.env").is_file():
                self.client = CapSolverClient.from_env_file(CAPTCHA_SOLVER_DIR / "capsolver.env")
            else:
                self.client = CapSolverClient.from_environment()

            self.enabled = True
            logger.info("CapSolver integration enabled successfully.")
        except Exception as e:
            logger.info("CapSolver client not initialized: %s", e)

    def check_balance(self) -> float:
        """Retrieves remaining CapSolver credit balance in USD."""
        if not self.enabled or not self.client:
            return 0.0
        try:
            return self.client.get_balance()
        except Exception as e:
            logger.error("Failed to check CapSolver balance: %s", e)
            return 0.0

    def is_challenge_page(self, page_url: str, page_title: str, page_content: str) -> bool:
        """Determines if the browser is stuck on a Google CAPTCHA / bot gate."""
        url_lower = page_url.lower()
        title_lower = page_title.lower()
        content_lower = page_content.lower()

        indicators = [
            "/sorry/index" in url_lower,
            "google.com/sorry" in url_lower,
            "unusual traffic from your computer network" in content_lower,
            "our systems have detected unusual traffic" in content_lower,
            "please solve the challenge below" in content_lower,
            ("recaptcha" in content_lower and "g-recaptcha" in content_lower),
            "robot or human" in title_lower,
        ]
        return any(indicators)

    def extract_sitekey(self, page_content: str, page_url: str) -> str:
        """Extracts the reCAPTCHA sitekey from the page DOM or returns default."""
        # 1. Check data-sitekey attribute
        match = re.search(r'data-sitekey=["\']([a-zA-Z0-9_-]+)["\']', page_content)
        if match:
            return match.group(1)

        # 2. Check iframe or script src k= parameter
        k_match = re.search(r'[?&]k=([a-zA-Z0-9_-]+)', page_content)
        if k_match:
            return k_match.group(1)

        # 3. Check recaptcha.render calls
        render_match = re.search(r'sitekey["\']?\s*:\s*["\']([a-zA-Z0-9_-]+)["\']', page_content)
        if render_match:
            return render_match.group(1)

        return DEFAULT_GOOGLE_SITEKEY

    def solve_recaptcha(
        self,
        website_url: str,
        site_key: str,
        proxy_url: Optional[str] = None,
        enterprise: bool = False,
    ) -> Optional[str]:
        """Submits a reCAPTCHA challenge to CapSolver and waits for the solution token."""
        if not self.enabled or not self.client:
            logger.warning("Captcha encountered but CapSolver is not configured.")
            return None

        try:
            logger.info("Submitting reCAPTCHA challenge to CapSolver (sitekey: %s) for URL: %s", site_key, website_url)
            task_payload = recaptcha_v2_task(
                website_url=website_url,
                website_key=site_key,
                proxy=proxy_url,
                enterprise=enterprise,
            )
            result = self.client.solve(task_payload, poll_timeout=120)
            solution = result.get("solution", {})
            token = solution.get("gRecaptchaResponse")
            if token:
                logger.info("Successfully solved Google CAPTCHA via CapSolver.")
                return token
            logger.error("CapSolver returned empty solution token.")
            return None
        except Exception as e:
            logger.error("Failed solving CAPTCHA via CapSolver: %s", e)
            return None
