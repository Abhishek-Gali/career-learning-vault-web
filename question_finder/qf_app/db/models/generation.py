"""Generated practice question metadata model."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from qf_app.db.models.base import Base, TimestampMixin, utc_now


class GeneratedQuestionMeta(Base, TimestampMixin):
    """Metadata tracking for generated practice questions."""

    __tablename__ = "generated_question_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), unique=True, index=True)
    template_family: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    supporting_aws_sources: Mapped[list[str]] = mapped_column(JSON, default=list)
    generation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    validation_notes: Mapped[str] = mapped_column(Text, default="PASSED_DETERMINISTIC_RULES")
