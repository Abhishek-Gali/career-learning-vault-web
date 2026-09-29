"""Suspicious content classifier for quarantine and review."""

from qf_app.config.settings import get_rejection_rules_data
from qf_app.core.types import ContentSafetyStatus


class ContentSafetyClassifier:
    """Inspects questions and pages for suspicious braindump / exam dump claims."""

    def __init__(self, rules_data: dict | None = None) -> None:
        self.rules = rules_data or get_rejection_rules_data()
        self.suspicious_keywords = self.rules.get("suspicious_keywords", [
            "actual exam question", "real exam dump", "leaked questions", "braindump"
        ])

    def evaluate(self, text: str) -> tuple[ContentSafetyStatus, str]:
        """Evaluate text for unauthorized or suspicious exam disclosure language."""
        lowered = text.lower()
        matched_signals = []

        for kw in self.suspicious_keywords:
            if kw in lowered:
                matched_signals.append(kw)

        if len(matched_signals) >= 2:
            return ContentSafetyStatus.QUARANTINED, f"Multiple suspicious signals detected: {', '.join(matched_signals)}"
        elif len(matched_signals) == 1:
            return ContentSafetyStatus.REVIEW_REQUIRED, f"Single suspicious signal detected: {matched_signals[0]}"

        return ContentSafetyStatus.NORMAL, "Content passed safety review"
