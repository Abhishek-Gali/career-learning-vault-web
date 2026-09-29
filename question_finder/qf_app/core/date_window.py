"""Dynamic research window calculations."""

from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta


def compute_research_window(months: int = 6, reference_date: date | None = None) -> tuple[date, date]:
    """Compute dynamic research window (start_date, end_date).

    End date defaults to current UTC date.
    Start date is end date minus `months` calendar months.
    """
    end = reference_date or datetime.now(timezone.utc).date()
    start = end - relativedelta(months=months)
    return start, end


def is_within_window(target_date: date | datetime, window_start: date, window_end: date) -> bool:
    """Check if target date falls within the inclusive date window."""
    if isinstance(target_date, datetime):
        d = target_date.date()
    else:
        d = target_date
    return window_start <= d <= window_end
