"""Curriculum syllabus coverage analyzer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from qf_app.db.models.question import Question

OFFICIAL_WEIGHTS = {
    1: {"name": "Cloud Concepts", "target_pct": 24.0},
    2: {"name": "Security and Compliance", "target_pct": 30.0},
    3: {"name": "Cloud Technology and Services", "target_pct": 34.0},
    4: {"name": "Billing, Pricing, and Support", "target_pct": 12.0},
}


class CoverageAnalyzer:
    """Analyzes domain and task statement distribution against official syllabus weights."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_domain_coverage(self) -> list[dict]:
        """Compute actual vs. target distribution for each domain."""
        stmt = (
            select(Question.domain, func.count(Question.id))
            .where(Question.domain.isnot(None))
            .group_by(Question.domain)
        )
        rows = (await self.session.execute(stmt)).fetchall()
        counts_by_domain = {r[0]: r[1] for r in rows}
        total_questions = sum(counts_by_domain.values()) or 1

        coverage_report = []
        for domain_num, meta in OFFICIAL_WEIGHTS.items():
            actual_count = counts_by_domain.get(domain_num, 0)
            actual_pct = (actual_count / total_questions) * 100.0
            coverage_report.append(
                {
                    "domain_number": domain_num,
                    "domain_name": meta["name"],
                    "target_percentage": meta["target_pct"],
                    "actual_count": actual_count,
                    "actual_percentage": round(actual_pct, 1),
                    "coverage_delta": round(actual_pct - meta["target_pct"], 1),
                }
            )

        return coverage_report
