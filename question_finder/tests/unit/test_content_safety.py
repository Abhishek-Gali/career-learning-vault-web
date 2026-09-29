"""Unit tests for content safety and suspicious braindump detection."""

from qf_app.content_safety.classifier import ContentSafetyClassifier
from qf_app.core.types import ContentSafetyStatus


def test_quarantines_multiple_suspicious_signals():
    classifier = ContentSafetyClassifier()
    text = "Get the actual exam question from yesterday real exam dump with 100% pass guarantee braindump."
    status, reason = classifier.evaluate(text)
    assert status == ContentSafetyStatus.QUARANTINED
    assert "Multiple suspicious signals" in reason


def test_passes_normal_practice_content():
    classifier = ContentSafetyClassifier()
    text = "Here is a free practice question on Amazon S3 storage classes and lifecycle rules."
    status, _ = classifier.evaluate(text)
    assert status == ContentSafetyStatus.NORMAL
