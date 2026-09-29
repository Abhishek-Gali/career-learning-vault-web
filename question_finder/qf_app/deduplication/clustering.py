"""Cluster management for duplicate questions."""

from sqlalchemy.ext.asyncio import AsyncSession
from qf_app.db.models.question import Question
from qf_app.db.repositories.dedup_repo import DedupRepository
from qf_app.deduplication.canonical import CanonicalSelector


class ClusterManager:
    """Coordinates cluster assignment, member linking, and canonical election."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DedupRepository(session)
        self.selector = CanonicalSelector()

    async def assign_duplicate(
        self,
        new_question: Question,
        matched_question: Question,
        similarity_score: float,
        comparison_method: str,
    ) -> int:
        """Link a new question as a duplicate of an existing question or its cluster."""
        cluster_id = matched_question.duplicate_cluster_id

        if not cluster_id:
            # Create new cluster with matched question as initial canonical
            cluster = await self.repo.create_cluster(
                canonical_question_id=matched_question.id,
                selection_reason="FIRST_SEEN_CANONICAL",
            )
            cluster_id = cluster.id

        # Add duplicate to cluster
        await self.repo.add_duplicate_to_cluster(
            cluster_id=cluster_id,
            duplicate_question_id=new_question.id,
            similarity_score=similarity_score,
            comparison_method=comparison_method,
        )

        return cluster_id
