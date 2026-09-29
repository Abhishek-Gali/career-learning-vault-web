"""Taxonomy dictionaries and keyword matching helpers for CLF-C02."""

from typing import Any
from qf_app.config.settings import get_taxonomy_data


class TaxonomyManager:
    """Manages domains, task statements, and AWS service classifications."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data = data or get_taxonomy_data()
        self.domains: list[dict[str, Any]] = self.data.get("domains", [])
        self.out_of_scope: list[str] = self.data.get("out_of_scope_services", [])

    def get_all_domains(self) -> list[dict[str, Any]]:
        """Return all domains with weightings and tasks."""
        return self.domains

    def get_domain_by_number(self, number: int) -> dict[str, Any] | None:
        """Lookup domain by number (1..4)."""
        for d in self.domains:
            if d.get("number") == number:
                return d
        return None

    def find_matching_services(self, text: str) -> list[str]:
        """Identify in-scope AWS services mentioned in text."""
        lowered = text.lower()
        matched = set()

        for d in self.domains:
            for t in d.get("tasks", []):
                for kw in t.get("keywords", []):
                    # Check if keyword represents an AWS service name
                    if kw.lower().startswith("amazon ") or kw.lower().startswith("aws "):
                        if kw.lower() in lowered:
                            matched.add(kw)
        return sorted(matched)

    def classify_text(self, text: str) -> tuple[int | None, str | None, str | None, float]:
        """Classify text into (domain_number, domain_name, task_statement, confidence)."""
        lowered = text.lower()
        domain_scores: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        task_scores: dict[str, int] = {}

        for d in self.domains:
            d_num = d.get("number", 1)
            for t in d.get("tasks", []):
                t_num = t.get("number", "")
                task_scores[t_num] = 0
                for kw in t.get("keywords", []):
                    if kw.lower() in lowered:
                        # Add score proportional to keyword length
                        pts = 2 if len(kw) > 6 else 1
                        domain_scores[d_num] += pts
                        task_scores[t_num] += pts

        # Find best matching domain
        best_domain = max(domain_scores, key=domain_scores.get)
        max_score = domain_scores[best_domain]

        if max_score == 0:
            # Default fallback if no keywords matched
            return 3, "Cloud Technology and Services", "3.1", 0.3

        # Find best matching task statement in that domain
        best_task = None
        best_task_score = -1
        domain_obj = self.get_domain_by_number(best_domain)
        if domain_obj:
            for t in domain_obj.get("tasks", []):
                t_num = t.get("number")
                if task_scores.get(t_num, 0) > best_task_score:
                    best_task_score = task_scores.get(t_num, 0)
                    best_task = t_num

        confidence = min(0.95, 0.4 + (max_score * 0.1))
        domain_name = domain_obj.get("name") if domain_obj else "Cloud Technology and Services"
        return best_domain, domain_name, best_task or "3.1", confidence
