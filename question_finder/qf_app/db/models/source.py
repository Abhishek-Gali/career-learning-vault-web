"""Source registries, crawled pages, and content snapshots models."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.core.types import DateConfidence, SourceTier
from qf_app.db.models.base import Base, TimestampMixin, utc_now


class Source(Base, TimestampMixin):
    """Registered domain and source provider."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), default=SourceTier.UNVERIFIED.value, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    requires_login: Mapped[bool] = mapped_column(Boolean, default=False)
    robots_policy: Mapped[str] = mapped_column(String(50), default="RESPECT")
    rate_limit: Mapped[float] = mapped_column(Float, default=1.5)
    license_info: Mapped[str] = mapped_column(String(255), default="Educational Reference")
    notes: Mapped[str] = mapped_column(Text, default="")

    # Health & Yield metrics
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    http_success_rate: Mapped[float] = mapped_column(Float, default=1.0)
    question_yield: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rate: Mapped[float] = mapped_column(Float, default=0.0)
    verification_success_rate: Mapped[float] = mapped_column(Float, default=0.0)

    pages: Mapped[list["SourcePage"]] = relationship("SourcePage", back_populates="source", cascade="all, delete-orphan")


class SourcePage(Base, TimestampMixin):
    """Unique discovered web page under a source."""

    __tablename__ = "source_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="")
    content_type: Mapped[str] = mapped_column(String(100), default="text/html")
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    date_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_confidence: Mapped[str] = mapped_column(String(30), default=DateConfidence.UNKNOWN.value)
    status: Mapped[str] = mapped_column(String(50), default="FETCHED", index=True)

    source: Mapped[Source | None] = relationship("Source", back_populates="pages")
    snapshots: Mapped[list["SourceSnapshot"]] = relationship("SourceSnapshot", back_populates="page", cascade="all, delete-orphan")


class SourceSnapshot(Base):
    """Historical point-in-time snapshot of fetched page contents."""

    __tablename__ = "source_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    content_length: Mapped[int] = mapped_column(Integer, default=0)

    page: Mapped[SourcePage] = relationship("SourcePage", back_populates="snapshots")
