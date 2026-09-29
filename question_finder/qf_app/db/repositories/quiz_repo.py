"""Repository for User Quiz Sessions and Answers."""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    async def record_answer(
        self,
        session_id: int,
        question_id: int,
        selected_option_keys: list[str],
        is_correct: bool,
        time_spent_seconds: float = 0.0,
    ) -> UserAnswer:
        """Record user response to a question."""
        answer = UserAnswer(
            session_id=session_id,
            question_id=question_id,
            selected_option_keys=selected_option_keys,
            is_correct=is_correct,
            time_spent_seconds=time_spent_seconds,
        )
        self.session.add(answer)

        # Update session counters
        quiz_sess = await self.session.get(UserQuizSession, session_id)
        if quiz_sess:
            quiz_sess.total_questions += 1
            if is_correct:
                quiz_sess.correct_count += 1
            quiz_sess.score_percentage = (quiz_sess.correct_count / quiz_sess.total_questions) * 100.0

        await self.session.commit()
        await self.session.refresh(answer)
        return answer

    async def complete_session(self, session_id: int) -> UserQuizSession | None:
        """Mark quiz session as completed."""
        quiz_sess = await self.session.get(UserQuizSession, session_id)
        if quiz_sess:
            quiz_sess.completed_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(quiz_sess)
        return quiz_sess

    async def get_session_with_answers(self, session_id: int) -> UserQuizSession | None:
        """Fetch session with all its answers and questions."""
        stmt = (
            select(UserQuizSession)
            .where(UserQuizSession.id == session_id)
            .options(
                selectinload(UserQuizSession.answers).selectinload(UserAnswer.question)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
