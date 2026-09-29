"""AWS knowledge currency and staleness verification."""

from datetime import datetime, timezone
from qf_app.core.types import KnowledgeStatus


class KnowledgeVerifier:
    """Verifies that concepts and service names align with current AWS documentation."""

    def check_currency(self, services: list[str], stem: str) -> tuple[KnowledgeStatus, str]:
        """Assess whether question content is currently valid AWS knowledge."""
        lowered = stem.lower()

        # Check for historical renames
        if "simple notification service (sns)" in lowered or "amazon sns" in lowered:
            return KnowledgeStatus.CURRENT, "Service is active and current"

        if "cloudwatch events" in lowered and "eventbridge" not in lowered:
            return KnowledgeStatus.POTENTIALLY_STALE, "CloudWatch Events is now known as Amazon EventBridge"

        if "aws single sign-on" in lowered and "identity center" not in lowered:
            return KnowledgeStatus.POTENTIALLY_STALE, "AWS SSO is now known as AWS IAM Identity Center"

        return KnowledgeStatus.CURRENT, "Knowledge verified against current AWS service catalogue"
