"""Base generator interface and schemas for generated questions."""

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from qf_app.questions.types import NormalizedOption


class GeneratedQuestion(BaseModel):
    """Normalized output from deterministic or AI generation."""

    stem: str
    options: list[NormalizedOption]
    explanation: str
    domain: int
    domain_name: str
    task_statement: str
    services: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    aws_source_url: str
    template_family: str
    is_generated: bool = True
    generation_method: str = "DETERMINISTIC_TEMPLATE"


class QuestionGenerator(ABC):
    """Abstract interface for practice question generators."""

    @abstractmethod
    def generate_batch(self, count_per_domain: int = 10) -> list[GeneratedQuestion]:
        """Generate a batch of practice questions balanced across domains."""
        pass
