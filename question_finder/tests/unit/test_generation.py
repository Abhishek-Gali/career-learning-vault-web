"""Unit tests for deterministic question generator and validator."""

from qf_app.generation.templates import TemplateGenerator
from qf_app.generation.validator import GenerationValidator


def test_template_generator_and_validator():
    generator = TemplateGenerator()
    questions = generator.generate_batch(count_per_domain=3)

    assert len(questions) > 0
    validator = GenerationValidator()

    for q in questions:
        assert q.is_generated is True
        assert q.generation_method == "DETERMINISTIC_TEMPLATE"
        assert len(q.options) >= 2
        val_res = validator.validate(q)
        assert val_res.is_valid is True, f"Validation failed: {val_res.reasons}"
