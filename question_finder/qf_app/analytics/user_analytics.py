"""User quiz performance tracking and weak-topic detection engine."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from qf_app.db.models.question import Question, QuestionTopic
from qf_app.db.models.quiz import UserAnswer


class UserAnalyticsEngine:
    """Analyzes user answer history to detect weak domains and recommend topics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_domain_performance(self) -> list[dict]:
        """Compute user accuracy breakdown across all 4 domains."""
        stmt = (
            select(
                Question.domain,
                Question.domain_name,
                func.count(UserAnswer.id).label("total_attempts"),
                func.count(UserAnswer.id).filter(UserAnswer.is_correct == True).label("correct_count"),
            )
            .join(Question, UserAnswer.question_id == Question.id)
            .group_by(Question.domain, Question.domain_name)
        )
        rows = (await self.session.execute(stmt)).fetchall()

        results = []
        for r in rows:
            domain_num = r[0] or 0
            domain_name = r[1] or "Unknown"
            attempts = r[2] or 0
            correct = r[3] or 0
            accuracy = (correct / attempts * 100.0) if attempts > 0 else 0.0

            results.append(
                {
                    "domain": domain_num,
                    "domain_name": domain_name,
                    "attempts": attempts,
                    "correct": correct,
                    "accuracy": round(accuracy, 1),
                    "is_weak": accuracy < 70.0 and attempts >= 3,
                }
            )
        return results

    async def get_weak_topics(self) -> list[dict]:
        """Identify specific topics with accuracy below 70%."""
        stmt = (
            select(
                QuestionTopic.topic,
                func.count(UserAnswer.id).label("attempts"),
                func.count(UserAnswer.id).filter(UserAnswer.is_correct == True).label("correct"),
            )
            .join(Question, UserAnswer.question_id == Question.id)
            .join(QuestionTopic, Question.id == QuestionTopic.question_id)
            .group_by(QuestionTopic.topic)
            .having(func.count(UserAnswer.id) >= 2)
        )
        rows = (await self.session.execute(stmt)).fetchall()

        weak_list = []
        for r in rows:
            topic = r[0]
            attempts = r[1]
            correct = r[2]
            acc = (correct / attempts * 100.0) if attempts > 0 else 0.0
            if acc < 70.0:
                weak_list.append(
                    {
                        "topic": topic,
                        "attempts": attempts,
                        "correct": correct,
                        "accuracy": round(acc, 1),
                    }
                )

        return sorted(weak_list, key=lambda x: x["accuracy"])
