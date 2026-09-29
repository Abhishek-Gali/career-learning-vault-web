"""Robots.txt parser, cache, and compliance checker."""

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx
from qf_app.core.logging import get_logger

logger = get_logger(__name__)


class RobotsManager:
    """Manages and caches robots.txt rules per domain."""

    def __init__(self, user_agent: str = "CLF-C02-Researcher", timeout: float = 10.0) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache: dict[str, RobotFileParser] = {}

    async def is_allowed(self, url: str) -> bool:
        """Check if URL fetching is permitted by domain's robots.txt."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if not domain:
            return False

        if domain not in self._cache:
            parser = RobotFileParser()
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    resp = await client.get(robots_url)
                    if resp.status_code == 200:
                        parser.parse(resp.text.splitlines())
                    else:
                        # Allow by default if robots.txt is missing (404)
                        parser.allow_all = True
            except Exception as err:
                logger.debug("Failed to fetch robots.txt for %s (%s). Defaulting to allow.", domain, err)
                parser.allow_all = True

            self._cache[domain] = parser

        parser = self._cache[domain]
        return parser.can_fetch(self.user_agent, url)
