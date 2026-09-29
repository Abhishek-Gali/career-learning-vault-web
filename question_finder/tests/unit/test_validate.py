"""Unit tests for question structural validation."""

from qf_app.questions.types import NormalizedOption, NormalizedQuestion
from qf_app.questions.validate import QuestionValidator


def test_validator_accepts_valid_question():
    q = NormalizedQuestion(
        stem="Which AWS database service provides in-memory caching capabilities for fast access?",
        options=[
            NormalizedOption(key="A", text="Amazon ElastiCache", is_correct=True),
            NormalizedOption(key="B", text="Amazon RDS", is_correct=False),
        ],
    )
    validator = QuestionValidator()
    res = validator.validate(q)
    assert res.is_valid is True


def test_validator_rejects_empty_stem_and_too_few_options():
    q = NormalizedQuestion(
        stem="Short",
        options=[
            NormalizedOption(key="A", text="Only One Option", is_correct=True),
        ],
    )
    validator = QuestionValidator()
    res = validator.validate(q)
    assert res.is_valid is False
    assert len(res.reasons) >= 2
