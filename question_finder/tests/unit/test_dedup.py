"""Unit tests for multi-level deduplication engine."""

from qf_app.db.models.question import Question, QuestionOption
from qf_app.deduplication.engine import DeduplicationEngine
from qf_app.questions.types import NormalizedOption, NormalizedQuestion


def test_dedup_exact_hash():
    existing = [
        Question(
            id=101,
            stem="Which AWS service provides object storage?",
            exact_hash="abc123exacthash",
            stem_hash="stemhash123",
            options=[
                QuestionOption(option_key="A", option_text="Amazon S3", is_correct=True),
                QuestionOption(option_key="B", option_text="Amazon EC2", is_correct=False),
            ],
        )
    ]

    new_q = NormalizedQuestion(
        stem="Which AWS service provides object storage?",
        options=[
            NormalizedOption(key="A", text="Amazon S3", is_correct=True),
            NormalizedOption(key="B", text="Amazon EC2", is_correct=False),
        ],
        exact_hash="abc123exacthash",
        stem_hash="stemhash123",
    )

    engine = DeduplicationEngine()
    match = engine.compare_with_existing(new_q, existing)

    assert match.is_duplicate is True
    assert match.matched_question_id == 101
    assert match.level == "LEVEL_1_EXACT_HASH"


def test_dedup_fuzzy_rapidfuzz():
    existing = [
        Question(
            id=202,
            stem="Which AWS service delivers on demand resizable compute capacity in the cloud?",
            exact_hash="hash1",
            stem_hash="stem1",
            options=[
                QuestionOption(option_key="A", option_text="Amazon EC2 Instances", is_correct=True),
                QuestionOption(option_key="B", option_text="AWS Lightsail Servers", is_correct=False),
            ],
        )
    ]

    new_q = NormalizedQuestion(
        stem="Which AWS service provides on-demand resizable compute capacity in cloud?",
        options=[
            NormalizedOption(key="A", text="Amazon Virtual Servers", is_correct=True),
            NormalizedOption(key="B", text="AWS Cloud Functions", is_correct=False),
        ],
        exact_hash="hash2",
        stem_hash="stem2",
    )

    engine = DeduplicationEngine(fuzzy_threshold=80.0)
    match = engine.compare_with_existing(new_q, existing)

    assert match.is_duplicate is True
    assert match.matched_question_id == 202
    assert "FUZZY" in match.level
