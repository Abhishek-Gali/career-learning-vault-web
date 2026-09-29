"""Question structural validation."""

from pydantic import BaseModel
from qf_app.questions.types import NormalizedQuestion


class ValidationResult(BaseModel):
    """Result of question structural validation."""

    is_valid: bool
    reasons: list[str] = []


class QuestionValidator:
    """Validates structural integrity of normalized question candidates."""

    def __init__(
        self,
        min_stem_length: int = 15,
        min_options_count: int = 2,
        max_options_count: int = 10,
        require_correct_answer: bool = False,
    ) -> None:
        self.min_stem_length = min_stem_length
        self.min_options_count = min_options_count
        self.max_options_count = max_options_count
        self.require_correct_answer = require_correct_answer

    def validate(self, question: NormalizedQuestion) -> ValidationResult:
        """Validate that the question is well-formed."""
        reasons: list[str] = []

        if not question.stem or len(question.stem.strip()) < self.min_stem_length:
            reasons.append(f"Stem is too short (minimum {self.min_stem_length} characters)")

        if len(question.options) < self.min_options_count:
            reasons.append(f"Too few options ({len(question.options)} < {self.min_options_count})")

        if len(question.options) > self.max_options_count:
            reasons.append(f"Too many options ({len(question.options)} > {self.max_options_count})")

        # Check option texts
        for opt in question.options:
            if not opt.text or len(opt.text.strip()) < 1:
                reasons.append("Empty option text encountered")

        # Check answers if required
        has_correct = any(opt.is_correct for opt in question.options)
        if self.require_correct_answer and not has_correct:
            reasons.append("No correct answer identified among options")

        return ValidationResult(is_valid=len(reasons) == 0, reasons=reasons)
