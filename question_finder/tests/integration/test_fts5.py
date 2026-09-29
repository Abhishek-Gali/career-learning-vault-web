"""Integration tests for FTS5 full-text search indexing."""

import pytest
from qf_app.db.fts import search_questions_fts
from qf_app.db.repositories.question_repo import QuestionRepository


@pytest.mark.asyncio
async def test_fts5_indexing_and_search(db_session):
    repo = QuestionRepository(db_session)

    q1 = await repo.create_question(
        stem="Which service provides real-time threat detection via machine learning?",
        options=[{"key": "A", "text": "Amazon GuardDuty", "is_correct": True}],
        explanation="Amazon GuardDuty is an intelligent threat detection service.",
        services=["Amazon GuardDuty"],
        topics=["Security"],
    )

    q2 = await repo.create_question(
        stem="How can an organization track user API activities across their accounts?",
        options=[{"key": "A", "text": "AWS CloudTrail", "is_correct": True}],
        explanation="AWS CloudTrail records AWS API calls.",
        services=["AWS CloudTrail"],
        topics=["Governance"],
    )

    # Search for "GuardDuty"
    ids = await search_questions_fts(db_session, "GuardDuty")
    assert q1.id in ids
    assert q2.id not in ids

    # Search for "API"
    ids_api = await search_questions_fts(db_session, "API")
    assert q2.id in ids_api
