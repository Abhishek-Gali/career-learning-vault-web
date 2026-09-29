"""Repository for SearchCandidates and ResearchRuns."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.core.types import CandidateStatus
from qf_app.db.models.research import ResearchRun, SearchCandidate


class CandidateRepository:
    """Manages search candidates and research run states."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_candidate(
        self,
        run_id: int | None,
        query: str,
        url: str,
        canonical_url: str,
        title: str = "",
        snippet: str = "",
        search_provider: str = "DIRECT",
        domain: str = "",
        relevance_score: float = 1.0,
    ) -> SearchCandidate | None:
        """Create new search candidate if not already recorded."""
        stmt = select(SearchCandidate).where(SearchCandidate.canonical_url == canonical_url)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return None

        candidate = SearchCandidate(
            run_id=run_id,
            query=query,
            url=url,
            canonical_url=canonical_url,
            title=title,
            snippet=snippet,
            search_provider=search_provider,
            domain=domain,
            relevance_score=relevance_score,
            status=CandidateStatus.NEW.value,
        )
        self.session.add(candidate)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def list_pending_candidates(self, limit: int = 100) -> list[SearchCandidate]:
        """Fetch candidates waiting to be fetched."""
        stmt = (
            select(SearchCandidate)
            .where(SearchCandidate.status.in_([CandidateStatus.NEW.value, CandidateStatus.QUEUED.value]))
            .order_by(SearchCandidate.relevance_score.desc(), SearchCandidate.id.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_candidate_status(
        self,
        candidate_id: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Update candidate processing state."""
        candidate = await self.session.get(SearchCandidate, candidate_id)
        if candidate:
            candidate.status = status
            candidate.error_message = error_message
            await self.session.commit()
