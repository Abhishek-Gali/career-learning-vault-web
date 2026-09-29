"""Unit tests for CLF-C02 syllabus classification."""

from qf_app.questions.classify import QuestionClassifier
from qf_app.questions.types import NormalizedOption, NormalizedQuestion


def test_classify_security_question():
    q = NormalizedQuestion(
        stem="Which AWS service helps manage encryption keys and controls their use across AWS services?",
        options=[
            NormalizedOption(key="A", text="AWS Key Management Service (AWS KMS)", is_correct=True),
            NormalizedOption(key="B", text="AWS Shield", is_correct=False),
        ],
    )
    classifier = QuestionClassifier()
    classified = classifier.classify(q)

    assert classified.domain == 2
    assert "Security" in classified.domain_name
    assert "AWS KMS" in classified.services or "AWS Key Management Service" in str(classified.services)
