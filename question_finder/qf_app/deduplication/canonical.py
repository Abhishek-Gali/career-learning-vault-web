"""Canonical question selection algorithm."""

from qf_app.core.types import AnswerStatus
from qf_app.db.models.question import Question


class CanonicalSelector:
    """Selects the best canonical representation from a set of duplicate questions."""

    def score_question(self, question: Question) -> tuple[float, str]:
        """Compute quality ranking score for canonical election."""
        score = 0.0
        reasons = []

        # 1. Answer Verification Status (up to 30 pts)
        if question.answer_status == AnswerStatus.VERIFIED.value:
            score += 30.0
            reasons.append("+30 Verified Answer")
        elif question.answer_status == AnswerStatus.PARTIALLY_VERIFIED.value:
            score += 15.0
            reasons.append("+15 Partial Verification")

        # 2. Explanation Completeness (up to 20 pts)
        if question.explanation and len(question.explanation) > 50:
            score += 20.0
            reasons.append("+20 Rich Explanation")
        elif question.explanation:
            score += 10.0
            reasons.append("+10 Basic Explanation")

        # 3. Provenance & Date Confidence (up to 20 pts)
        if question.date_confidence == "HIGH":
            score += 20.0
            reasons.append("+20 High Date Confidence")
        elif question.date_confidence == "MEDIUM":
            score += 10.0
            reasons.append("+10 Medium Date Confidence")

        # 4. Stem Clarity (up to 15 pts)
        if 40 <= len(question.stem) <= 300:
            score += 15.0
            reasons.append("+15 Clear Concise Stem")
        else:
            score += 5.0

        # 5. Option Completeness (up to 15 pts)
        if len(question.options) == 4:
            score += 15.0
            reasons.append("+15 Standard 4 Options")
        elif len(question.options) >= 2:
            score += 10.0

        return score, "; ".join(reasons)

    def select_best(self, candidates: list[Question]) -> tuple[Question, str]:
        """Return the highest-scoring candidate and explanation."""
        if not candidates:
            raise ValueError("Candidates list cannot be empty")
        if len(candidates) == 1:
            return candidates[0], "Only candidate in cluster"

        best_q = candidates[0]
        best_score, best_reason = self.score_question(candidates[0])

        for q in candidates[1:]:
            score, reason = self.score_question(q)
            if score > best_score:
                best_score = score
                best_q = q
                best_reason = reason

        return best_q, f"Selected with score {best_score:.1f}: {best_reason}"
