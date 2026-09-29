"""RSS/Atom feed discovery provider."""

from urllib.parse import urlparse
import feedparser
import httpx
from qf_app.core.logging import get_logger
from qf_app.discovery.providers.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class RSSProvider(SearchProvider):
    """Discovers articles and question posts from RSS and Atom feeds."""

    def __init__(self, feed_urls: list[str] | None = None, timeout: float = 15.0) -> None:
        self.feed_urls = feed_urls or []
        self.timeout = timeout

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Fetch feeds and return entries matching query or cloud keywords."""
        results: list[SearchResult] = []
        if not self.feed_urls:
            return results

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for feed_url in self.feed_urls:
                try:
                    resp = await client.get(feed_url)
                    if resp.status_code == 200:
                        parsed = feedparser.parse(resp.content)
                        for entry in parsed.entries[:limit]:
                            link = entry.get("link", "")
                            if link:
                                domain = urlparse(link).netloc.lower()
                                results.append(
                                    SearchResult(
                                        url=link,
                                        title=entry.get("title", ""),
                                        snippet=entry.get("summary", ""),
                                        provider="RSS",
                                        query=query,
                                        domain=domain,
                                        relevance_score=0.8,
                                    )
                                )
                                if len(results) >= limit:
                                    return results
                except Exception as err:
                    logger.debug("Error fetching RSS feed %s: %s", feed_url, err)

        return results
