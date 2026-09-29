"""Direct source registry crawler provider."""

from urllib.parse import urljoin, urlparse
from qf_app.config.settings import get_sources_data
from qf_app.discovery.providers.base import SearchProvider, SearchResult


class DirectSourceProvider(SearchProvider):
    """Generates search candidate URLs directly from configured source roots."""

    def __init__(self, sources: list[dict] | None = None) -> None:
        self.sources = sources or get_sources_data()

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Generate candidate endpoints matching the query domain from configured sources."""
        results: list[SearchResult] = []

        for src in self.sources:
            if not src.get("enabled", True):
                continue
            domain = src.get("domain", "")
            for path in src.get("allowed_paths", []):
                full_url = urljoin(f"https://{domain}", path)
                results.append(
                    SearchResult(
                        url=full_url,
                        title=src.get("name", domain),
                        snippet=f"Registered source practice path: {path}",
                        provider="DIRECT_SOURCE",
                        query=query,
                        domain=domain,
                        relevance_score=float(src.get("priority", 50)) / 100.0,
                    )
                )
                if len(results) >= limit:
                    return results

        return results
