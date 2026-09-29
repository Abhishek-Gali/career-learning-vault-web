"""End-to-end acceptance test for the research pipeline."""

import pytest
from qf_app.db.repositories.question_repo import QuestionRepository
from qf_app.export.formats import DatasetExporter
from qf_app.pipeline.orchestrator import ResearchPipeline


@pytest.mark.asyncio
async def test_end_to_end_research_and_export(db_session):
    pipeline = ResearchPipeline(db_session)
    stats = await pipeline.run(months=6, recent_source_target=10, max_pages=5)

    assert stats.run_id is not None
    assert stats.total_study_questions > 0

    repo = QuestionRepository(db_session)
    questions, total = await repo.list_questions(limit=100)

    assert total > 0
    assert len(questions) > 0

    # Verify exporters
    exporter = DatasetExporter()
    json_file = exporter.export_json(questions, "e2e_test.json")
    assert json_file.exists()
    assert len(json_file.read_text(encoding="utf-8")) > 100

    csv_file = exporter.export_csv(questions, "e2e_test.csv")
    assert csv_file.exists()
