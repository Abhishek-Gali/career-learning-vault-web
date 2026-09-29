"""XML Sitemap discovery provider."""

from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx
from qf_app.core.logging import get_logger
from qf_app.discovery.providers.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class SitemapProvider(SearchProvider):
    """Discovers practice question URLs from XML sitemaps."""

    def __init__(self, sitemap_urls: list[str] | None = None, timeout: float = 15.0) -> None:
        self.sitemap_urls = sitemap_urls or []
        self.timeout = timeout

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Fetch and parse XML sitemaps for relevant URLs."""
        results: list[SearchResult] = []
        if not self.sitemap_urls:
            return results

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for sitemap_url in self.sitemap_urls:
                try:
                    resp = await client.get(sitemap_url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.content, "xml")
                        loc_tags = soup.find_all("loc")
                        for loc in loc_tags[:limit]:
                            url = loc.get_text(strip=True)
                            if "clf" in url.lower() or "cloud-practitioner" in url.lower() or "aws" in url.lower():
                                domain = urlparse(url).netloc.lower()
                                results.append(
                                    SearchResult(
                                        url=url,
                                        title="Sitemap Discovered Page",
                                        snippet=f"Discovered via {sitemap_url}",
                                        provider="SITEMAP",
                                        query=query,
                                        domain=domain,
                                        relevance_score=0.85,
                                    )
                                )
                                if len(results) >= limit:
                                    return results
                except Exception as err:
                    logger.debug("Error parsing sitemap %s: %s", sitemap_url, err)

        return results
