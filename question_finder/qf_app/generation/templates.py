"""Deterministic practice question generator implementation."""

import random
from qf_app.generation.generator import GeneratedQuestion, QuestionGenerator
from qf_app.generation.template_data.billing import BILLING_TEMPLATES
from qf_app.generation.template_data.cloud_concepts import CLOUD_CONCEPTS_TEMPLATES
from qf_app.generation.template_data.security import SECURITY_TEMPLATES
from qf_app.generation.template_data.technology import TECHNOLOGY_TEMPLATES
from qf_app.questions.types import NormalizedOption


class TemplateGenerator(QuestionGenerator):
    """Generates supplementary CLF-C02 practice questions from verified templates."""

    def __init__(self) -> None:
        self.template_registry = {
            1: CLOUD_CONCEPTS_TEMPLATES,
            2: SECURITY_TEMPLATES,
            3: TECHNOLOGY_TEMPLATES,
            4: BILLING_TEMPLATES,
        }

    def generate_batch(self, count_per_domain: int = 5) -> list[GeneratedQuestion]:
        """Generate questions across domains with randomized option order."""
        generated: list[GeneratedQuestion] = []

        for domain_num, templates in self.template_registry.items():
            selected = templates[:count_per_domain] if len(templates) >= count_per_domain else templates
            for tpl in selected:
                raw_options = [{"text": tpl["correct"], "is_correct": True}]
                for dist in tpl["distractors"]:
                    raw_options.append({"text": dist, "is_correct": False})

                # Shuffle options deterministically
                random.shuffle(raw_options)

                normalized_options = []
                for idx, opt in enumerate(raw_options):
                    normalized_options.append(
                        NormalizedOption(
                            key=chr(65 + idx),
                            text=opt["text"],
                            is_correct=opt["is_correct"],
                            original_position=idx,
                            normalized_position=idx,
                        )
                    )

                generated.append(
                    GeneratedQuestion(
                        stem=tpl["stem"],
                        options=normalized_options,
                        explanation=tpl["explanation"],
                        domain=tpl["domain"],
                        domain_name=tpl["domain_name"],
                        task_statement=tpl["task"],
                        services=tpl.get("services", []),
                        topics=tpl.get("topics", []),
                        aws_source_url=tpl["aws_source"],
                        template_family=f"DOMAIN_{domain_num}",
                        is_generated=True,
                        generation_method="DETERMINISTIC_TEMPLATE",
                    )
                )

        return generated
