"""Optional local SearXNG search engine provider."""

from urllib.parse import urlparse
import httpx
from qf_app.core.logging import get_logger
from qf_app.discovery.providers.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class SearXNGProvider(SearchProvider):
    """Integrates with local or configured SearXNG JSON search API."""

    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Query SearXNG JSON search endpoint."""
        results: list[SearchResult] = []
        search_url = f"{self.base_url}/search"
        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "safesearch": "0",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(search_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_items = data.get("results", [])[:limit]
                    for item in raw_items:
                        url = item.get("url", "")
                        if url and (url.startswith("http://") or url.startswith("https://")):
                            domain = urlparse(url).netloc.lower()
                            results.append(
                                SearchResult(
                                    url=url,
                                    title=item.get("title", ""),
                                    snippet=item.get("content", ""),
                                    provider="SEARXNG",
                                    query=query,
                                    domain=domain,
                                    relevance_score=item.get("score", 1.0),
                                )
                            )
        except Exception as err:
            logger.debug("SearXNG search query '%s' skipped or unavailable: %s", query, err)

        return results
