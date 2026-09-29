"""Unit tests for CLF-C01 legacy syllabus detection."""

from qf_app.core.types import LegacyStatus
from qf_app.verification.c01_detector import LegacyC01Detector


def test_detects_explicit_c01():
    detector = LegacyC01Detector()
    status, reason = detector.evaluate("This question covers the old CLF-C01 syllabus from 2019.")
    assert status == LegacyStatus.LEGACY_CLF_C01
    assert "clf-c01" in reason.lower()


def test_detects_retired_terms():
    detector = LegacyC01Detector()
    status, reason = detector.evaluate("How does Amazon SimpleDB compare with modern DynamoDB tables?")
    assert status == LegacyStatus.POSSIBLE_LEGACY
    assert "simpledb" in reason.lower()


def test_passes_valid_c02():
    detector = LegacyC01Detector()
    status, _ = detector.evaluate("Which service provides serverless compute via AWS Lambda?")
    assert status == LegacyStatus.CLF_C02
