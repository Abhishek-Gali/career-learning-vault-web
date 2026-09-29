"""Unit tests for date extraction and hierarchy parsing."""

from datetime import datetime, timezone
from qf_app.core.types import DateConfidence, RecentnessStatus
from qf_app.extraction.dates import DateAnalyzer
from qf_app.extraction.metadata import MetadataExtractor


def test_date_extraction_from_json_ld(load_fixture):
    html = load_fixture("valid_recent_source.html")
    meta_extractor = MetadataExtractor()
    metadata = meta_extractor.extract(html)

    analyzer = DateAnalyzer()
    res = analyzer.analyze(metadata, raw_html=html)

    assert res.published_at is not None
    assert res.published_at.year == 2026
    assert res.published_at.month == 6
    assert res.confidence == DateConfidence.HIGH.value
    assert res.date_source == "JSON_LD_DATE_PUBLISHED"
