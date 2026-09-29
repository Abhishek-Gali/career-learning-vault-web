"""Candidate URL pipeline and queue management."""

from sqlalchemy.ext.asyncio import AsyncSession
from qf_app.core.logging import get_logger
from qf_app.db.models.research import SearchCandidate
from qf_app.db.repositories.candidate_repo import CandidateRepository
from qf_app.discovery.providers.base import SearchResult
from qf_app.fetching.url import normalize_url

logger = get_logger(__name__)


class CandidateManager:
    """Manages the discovery, normalization, and queuing of search candidate URLs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CandidateRepository(session)

    async def ingest_search_results(
        self,
        run_id: int | None,
        results: list[SearchResult],
    ) -> int:
        """Process and register a batch of search results."""
        added_count = 0
        for r in results:
            canonical = normalize_url(r.url)
            candidate = await self.repo.create_candidate(
                run_id=run_id,
                query=r.query,
                url=r.url,
                canonical_url=canonical,
                title=r.title,
                snippet=r.snippet,
                search_provider=r.provider,
                domain=r.domain,
                relevance_score=r.relevance_score,
            )
            if candidate:
                added_count += 1

        logger.info("Ingested %d new candidate URLs from batch of %d results.", added_count, len(results))
        return added_count

    async def get_next_candidates(self, limit: int = 50) -> list[SearchCandidate]:
        """Fetch queued candidates ready for fetching."""
        return await self.repo.list_pending_candidates(limit=limit)
