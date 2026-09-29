"""Async HTTP fetcher using HTTPX."""

import hashlib
from typing import Any
import httpx
from pydantic import BaseModel

from qf_app.core.exceptions import ContentTooLargeError, FetchError, RobotsDeniedError
from qf_app.core.logging import get_logger
from qf_app.fetching.cache import PageCacheManager
from qf_app.fetching.rate_limit import DomainRateLimiter
from qf_app.fetching.robots import RobotsManager
from qf_app.fetching.url import validate_url_security

logger = get_logger(__name__)


class FetchResult(BaseModel):
    """Normalized output from fetching a URL."""

    url: str
    final_url: str
    status_code: int
    content_type: str
    content_length: int
    content_hash: str
    etag: str | None = None
    last_modified: str | None = None
    body: str
    from_cache: bool = False


class HttpFetcher:
    """Robust async HTTP fetcher with caching, rate limiting, and size caps."""

    def __init__(
        self,
        timeout: float = 20.0,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB
        user_agent: str = "CLF-C02-Researcher/0.1 (educational-study-tool)",
        respect_robots: bool = True,
    ) -> None:
        self.timeout = timeout
        self.max_size_bytes = max_size_bytes
        self.user_agent = user_agent
        self.respect_robots = respect_robots

        self.cache = PageCacheManager()
        self.rate_limiter = DomainRateLimiter()
        self.robots = RobotsManager(user_agent=user_agent)

    async def fetch(self, url: str, force_refresh: bool = False) -> FetchResult:
        """Fetch URL with SSRF protection, robots compliance, and caching."""
        # 1. SSRF check
        validate_url_security(url)

        # 2. Check local disk cache
        if not force_refresh:
            cached = self.cache.get(url)
            if cached:
                return FetchResult(
                    url=url,
                    final_url=cached.url,
                    status_code=cached.status_code,
                    content_type=cached.content_type,
                    content_length=len(cached.body.encode("utf-8")),
                    content_hash=cached.content_hash,
                    etag=cached.etag,
                    last_modified=cached.last_modified,
                    body=cached.body,
                    from_cache=True,
                )

        # 3. Check robots.txt
        if self.respect_robots:
            allowed = await self.robots.is_allowed(url)
            if not allowed:
                raise RobotsDeniedError(f"Access to {url} prohibited by robots.txt")

        # 4. Enforce domain rate limit
        await self.rate_limiter.acquire(url)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=5,
                headers=headers,
            ) as client:
                resp = await client.get(url)

                # Check content length
                content_len = len(resp.content)
                if content_len > self.max_size_bytes:
                    raise ContentTooLargeError(
                        f"Page size ({content_len} bytes) exceeds limit ({self.max_size_bytes} bytes)"
                    )

                content_type = resp.headers.get("content-type", "text/html").split(";")[0].strip()
                body_text = resp.text

                # Store in cache
                header_dict = {k.lower(): v for k, v in resp.headers.items()}
                cached = self.cache.store(
                    url=url,
                    status_code=resp.status_code,
                    content_type=content_type,
                    headers=header_dict,
                    body=body_text,
                )

                return FetchResult(
                    url=url,
                    final_url=str(resp.url),
                    status_code=resp.status_code,
                    content_type=content_type,
                    content_length=content_len,
                    content_hash=cached.content_hash,
                    etag=cached.etag,
                    last_modified=cached.last_modified,
                    body=body_text,
                    from_cache=False,
                )
        except (RobotsDeniedError, ContentTooLargeError):
            raise
        except Exception as err:
            logger.warning("HTTP fetch failed for %s: %s", url, err)
            raise FetchError(f"Fetch failed for {url}: {err}") from err
