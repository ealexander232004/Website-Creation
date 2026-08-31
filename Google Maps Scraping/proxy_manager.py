"""Proxy pool management and rotation for Playwright and HTTP engines.

Loads proxy routes from Oxylabs static ISP bundle, environment variables,
or custom files, and provides health-checked round-robin rotation, exponential
backoff, and a global circuit breaker to protect proxy reputation.
"""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse

logger = logging.getLogger("gmaps_scraper.proxy_manager")


@dataclass
class ProxyRoute:
    """A single proxy endpoint route with health metrics and backoff state."""
    raw_url: str
    scheme: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_failure_time: float = 0.0
    cooldown_until: float = 0.0

    @classmethod
    def from_url(cls, url: str) -> "ProxyRoute":
        url = url.strip()
        parsed = urlparse(url)
        
        username = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        return cls(
            raw_url=url,
            scheme=parsed.scheme or "http",
            host=host,
            port=port,
            username=username,
            password=password,
        )

    def to_playwright_dict(self) -> Dict[str, str]:
        """Converts route to Playwright browser launch proxy dictionary."""
        proxy_dict: Dict[str, str] = {
            "server": f"{self.scheme}://{self.host}:{self.port}",
        }
        if self.username:
            proxy_dict["username"] = self.username
        if self.password:
            proxy_dict["password"] = self.password
        return proxy_dict

    def is_available(self) -> bool:
        """Returns True if proxy is not currently cooling down from a block/ban."""
        return time.time() >= self.cooldown_until

    def mark_success(self) -> None:
        self.success_count += 1
        self.consecutive_failures = 0

    def mark_failure(self, base_cooldown: float = 30.0) -> float:
        """Applies exponential cooldown backoff based on consecutive failures."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        
        # Exponential backoff: 30s, 60s, 120s, max 300s (5 min)
        cooldown = min(300.0, base_cooldown * (2 ** max(0, self.consecutive_failures - 1)))
        self.cooldown_until = time.time() + cooldown
        logger.warning(
            "Proxy %s:%d failed (%d in a row). Cooling down for %.1fs.",
            self.host,
            self.port,
            self.consecutive_failures,
            cooldown,
        )
        return cooldown


class ProxyManager:
    """Thread-safe proxy pool manager providing round-robin selection, worker-proxy mapping, and circuit breaker."""

    def __init__(
        self,
        proxy_urls_file: Optional[Path] = None,
        custom_urls: Optional[List[str]] = None,
        global_failure_threshold: int = 8,
    ) -> None:
        self._lock = threading.Lock()
        self._routes: List[ProxyRoute] = []
        self._index: int = 0
        self.global_consecutive_failures: int = 0
        self.global_failure_threshold = global_failure_threshold
        self.circuit_open_until: float = 0.0

        # 1. Load from provided custom list
        if custom_urls:
            for url in custom_urls:
                if url.strip():
                    self._routes.append(ProxyRoute.from_url(url))

        # 2. Load from proxy-urls.txt or file
        if not self._routes and proxy_urls_file and Path(proxy_urls_file).is_file():
            self._load_from_file(Path(proxy_urls_file))

        # 3. Load from environment variable STATIC_ISP_PROXY_URLS / STATIC_ISP_PROXY_URL
        if not self._routes:
            env_urls = os.getenv("STATIC_ISP_PROXY_URLS")
            if env_urls:
                for url in env_urls.split(","):
                    if url.strip():
                        self._routes.append(ProxyRoute.from_url(url.strip()))
            else:
                single_url = os.getenv("STATIC_ISP_PROXY_URL") or os.getenv("HTTP_PROXY")
                if single_url:
                    self._routes.append(ProxyRoute.from_url(single_url.strip()))

        logger.info("Initialized ProxyManager with %d available proxy routes.", len(self._routes))

    def _load_from_file(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        self._routes.append(ProxyRoute.from_url(line))
                    except Exception as e:
                        logger.warning("Failed to parse proxy line: %s (%s)", line, e)

    @property
    def total_proxies(self) -> int:
        return len(self._routes)

    def is_circuit_tripped(self) -> bool:
        """Returns True if the entire scraper should pause to protect proxy reputation."""
        with self._lock:
            return time.time() < self.circuit_open_until

    def trip_circuit_breaker(self, pause_seconds: float = 60.0) -> None:
        """Opens global circuit breaker to halt scraping and protect proxy pool reputation."""
        with self._lock:
            self.circuit_open_until = time.time() + pause_seconds
            logger.critical(
                "GLOBAL CIRCUIT BREAKER TRIPPED! Consecutive failures (%d) reached threshold. Pausing all workers for %.1fs.",
                self.global_consecutive_failures,
                pause_seconds,
            )

    def record_global_success(self) -> None:
        with self._lock:
            self.global_consecutive_failures = 0

    def record_global_failure(self) -> None:
        with self._lock:
            self.global_consecutive_failures += 1
            if self.global_consecutive_failures >= self.global_failure_threshold:
                self.trip_circuit_breaker(pause_seconds=90.0)

    def get_route_for_worker(self, worker_id: int) -> Optional[ProxyRoute]:
        """Maps a worker ID (1-indexed) directly to its dedicated proxy route."""
        with self._lock:
            if not self._routes:
                return None
            idx = (worker_id - 1) % len(self._routes)
            return self._routes[idx]

    def get_next_proxy(self) -> Optional[ProxyRoute]:
        """Returns the next available proxy route in round-robin sequence."""
        with self._lock:
            if not self._routes:
                return None

            for _ in range(len(self._routes)):
                route = self._routes[self._index % len(self._routes)]
                self._index += 1
                if route.is_available():
                    return route

            return min(self._routes, key=lambda r: r.failure_count)
