"""Interactive quiz session and user answer tracking models."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.core.types import QuizMode
from qf_app.db.models.base import Base, TimestampMixin, utc_now


class UserQuizSession(Base, TimestampMixin):
    """User interactive study or quiz session."""

    __tablename__ = "user_quiz_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(50), default=QuizMode.RANDOM.value, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    score_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    answers: Mapped[list["UserAnswer"]] = relationship("UserAnswer", back_populates="session", cascade="all, delete-orphan")


class UserAnswer(Base):
    """User submission for an individual question in a session."""

    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option_keys: Mapped[list[str]] = mapped_column(JSON, default=list)  # e.g. ['A'] or ['B', 'D']
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_spent_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    session: Mapped[UserQuizSession] = relationship("UserQuizSession", back_populates="answers")
    question: Mapped["Question"] = relationship("Question")
