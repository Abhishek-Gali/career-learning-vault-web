"""Question models, options, sources, topics, and service mappings."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.core.types import (
    AnswerStatus,
    DateConfidence,
    KnowledgeStatus,
    QuestionStatus,
    QuestionType,
    RecentnessStatus,
    SourceKind,
)
from qf_app.db.models.base import Base, TimestampMixin, utc_now


class Question(Base, TimestampMixin):
    """Core question entity."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), default=QuestionType.SINGLE_CHOICE.value, index=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default=QuestionStatus.ACCEPTED.value, index=True)
    source_kind: Mapped[str] = mapped_column(String(30), default=SourceKind.PUBLIC_PRACTICE.value, index=True)

    # Curriculum mapping
    domain: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    domain_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    task_statement: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="INTERMEDIATE")
    classification_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    classification_method: Mapped[str] = mapped_column(String(50), default="TAXONOMY_RULES")

    # Dates and Recency
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    date_confidence: Mapped[str] = mapped_column(String(30), default=DateConfidence.UNKNOWN.value)
    recentness_status: Mapped[str] = mapped_column(String(30), default=RecentnessStatus.UNKNOWN_DATE.value, index=True)

    # Verification & Knowledge Status
    answer_status: Mapped[str] = mapped_column(String(30), default=AnswerStatus.UNVERIFIED.value, index=True)
    answer_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_status: Mapped[str] = mapped_column(String(30), default=KnowledgeStatus.CURRENT.value)
    knowledge_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Quality & Deduplication
    quality_score: Mapped[float] = mapped_column(Float, default=70.0)
    exact_hash: Mapped[str] = mapped_column(String(64), index=True)
    stem_hash: Mapped[str] = mapped_column(String(64), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    duplicate_cluster_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("duplicate_clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    is_canonical: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Generated Practice fields
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    generation_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    options: Mapped[list["QuestionOption"]] = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.normalized_position")
    sources: Mapped[list["QuestionSource"]] = relationship("QuestionSource", back_populates="question", cascade="all, delete-orphan")
    topics: Mapped[list["QuestionTopic"]] = relationship("QuestionTopic", back_populates="question", cascade="all, delete-orphan")
    services: Mapped[list["QuestionService"]] = relationship("QuestionService", back_populates="question", cascade="all, delete-orphan")
    verifications: Mapped[list["VerificationRecord"]] = relationship("VerificationRecord", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    """Normalized options belonging to a question."""

    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_key: Mapped[str] = mapped_column(String(10), nullable=False)  # 'A', 'B', 'C', 'D'
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    original_position: Mapped[int] = mapped_column(Integer, default=0)
    normalized_position: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[Question] = relationship("Question", back_populates="options")


class QuestionSource(Base):
    """Provenance tracking for a question's discovery source."""

    __tablename__ = "question_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("source_pages.id", ondelete="SET NULL"), nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str] = mapped_column(String(500), default="")
    extraction_method: Mapped[str] = mapped_column(String(50), default="DOM_HEURISTICS")
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    question_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    question: Mapped[Question] = relationship("Question", back_populates="sources")


class QuestionTopic(Base):
    """Topic tag associated with a question."""

    __tablename__ = "question_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    question: Mapped[Question] = relationship("Question", back_populates="topics")


class QuestionService(Base):
    """In-scope AWS service referenced in a question."""

    __tablename__ = "question_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    question: Mapped[Question] = relationship("Question", back_populates="services")
