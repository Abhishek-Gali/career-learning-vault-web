"""Unit tests for question text normalization and hashing."""

from qf_app.extraction.html import ExtractedOption, ExtractedQuestion
from qf_app.questions.normalize import QuestionNormalizer, compute_exact_hash, compute_stem_hash


def test_question_normalizer():
    extracted = ExtractedQuestion(
        stem="   Q1.   Which AWS service provides serverless compute?  ",
        options=[
            ExtractedOption(key="1", text="AWS Lambda", is_correct=True),
            ExtractedOption(key="2", text="Amazon EC2", is_correct=False),
        ],
        explanation="AWS Lambda is serverless.",
    )

    normalizer = QuestionNormalizer()
    norm = normalizer.normalize(extracted)

    assert norm.stem == "Q1. Which AWS service provides serverless compute?"
    assert len(norm.options) == 2
    assert norm.options[0].key == "A"
    assert norm.options[1].key == "B"
    assert len(norm.exact_hash) == 64
    assert len(norm.stem_hash) == 64
