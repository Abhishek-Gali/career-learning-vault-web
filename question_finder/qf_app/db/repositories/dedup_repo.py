"""Repository for Duplicate Clusters and Members."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.db.models.dedup import DuplicateCluster, DuplicateMember
from qf_app.db.models.question import Question


class DedupRepository:
    """Manages duplicate clustering and canonical question linkage."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_cluster(
        self,
        canonical_question_id: int,
        selection_reason: str = "INITIAL_CANONICAL",
    ) -> DuplicateCluster:
        """Create new duplicate cluster."""
        cluster = DuplicateCluster(
            canonical_question_id=canonical_question_id,
            cluster_size=1,
            selection_reason=selection_reason,
        )
        self.session.add(cluster)
        await self.session.flush()

        member = DuplicateMember(
            cluster_id=cluster.id,
            question_id=canonical_question_id,
            similarity_score=1.0,
            comparison_method="CANONICAL_SELF",
        )
        self.session.add(member)

        # Update question cluster link
        question = await self.session.get(Question, canonical_question_id)
        if question:
            question.duplicate_cluster_id = cluster.id
            question.is_canonical = True

        await self.session.commit()
        await self.session.refresh(cluster)
        return cluster

    async def add_duplicate_to_cluster(
        self,
        cluster_id: int,
        duplicate_question_id: int,
        similarity_score: float = 1.0,
        comparison_method: str = "EXACT_HASH",
    ) -> DuplicateMember:
        """Add duplicate question to an existing cluster."""
        member = DuplicateMember(
            cluster_id=cluster_id,
            question_id=duplicate_question_id,
            similarity_score=similarity_score,
            comparison_method=comparison_method,
        )
        self.session.add(member)

        cluster = await self.session.get(DuplicateCluster, cluster_id)
        if cluster:
            cluster.cluster_size += 1

        question = await self.session.get(Question, duplicate_question_id)
        if question:
            question.duplicate_cluster_id = cluster_id
            question.is_canonical = False

        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_cluster_with_members(self, cluster_id: int) -> DuplicateCluster | None:
        """Fetch cluster and all its member questions."""
        stmt = (
            select(DuplicateCluster)
            .where(DuplicateCluster.id == cluster_id)
            .options(selectinload(DuplicateCluster.members))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
