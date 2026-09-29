"""Curriculum classifier mapping questions to CLF-C02 domains and tasks."""

from qf_app.curriculum.taxonomy import TaxonomyManager
from qf_app.questions.types import NormalizedQuestion


class QuestionClassifier:
    """Classifies question candidates into official CLF-C02 domains and task statements."""

    def __init__(self, taxonomy: TaxonomyManager | None = None) -> None:
        self.taxonomy = taxonomy or TaxonomyManager()

    def classify(self, question: NormalizedQuestion) -> NormalizedQuestion:
        """Enrich question with domain, task statement, service list, and confidence."""
        full_text = f"{question.stem} {' '.join([o.text for o in question.options])} {question.explanation}"

        # 1. Match in-scope AWS services
        matched_services = self.taxonomy.find_matching_services(full_text)
        question.services = matched_services

        # 2. Domain & Task classification
        domain_num, domain_name, task_stmt, confidence = self.taxonomy.classify_text(full_text)
        question.domain = domain_num
        question.domain_name = domain_name
        question.task_statement = task_stmt
        question.classification_confidence = confidence
        question.classification_method = "TAXONOMY_RULES"

        # 3. Determine topic tags
        topics = list(matched_services)
        if domain_name:
            topics.append(domain_name)
        question.topics = list(set(topics))

        # 4. Difficulty heuristic (scenario length + multi-response)
        if len(question.stem) > 200 or question.question_type == "MULTIPLE_RESPONSE":
            question.difficulty = "ADVANCED"
        elif len(question.stem) > 100:
            question.difficulty = "INTERMEDIATE"
        else:
            question.difficulty = "BASIC"

        return question
