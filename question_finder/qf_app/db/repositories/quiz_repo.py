"""Repository for User Quiz Sessions and Answers."""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.db.models.question import Question
from qf_app.db.models.quiz import UserAnswer, UserQuizSession


class QuizRepository:
    """Manages user quiz sessions and individual answer attempts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(
        self,
        mode: str,
        config_json: dict | None = None,
    ) -> UserQuizSession:
        """Create new quiz attempt session."""
        session = UserQuizSession(
            mode=mode,
            config_json=config_json or {},
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_user_answer(self, session_id: int, question_id: int) -> UserAnswer | None:
        """Fetch a specific answer recorded for a question in a session."""
        stmt = select(UserAnswer).where(
            UserAnswer.session_id == session_id,
            UserAnswer.question_id == question_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_answers(self, session_id: int) -> list[UserAnswer]:
        """Fetch all answers for a session."""
        stmt = select(UserAnswer).where(UserAnswer.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def record_answer(
        self,
        session_id: int,
        question_id: int,
        selected_option_keys: list[str],
        is_correct: bool,
        time_spent_seconds: float = 0.0,
    ) -> UserAnswer:
        """Record or update user response to a question."""
        stmt = select(UserAnswer).where(
            UserAnswer.session_id == session_id,
            UserAnswer.question_id == question_id,
        )
        answer = (await self.session.execute(stmt)).scalar_one_or_none()

        if answer:
            answer.selected_option_keys = selected_option_keys
            answer.is_correct = is_correct
            answer.time_spent_seconds += time_spent_seconds
        else:
            answer = UserAnswer(
                session_id=session_id,
                question_id=question_id,
                selected_option_keys=selected_option_keys,
                is_correct=is_correct,
                time_spent_seconds=time_spent_seconds,
            )
            self.session.add(answer)

        await self.session.flush()

        # Update session counters accurately based on all current answers
        quiz_sess = await self.session.get(UserQuizSession, session_id)
        if quiz_sess:
            all_answers_stmt = select(UserAnswer).where(UserAnswer.session_id == session_id)
            all_answers = list((await self.session.execute(all_answers_stmt)).scalars().all())

            q_ids = quiz_sess.config_json.get("question_ids", [])
            total_target = len(q_ids) if q_ids else len(all_answers)

            correct_cnt = sum(1 for a in all_answers if a.is_correct)
            quiz_sess.total_questions = total_target
            quiz_sess.correct_count = correct_cnt
            quiz_sess.score_percentage = (correct_cnt / total_target * 100.0) if total_target > 0 else 0.0

        await self.session.commit()
        await self.session.refresh(answer)
        return answer

    async def complete_session(self, session_id: int) -> UserQuizSession | None:
        """Mark quiz session as completed."""
        quiz_sess = await self.session.get(UserQuizSession, session_id)
        if quiz_sess and not quiz_sess.completed_at:
            quiz_sess.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(quiz_sess)
        return quiz_sess

    async def get_session_with_answers(self, session_id: int) -> UserQuizSession | None:
        """Fetch session with all its answers, questions, options, and sources eagerly loaded."""
        stmt = (
            select(UserQuizSession)
            .where(UserQuizSession.id == session_id)
            .options(
                selectinload(UserQuizSession.answers)
                .selectinload(UserAnswer.question)
                .selectinload(Question.options),
                selectinload(UserQuizSession.answers)
                .selectinload(UserAnswer.question)
                .selectinload(Question.sources),
                selectinload(UserQuizSession.answers)
                .selectinload(UserAnswer.question)
                .selectinload(Question.services),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
