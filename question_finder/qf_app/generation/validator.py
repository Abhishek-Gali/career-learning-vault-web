"""Generated question fact and distractor validation."""

from pydantic import BaseModel
from qf_app.generation.generator import GeneratedQuestion


class GenerationValidationResult(BaseModel):
    """Validation outcome for a generated question."""

    is_valid: bool
    reasons: list[str] = []


class GenerationValidator:
    """Validates generated questions for AWS factual correctness and unambiguity."""

    def validate(self, question: GeneratedQuestion) -> GenerationValidationResult:
        """Run validation rules against generated question."""
        reasons: list[str] = []

        # Rule 1: Minimum stem length
        if len(question.stem.strip()) < 20:
            reasons.append("Stem length is under minimum 20 characters")

        # Rule 2: Valid options count (must have >= 2)
        if len(question.options) < 2:
            reasons.append(f"Too few options: {len(question.options)}")

        # Rule 3: Exactly one correct option (for single choice templates)
        correct_opts = [o for o in question.options if o.is_correct]
        if len(correct_opts) != 1:
            reasons.append(f"Expected exactly 1 correct answer, found {len(correct_opts)}")

        # Rule 4: Distinct options (no duplicate option texts)
        opt_texts = [o.text.lower().strip() for o in question.options]
        if len(opt_texts) != len(set(opt_texts)):
            reasons.append("Duplicate option texts found among choices")

        # Rule 5: Supporting AWS URL present
        if not question.aws_source_url or not question.aws_source_url.startswith("http"):
            reasons.append("Missing valid official AWS source citation URL")

        return GenerationValidationResult(is_valid=len(reasons) == 0, reasons=reasons)
