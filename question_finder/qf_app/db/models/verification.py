"""Answer verification records model."""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.core.types import AnswerStatus
from qf_app.db.models.base import Base, TimestampMixin, utc_now


class VerificationRecord(Base, TimestampMixin):
    """Authoritative evidence verifying a question's correct answer."""

    __tablename__ = "verification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str] = mapped_column(String(500), default="Official AWS Documentation")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    supporting_text_summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), default="OFFICIAL_AWS_DOCS")
    verification_method: Mapped[str] = mapped_column(String(50), default="EXACT_DOC_MATCH")
    status: Mapped[str] = mapped_column(String(30), default=AnswerStatus.VERIFIED.value, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    question: Mapped["Question"] = relationship("Question", back_populates="verifications")
