"""Dataset statistics calculator."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from qf_app.core.types import AnswerStatus, QuestionStatus, RecentnessStatus, SourceKind
from qf_app.db.models.question import Question


class DatasetStatsCalculator:
    """Calculates dataset breakdown numbers for dashboards and reports."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary_stats(self) -> dict:
        """Compute full statistical summary of all questions."""
        stmt = select(
            func.count(Question.id).label("total"),
            func.count(Question.id).filter(
                Question.source_kind == SourceKind.PUBLIC_PRACTICE.value,
                Question.recentness_status.in_([RecentnessStatus.RECENT_PUBLISHED.value, RecentnessStatus.RECENT_UPDATED.value]),
                Question.is_canonical == True,
            ).label("recent_source"),
            func.count(Question.id).filter(Question.source_kind == SourceKind.GENERATED_PRACTICE.value).label("generated"),
            func.count(Question.id).filter(Question.recentness_status == RecentnessStatus.OLDER.value).label("older"),
            func.count(Question.id).filter(Question.recentness_status == RecentnessStatus.LEGACY.value).label("legacy"),
            func.count(Question.id).filter(Question.status == QuestionStatus.QUARANTINED.value).label("quarantined"),
            func.count(Question.id).filter(Question.is_canonical == False).label("duplicates"),
            func.count(Question.id).filter(Question.answer_status == AnswerStatus.VERIFIED.value).label("verified"),
            func.count(Question.id).filter(Question.answer_status == AnswerStatus.PARTIALLY_VERIFIED.value).label("partial_verified"),
            func.count(Question.id).filter(Question.answer_status == AnswerStatus.CONFLICTING.value).label("conflicting"),
        )
        row = (await self.session.execute(stmt)).one()

        # Domain breakdown
        domain_stmt = select(Question.domain, func.count(Question.id)).group_by(Question.domain)
        domain_rows = (await self.session.execute(domain_stmt)).fetchall()
        domain_counts = {r[0] or 0: r[1] for r in domain_rows}

        return {
            "total_study_questions": (row.recent_source or 0) + (row.generated or 0) + (row.older or 0),
            "recent_source_questions": row.recent_source or 0,
            "generated_practice_questions": row.generated or 0,
            "older_questions": row.older or 0,
            "legacy_clf_c01": row.legacy or 0,
            "quarantined_questions": row.quarantined or 0,
            "duplicate_questions": row.duplicates or 0,
            "verified_questions": row.verified or 0,
            "partially_verified_questions": row.partial_verified or 0,
            "conflicting_questions": row.conflicting or 0,
            "domain_counts": domain_counts,
        }
