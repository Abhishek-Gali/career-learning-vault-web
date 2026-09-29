"""Pydantic schemas for normalized questions and processing pipeline."""

from datetime import datetime
from pydantic import BaseModel, Field

from qf_app.core.types import QuestionType, RecentnessStatus, SourceKind


class NormalizedOption(BaseModel):
    """Normalized option model."""

    key: str  # 'A', 'B', 'C', 'D'
    text: str
    is_correct: bool = False
    original_position: int = 0
    normalized_position: int = 0


class NormalizedQuestion(BaseModel):
    """Cleaned, validated, and normalized question candidate."""

    stem: str
    options: list[NormalizedOption]
    explanation: str = ""
    question_type: str = QuestionType.SINGLE_CHOICE.value

    # Curriculum mapping
    domain: int | None = None
    domain_name: str | None = None
    task_statement: str | None = None
    difficulty: str = "INTERMEDIATE"
    classification_confidence: float = 1.0
    classification_method: str = "TAXONOMY_RULES"
    topics: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)

    # Dates and recency
    published_at: datetime | None = None
    updated_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=datetime.now)
    date_confidence: str = "UNKNOWN"
    recentness_status: str = RecentnessStatus.UNKNOWN_DATE.value

    # Quality & Hashes
    quality_score: float = 70.0
    exact_hash: str = ""
    stem_hash: str = ""
    content_hash: str = ""

    # Provenance
    source_kind: str = SourceKind.PUBLIC_PRACTICE.value
    source_url: str = ""
    source_title: str = ""
    page_id: int | None = None
    extraction_method: str = "DOM_HEURISTICS"

    # Generated
    is_generated: bool = False
    generation_method: str | None = None
