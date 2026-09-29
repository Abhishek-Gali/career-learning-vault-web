"""CLF-C01 legacy syllabus detector."""

from qf_app.config.settings import get_rejection_rules_data
from qf_app.core.types import LegacyStatus


class LegacyC01Detector:
    """Detects older CLF-C01 specific content and retired AWS terminology."""

    def __init__(self, rules_data: dict | None = None) -> None:
        self.rules = rules_data or get_rejection_rules_data()
        self.c01_markers = self.rules.get("legacy_clf_c01_markers", ["clf-c01", "clfc01"])
        self.retired_terms = self.rules.get("retired_services_or_terms", ["amazon simpledb", "aws opsworks"])

    def evaluate(self, text: str) -> tuple[LegacyStatus, str]:
        """Classify text for CLF-C01 vs. CLF-C02."""
        lowered = text.lower()

        # Check explicit C01 markers
        for m in self.c01_markers:
            if m in lowered:
                return LegacyStatus.LEGACY_CLF_C01, f"Explicit legacy marker found: '{m}'"

        # Check retired terms
        for r in self.retired_terms:
            if r in lowered:
                return LegacyStatus.POSSIBLE_LEGACY, f"Retired AWS service mentioned: '{r}'"

        return LegacyStatus.CLF_C02, "Complies with CLF-C02 syllabus"
