"""Abstract base class for search and candidate discovery providers."""

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Normalized search discovery candidate item."""

    url: str
    title: str = ""
    snippet: str = ""
    provider: str = "DIRECT"
    query: str = ""
    domain: str = ""
    relevance_score: float = 1.0


class SearchProvider(ABC):
    """Abstract interface for discovery providers."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Execute discovery search for a given query string."""
        pass
