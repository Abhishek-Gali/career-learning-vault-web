"""Research runs and search candidates models."""

import uuid
from datetime import date, datetime
from typing import Any
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.core.types import CandidateStatus
from qf_app.db.models.base import Base, TimestampMixin, utc_now


class ResearchRun(Base, TimestampMixin):
    """Tracks research runs and pipeline executions."""

    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="RUNNING", index=True)
    window_start: Mapped[date] = mapped_column(Date, nullable=False)
    window_end: Mapped[date] = mapped_column(Date, nullable=False)
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    stats_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    candidates: Mapped[list["SearchCandidate"]] = relationship("SearchCandidate", back_populates="run", cascade="all, delete-orphan")


class SearchCandidate(Base, TimestampMixin):
    """Tracks discovered candidate search URLs."""

    __tablename__ = "search_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    search_provider: Mapped[str] = mapped_column(String(50), default="DIRECT", index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    estimated_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=CandidateStatus.NEW.value, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[ResearchRun | None] = relationship("ResearchRun", back_populates="candidates")
