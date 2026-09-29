"""Integration tests for SQLite schema and repositories."""

import pytest
from qf_app.db.repositories.question_repo import QuestionRepository


@pytest.mark.asyncio
async def test_question_crud_and_options(db_session):
    repo = QuestionRepository(db_session)

    q = await repo.create_question(
        stem="Which AWS service is used to deploy Infrastructure as Code?",
        options=[
            {"key": "A", "text": "AWS CloudFormation", "is_correct": True},
            {"key": "B", "text": "AWS Elastic Beanstalk", "is_correct": False},
        ],
        explanation="AWS CloudFormation allows modeling infrastructure in JSON/YAML.",
        domain=3,
        domain_name="Cloud Technology and Services",
        task_statement="3.1",
        services=["AWS CloudFormation"],
        topics=["Infrastructure as Code"],
    )

    assert q.id is not None
    fetched = await repo.get_by_id(q.id)
    assert fetched is not None
    assert fetched.stem == "Which AWS service is used to deploy Infrastructure as Code?"
    assert len(fetched.options) == 2
    assert fetched.options[0].option_text == "AWS CloudFormation"
    assert fetched.options[0].is_correct is True
