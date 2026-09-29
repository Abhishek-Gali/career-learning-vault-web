"""Official AWS CLF-C02 Curriculum snapshot models."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.db.models.base import Base, TimestampMixin, utc_now


class CurriculumSnapshot(Base, TimestampMixin):
    """Historical snapshot of the AWS CLF-C02 official curriculum."""

    __tablename__ = "curriculum_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_code: Mapped[str] = mapped_column(String(50), default="CLF-C02", index=True)
    exam_name: Mapped[str] = mapped_column(String(255), default="AWS Certified Cloud Practitioner")
    guide_url: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    domains: Mapped[list["CurriculumDomain"]] = relationship("CurriculumDomain", back_populates="snapshot", cascade="all, delete-orphan")


class CurriculumDomain(Base):
    """Domain within a curriculum snapshot."""

    __tablename__ = "curriculum_domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("curriculum_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    domain_number: Mapped[int] = mapped_column(Integer, nullable=False)
    domain_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weighting: Mapped[float] = mapped_column(Float, nullable=False)  # e.g., 0.24

    snapshot: Mapped[CurriculumSnapshot] = relationship("CurriculumSnapshot", back_populates="domains")
    tasks: Mapped[list["CurriculumTask"]] = relationship("CurriculumTask", back_populates="domain", cascade="all, delete-orphan")


class CurriculumTask(Base):
    """Task statement within a curriculum domain."""

    __tablename__ = "curriculum_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("curriculum_domains.id", ondelete="CASCADE"), nullable=False, index=True)
    task_number: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., '1.1'
    task_statement: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_items: Mapped[list[str]] = mapped_column(JSON, default=list)

    domain: Mapped[CurriculumDomain] = relationship("CurriculumDomain", back_populates="tasks")
