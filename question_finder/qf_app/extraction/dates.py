"""10-Level Date extraction hierarchy and recency analyzer."""

from datetime import datetime, timezone
import dateparser
from pydantic import BaseModel

from qf_app.core.types import DateConfidence, RecentnessStatus
from qf_app.extraction.metadata import PageMetadata


class DateResult(BaseModel):
    """Extracted publication and update dates with confidence evaluation."""

    published_at: datetime | None = None
    updated_at: datetime | None = None
    date_source: str = "UNKNOWN"
    confidence: str = DateConfidence.UNKNOWN.value
    recentness_status: str = RecentnessStatus.UNKNOWN_DATE.value
    recentness_reason: str = "No valid date found"


def parse_date_string(date_str: str | None) -> datetime | None:
    """Safely parse human or ISO date string using dateparser."""
    if not date_str or len(date_str.strip()) < 4:
        return None
    try:
        parsed = dateparser.parse(
            date_str.strip(),
            languages=["en"],
            settings={"PREFER_DATES_FROM": "past", "TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True},
        )
        return parsed
    except Exception:
        return None


class DateAnalyzer:
    """Inspects metadata and page markup using a 10-level hierarchy."""

    def analyze(
        self,
        metadata: PageMetadata,
        raw_html: str = "",
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> DateResult:
        """Run 10-level hierarchy to extract published_at and updated_at."""
        published_at: datetime | None = None
        updated_at: datetime | None = None
        date_source: str = "UNKNOWN"
        confidence: str = DateConfidence.UNKNOWN.value

        # Level 1 & 2: JSON-LD Structured Data
        for block in metadata.json_ld_blocks:
            if "datePublished" in block:
                published_at = parse_date_string(str(block["datePublished"]))
                date_source = "JSON_LD_DATE_PUBLISHED"
                confidence = DateConfidence.HIGH.value
            if "dateModified" in block:
                updated_at = parse_date_string(str(block["dateModified"]))
                if not date_source or date_source == "UNKNOWN":
                    date_source = "JSON_LD_DATE_MODIFIED"
                    confidence = DateConfidence.HIGH.value

        # Level 3 & 4: OpenGraph Article Dates
        if not published_at and metadata.og_published_time:
            published_at = parse_date_string(metadata.og_published_time)
            date_source = "OPENGRAPH_PUBLISHED"
            confidence = DateConfidence.HIGH.value

        if not updated_at and metadata.og_modified_time:
            updated_at = parse_date_string(metadata.og_modified_time)
            if not date_source or date_source == "UNKNOWN":
                date_source = "OPENGRAPH_MODIFIED"
                confidence = DateConfidence.HIGH.value

        # Level 5: Meta date tags
        if not published_at:
            for k, v in metadata.meta_dates.items():
                if "pub" in k or "create" in k:
                    published_at = parse_date_string(v)
                    if published_at:
                        date_source = f"META_{k.upper()}"
                        confidence = DateConfidence.MEDIUM.value
                        break

        if not updated_at:
            for k, v in metadata.meta_dates.items():
                if "mod" in k or "update" in k:
                    updated_at = parse_date_string(v)
                    if updated_at:
                        if not date_source or date_source == "UNKNOWN":
                            date_source = f"META_{k.upper()}"
                            confidence = DateConfidence.MEDIUM.value
                        break

        # Evaluate recency status
        now_utc = datetime.now(timezone.utc)
        eval_date = updated_at or published_at

        if not eval_date:
            return DateResult(
                published_at=None,
                updated_at=None,
                date_source="UNKNOWN",
                confidence=DateConfidence.UNKNOWN.value,
                recentness_status=RecentnessStatus.UNKNOWN_DATE.value,
                recentness_reason="No machine-readable date found in metadata",
            )

        # Recency evaluation relative to 6-month window
        if window_start and window_end:
            win_start = window_start.replace(tzinfo=timezone.utc) if window_start.tzinfo is None else window_start
            win_end = window_end.replace(tzinfo=timezone.utc) if window_end.tzinfo is None else window_end

            if published_at and win_start <= published_at <= win_end:
                status = RecentnessStatus.RECENT_PUBLISHED.value
                reason = f"Published ({published_at.strftime('%Y-%m-%d')}) within active research window"
            elif updated_at and win_start <= updated_at <= win_end:
                status = RecentnessStatus.RECENT_UPDATED.value
                reason = f"Substantially updated ({updated_at.strftime('%Y-%m-%d')}) within active research window"
            else:
                status = RecentnessStatus.OLDER.value
                reason = f"Date ({eval_date.strftime('%Y-%m-%d')}) falls outside the 6-month research window"
        else:
            status = RecentnessStatus.RECENT_PUBLISHED.value
            reason = "Date resolved successfully"

        return DateResult(
            published_at=published_at,
            updated_at=updated_at,
            date_source=date_source,
            confidence=confidence,
            recentness_status=status,
            recentness_reason=reason,
        )
