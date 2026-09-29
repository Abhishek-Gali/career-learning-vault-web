"""Repository for Questions, Options, Topics, and Services."""

from datetime import datetime
from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.core.types import AnswerStatus, QuestionStatus, RecentnessStatus, SourceKind
from qf_app.db.fts import search_questions_fts, sync_question_fts
from qf_app.db.models.question import Question, QuestionOption, QuestionService, QuestionSource, QuestionTopic


class QuestionRepository:
    """Handles persistence and retrieval of questions and their relations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_question(
        self,
        stem: str,
        options: list[dict],
        explanation: str = "",
        question_type: str = "SINGLE_CHOICE",
        domain: int | None = None,
        domain_name: str | None = None,
        task_statement: str | None = None,
        difficulty: str = "INTERMEDIATE",
        published_at: datetime | None = None,
        updated_at: datetime | None = None,
        retrieved_at: datetime | None = None,
        date_confidence: str = "UNKNOWN",
        recentness_status: str = RecentnessStatus.UNKNOWN_DATE.value,
        exact_hash: str = "",
        stem_hash: str = "",
        content_hash: str = "",
        source_kind: str = SourceKind.PUBLIC_PRACTICE.value,
        is_generated: bool = False,
        generation_method: str | None = None,
        topics: list[str] | None = None,
        services: list[str] | None = None,
        sources: list[dict] | None = None,
        quality_score: float = 70.0,
        answer_status: str = AnswerStatus.UNVERIFIED.value,
        answer_confidence: float = 0.0,
    ) -> Question:
        """Create and persist a new Question with options and metadata."""
        question = Question(
            stem=stem,
            question_type=question_type,
            explanation=explanation,
            domain=domain,
            domain_name=domain_name,
            task_statement=task_statement,
            difficulty=difficulty,
            published_at=published_at,
            updated_at=updated_at,
            retrieved_at=retrieved_at or datetime.now(),
            date_confidence=date_confidence,
            recentness_status=recentness_status,
            answer_status=answer_status,
            answer_confidence=answer_confidence,
            exact_hash=exact_hash,
            stem_hash=stem_hash,
            content_hash=content_hash,
            source_kind=source_kind,
            is_generated=is_generated,
            generation_method=generation_method,
            quality_score=quality_score,
            status=QuestionStatus.ACCEPTED.value,
        )
        self.session.add(question)
        await self.session.flush()

        # Add Options
        for idx, opt in enumerate(options):
            option = QuestionOption(
                question_id=question.id,
                option_key=opt.get("key", opt.get("id", chr(65 + idx))),
                option_text=opt.get("text", ""),
                is_correct=opt.get("is_correct", False),
                original_position=idx,
                normalized_position=idx,
            )
            self.session.add(option)

        # Add Topics
        if topics:
            for top in topics:
                self.session.add(QuestionTopic(question_id=question.id, topic=top))

        # Add Services
        if services:
            for svc in services:
                self.session.add(QuestionService(question_id=question.id, service_name=svc))

        # Add Sources
        if sources:
            for src in sources:
                self.session.add(
                    QuestionSource(
                        question_id=question.id,
                        page_id=src.get("page_id"),
                        source_url=src.get("source_url", ""),
                        source_title=src.get("source_title", ""),
                        extraction_method=src.get("extraction_method", "DOM_HEURISTICS"),
                        content_hash=src.get("content_hash"),
                        question_hash=src.get("question_hash"),
                    )
                )

        await self.session.commit()
        await self.session.refresh(question)

        # Sync to FTS5
        opts_text = " ".join([o.get("text", "") for o in options])
        topics_str = " ".join(topics or [])
        services_str = " ".join(services or [])
        source_title_str = (sources[0].get("source_title", "") if sources else "")
        await sync_question_fts(
            self.session,
            question.id,
            stem,
            opts_text,
            explanation,
            services_str,
            topics_str,
            domain_name or "",
            task_statement or "",
            source_title_str,
        )

        return question

    async def get_by_id(self, question_id: int) -> Question | None:
        """Fetch question by primary key with all relations loaded."""
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(
                selectinload(Question.options),
                selectinload(Question.topics),
                selectinload(Question.services),
                selectinload(Question.sources),
                selectinload(Question.verifications),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_exact_hash(self, exact_hash: str) -> Question | None:
        """Find question by exact hash."""
        stmt = select(Question).where(Question.exact_hash == exact_hash).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_stem_hash(self, stem_hash: str) -> list[Question]:
        """Find questions by stem hash."""
        stmt = select(Question).where(Question.stem_hash == stem_hash)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_questions(
        self,
        domain: int | None = None,
        task_statement: str | None = None,
        source_kind: str | None = None,
        recentness_status: str | None = None,
        answer_status: str | None = None,
        is_canonical: bool | None = None,
        search_query: str | None = None,
        limit: int = 50,
        offset: int = 0,
        order_dir: str = "asc",
    ) -> tuple[list[Question], int]:
        """Query and paginate questions with filters and optional FTS5 matching."""
        stmt = select(Question).options(
            selectinload(Question.options),
            selectinload(Question.topics),
            selectinload(Question.services),
            selectinload(Question.sources),
            selectinload(Question.verifications),
        )

        # FTS5 search filter
        if search_query:
            matching_ids = await search_questions_fts(self.session, search_query, limit=200)
            if not matching_ids:
                return [], 0
            stmt = stmt.where(Question.id.in_(matching_ids))

        if domain is not None:
            stmt = stmt.where(Question.domain == domain)
        if task_statement is not None:
            stmt = stmt.where(Question.task_statement == task_statement)
        if source_kind is not None:
            stmt = stmt.where(Question.source_kind == source_kind)
        if recentness_status is not None:
            stmt = stmt.where(Question.recentness_status == recentness_status)
        if answer_status is not None:
            stmt = stmt.where(Question.answer_status == answer_status)
        if is_canonical is not None:
            stmt = stmt.where(Question.is_canonical == is_canonical)

        # Count total matches
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        # Ordering direction
        if order_dir.lower() == "desc":
            stmt = stmt.order_by(Question.id.desc())
        else:
            stmt = stmt.order_by(Question.id.asc())

        # Pagination
        if limit > 0:
            stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total_count

    async def get_counts_by_category(self) -> dict[str, int]:
        """Compute distinct counts across question categories."""
        stmt = select(
            func.count(Question.id).filter(Question.source_kind == SourceKind.PUBLIC_PRACTICE.value, Question.recentness_status.in_([RecentnessStatus.RECENT_PUBLISHED.value, RecentnessStatus.RECENT_UPDATED.value])).label("recent_source"),
            func.count(Question.id).filter(Question.source_kind == SourceKind.GENERATED_PRACTICE.value).label("generated"),
            func.count(Question.id).filter(Question.recentness_status == RecentnessStatus.OLDER.value).label("older"),
            func.count(Question.id).filter(Question.recentness_status == RecentnessStatus.LEGACY.value).label("legacy"),
            func.count(Question.id).filter(Question.status == QuestionStatus.QUARANTINED.value).label("quarantined"),
            func.count(Question.id).filter(Question.is_canonical == False).label("duplicates"),
            func.count(Question.id).label("total"),
        )
        row = (await self.session.execute(stmt)).one()
        return {
            "recent_source_questions": row.recent_source or 0,
            "generated_practice_questions": row.generated or 0,
            "older_questions": row.older or 0,
            "legacy_clf_c01_questions": row.legacy or 0,
            "quarantined_questions": row.quarantined or 0,
            "duplicate_questions": row.duplicates or 0,
            "total_questions": row.total or 0,
        }
