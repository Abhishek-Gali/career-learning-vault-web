"""Audit trails and rejection records models."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from qf_app.db.models.base import Base, utc_now


class AuditLog(Base):
    """Audit log tracking all major dataset changes and curation decisions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'QUESTION', 'SOURCE', 'CLUSTER'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'ACCEPT', 'REJECT', 'MERGE', 'VERIFY'
    decision: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    component: Mapped[str] = mapped_column(String(50), default="PIPELINE")
    version: Mapped[str] = mapped_column(String(20), default="0.1.0")


class RejectionRecord(Base):
    """Record of rejected candidate URLs or malformed questions."""

    __tablename__ = "rejection_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'PAGE', 'QUESTION'
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    evidence: Mapped[str] = mapped_column(Text, default="")
    rejected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    component: Mapped[str] = mapped_column(String(50), default="VALIDATOR")
