"""6-Level Deduplication engine using hashing and RapidFuzz."""

from pydantic import BaseModel
from rapidfuzz import fuzz

from qf_app.db.models.question import Question
from qf_app.questions.types import NormalizedQuestion


class DuplicateMatch(BaseModel):
    """Result of duplicate comparison."""

    is_duplicate: bool
    matched_question_id: int | None = None
    similarity_score: float = 0.0
    level: str = "NONE"
    reason: str = "No duplicate detected"


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Calculate Jaccard index between two token sets."""
    if not set_a and not set_b:
        return 1.0
    union = set_a.union(set_b)
    if not union:
        return 0.0
    return len(set_a.intersection(set_b)) / len(union)


class DeduplicationEngine:
    """Executes multi-level duplicate detection on incoming questions against existing corpus."""

    def __init__(self, fuzzy_threshold: float = 85.0) -> None:
        self.fuzzy_threshold = fuzzy_threshold

    def compare_with_existing(
        self,
        new_q: NormalizedQuestion,
        existing_questions: list[Question],
    ) -> DuplicateMatch:
        """Evaluate new question against existing question corpus."""
        new_stem_lower = new_q.stem.lower()
        new_opts_set = {o.text.lower().strip() for o in new_q.options}

        for ex in existing_questions:
            # Level 1: Exact Hash
            if new_q.exact_hash and new_q.exact_hash == ex.exact_hash:
                return DuplicateMatch(
                    is_duplicate=True,
                    matched_question_id=ex.id,
                    similarity_score=1.0,
                    level="LEVEL_1_EXACT_HASH",
                    reason="Exact match on stem, options, and correct answers",
                )

            # Level 2: Stem Hash
            if new_q.stem_hash and new_q.stem_hash == ex.stem_hash:
                return DuplicateMatch(
                    is_duplicate=True,
                    matched_question_id=ex.id,
                    similarity_score=0.98,
                    level="LEVEL_2_STEM_HASH",
                    reason="Exact match on normalized question stem",
                )

            try:
                ex_opts_set = {o.option_text.lower().strip() for o in (ex.options or [])}
            except Exception:
                ex_opts_set = set()
            opt_sim = jaccard_similarity(new_opts_set, ex_opts_set)
            if opt_sim >= 0.90 and fuzz.ratio(new_stem_lower, ex.stem.lower()) >= 80.0:
                return DuplicateMatch(
                    is_duplicate=True,
                    matched_question_id=ex.id,
                    similarity_score=opt_sim,
                    level="LEVEL_3_OPTION_SET",
                    reason=f"High option set similarity ({opt_sim:.2f}) and matching stem",
                )

            # Level 5: RapidFuzz Fuzzy Stem Matching
            fuzzy_score = fuzz.token_sort_ratio(new_stem_lower, ex.stem.lower())
            if fuzzy_score >= self.fuzzy_threshold:
                return DuplicateMatch(
                    is_duplicate=True,
                    matched_question_id=ex.id,
                    similarity_score=fuzzy_score / 100.0,
                    level="LEVEL_5_FUZZY_RAPIDFUZZ",
                    reason=f"Fuzzy token-sort score {fuzzy_score:.1f} exceeds threshold {self.fuzzy_threshold}",
                )

        return DuplicateMatch(is_duplicate=False)
