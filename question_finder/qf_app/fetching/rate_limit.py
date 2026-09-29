"""Per-domain async rate limiter."""

import asyncio
import time
from urllib.parse import urlparse


class DomainRateLimiter:
    """Enforces minimum delays between requests to the same origin domain."""

    def __init__(self, default_delay: float = 1.5) -> None:
        self.default_delay = default_delay
        self._last_request_time: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_lock(self, domain: str) -> asyncio.Lock:
        async with self._global_lock:
            if domain not in self._locks:
                self._locks[domain] = asyncio.Lock()
            return self._locks[domain]

    async def acquire(self, url_or_domain: str, custom_delay: float | None = None) -> None:
        """Wait until enough time has elapsed since last request to domain."""
        if "://" in url_or_domain:
            domain = urlparse(url_or_domain).netloc.lower()
        else:
            domain = url_or_domain.lower()

        delay = custom_delay if custom_delay is not None else self.default_delay
        lock = await self._get_lock(domain)

        async with lock:
            last_time = self._last_request_time.get(domain, 0.0)
            elapsed = time.time() - last_time
            if elapsed < delay:
                wait_time = delay - elapsed
                await asyncio.sleep(wait_time)
            self._last_request_time[domain] = time.time()
