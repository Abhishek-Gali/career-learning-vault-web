"""Repository for Verification Records."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.db.models.verification import VerificationRecord


class VerificationRepository:
    """Manages answer verification evidence records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_verification(
        self,
        question_id: int,
        source_url: str,
        supporting_text_summary: str,
        source_title: str = "Official AWS Documentation",
        evidence_type: str = "OFFICIAL_AWS_DOCS",
        verification_method: str = "EXACT_DOC_MATCH",
        status: str = "VERIFIED",
        confidence: float = 1.0,
    ) -> VerificationRecord:
        """Add authoritative evidence record for a question."""
        record = VerificationRecord(
            question_id=question_id,
            source_url=source_url,
            source_title=source_title,
            supporting_text_summary=supporting_text_summary,
            evidence_type=evidence_type,
            verification_method=verification_method,
            status=status,
            confidence=confidence,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_by_question_id(self, question_id: int) -> list[VerificationRecord]:
        """Fetch all verification evidence records for a question."""
        stmt = select(VerificationRecord).where(VerificationRecord.question_id == question_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
