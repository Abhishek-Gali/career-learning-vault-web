"""Unit tests for dynamic research window calculations."""

from datetime import date
from qf_app.core.date_window import compute_research_window, is_within_window


def test_dynamic_date_window_six_months():
    ref_date = date(2026, 9, 29)
    start, end = compute_research_window(months=6, reference_date=ref_date)

    assert end == date(2026, 9, 29)
    assert start == date(2026, 3, 29)

    # Test dates inside vs. outside window
    assert is_within_window(date(2026, 6, 1), start, end) is True
    assert is_within_window(date(2026, 3, 29), start, end) is True
    assert is_within_window(date(2025, 12, 1), start, end) is False
    assert is_within_window(date(2026, 10, 1), start, end) is False
