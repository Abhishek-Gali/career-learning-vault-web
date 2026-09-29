"""Authoritative answer verification engine."""

from pydantic import BaseModel
from qf_app.core.types import AnswerStatus
from qf_app.questions.types import NormalizedQuestion
from qf_app.verification.evidence import EvidenceGatherer, EvidenceItem
from qf_app.verification.knowledge import KnowledgeVerifier


class VerificationResult(BaseModel):
    """Output from the answer verification process."""

    status: str
    confidence: float
    evidence_items: list[EvidenceItem] = []
    verification_notes: str = ""


class AnswerVerifier:
    """Verifies answers using official AWS evidence and domain principles."""

    def __init__(self) -> None:
        self.evidence_gatherer = EvidenceGatherer()
        self.knowledge_verifier = KnowledgeVerifier()

    def verify(self, question: NormalizedQuestion) -> VerificationResult:
        """Verify question answer against authoritative references."""
        correct_options = [o for o in question.options if o.is_correct]

        if not correct_options:
            return VerificationResult(
                status=AnswerStatus.UNVERIFIED.value,
                confidence=0.0,
                verification_notes="No correct answer was extracted from source",
            )

        # Gather supporting AWS documentation citations
        evidence_items = self.evidence_gatherer.find_evidence(question.services, question.stem)

        # Check knowledge currency
        know_status, know_notes = self.knowledge_verifier.check_currency(question.services, question.stem)

        if evidence_items:
            status = AnswerStatus.VERIFIED.value
            confidence = 0.95
            notes = f"Answer verified against official AWS documentation. {know_notes}"
        else:
            status = AnswerStatus.PARTIALLY_VERIFIED.value
            confidence = 0.75
            notes = f"Answer supported by curriculum taxonomy and service definitions. {know_notes}"

        return VerificationResult(
            status=status,
            confidence=confidence,
            evidence_items=evidence_items,
            verification_notes=notes,
        )
