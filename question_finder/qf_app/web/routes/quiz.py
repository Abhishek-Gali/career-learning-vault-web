"""Interactive Quiz and Study Session routes."""

import random
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import get_db_session
from qf_app.db.models.question import Question
from qf_app.db.models.quiz import UserQuizSession
from qf_app.db.repositories.quiz_repo import QuizRepository

router = APIRouter(prefix="/quiz")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
async def quiz_setup_view(request: Request):
    """Render quiz configuration and mode selection view."""
    return templates.TemplateResponse(request=request, name="quiz/setup.html", context={})


@router.post("/start")
async def start_quiz_session(
    request: Request,
    mode: str = Form(...),
    domain: int | None = Form(default=None),
    limit: int = Form(default=25),
    session: AsyncSession = Depends(get_db_session),
):
    """Initialize a quiz attempt session with matching questions."""
    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.is_canonical == True)
    )

    if domain:
        stmt = stmt.where(Question.domain == domain)
    if mode == "RECENT_SOURCE_ONLY":
        stmt = stmt.where(Question.source_kind == "PUBLIC_PRACTICE")
    elif mode == "GENERATED_ONLY":
        stmt = stmt.where(Question.source_kind == "GENERATED_PRACTICE")
    elif mode == "VERIFIED_ONLY":
        stmt = stmt.where(Question.answer_status == "VERIFIED")

    result = await session.execute(stmt)
    all_qs = list(result.scalars().all())

    if not all_qs:
        # Fallback to any questions
        all_qs = list((await session.execute(select(Question).options(selectinload(Question.options)))).scalars().all())

    if not all_qs:
        raise HTTPException(status_code=400, detail="No questions available for quiz")

    selected_ids = [q.id for q in random.sample(all_qs, min(limit, len(all_qs)))]

    quiz_repo = QuizRepository(session)
    quiz_sess = await quiz_repo.create_session(
        mode=mode,
        config_json={"question_ids": selected_ids, "total": len(selected_ids)},
    )

    root = request.scope.get("root_path", "")
    return RedirectResponse(url=f"{root}/quiz/{quiz_sess.id}/play?index=1", status_code=303)


@router.get("/{session_id}/play", response_class=HTMLResponse)
async def quiz_play_view(
    request: Request,
    session_id: int,
    index: int = 1,
    session: AsyncSession = Depends(get_db_session),
):
    """Render current question in the quiz session."""
    quiz_sess = await session.get(UserQuizSession, session_id)
    if not quiz_sess:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    q_ids = quiz_sess.config_json.get("question_ids", [])
    if index > len(q_ids):
        # Quiz completed
        root = request.scope.get("root_path", "")
        return RedirectResponse(url=f"{root}/quiz/{session_id}/result", status_code=303)

    target_qid = q_ids[index - 1]
    stmt = (
        select(Question)
        .options(
            selectinload(Question.options),
            selectinload(Question.sources),
            selectinload(Question.services),
        )
        .where(Question.id == target_qid)
    )
    question = (await session.execute(stmt)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    ordered_options = sorted(question.options, key=lambda o: (o.original_position if o.original_position is not None else 0, o.option_key))

    return templates.TemplateResponse(
        request=request,
        name="quiz/question.html",
        context={
            "session_id": session_id,
            "current_index": index,
            "total_questions": len(q_ids),
            "mode": quiz_sess.mode,
            "q": question,
            "shuffled_options": ordered_options,
        },
    )


@router.post("/{session_id}/submit")
async def submit_quiz_answer(
    request: Request,
    session_id: int,
    question_id: int = Form(...),
    current_index: int = Form(...),
    selected_options: list[str] = Form(...),
    session: AsyncSession = Depends(get_db_session),
):
    """Record answer and route to next question or results."""
    stmt = select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
    question = (await session.execute(stmt)).scalar_one_or_none()

    correct_keys = set(o.option_key for o in question.options if o.is_correct)
    user_keys = set(selected_options)
    is_correct = (correct_keys == user_keys)

    quiz_repo = QuizRepository(session)
    await quiz_repo.record_answer(
        session_id=session_id,
        question_id=question_id,
        selected_option_keys=list(user_keys),
        is_correct=is_correct,
    )

    root = request.scope.get("root_path", "")
    return RedirectResponse(url=f"{root}/quiz/{session_id}/play?index={current_index + 1}", status_code=303)


@router.get("/{session_id}/result", response_class=HTMLResponse)
async def quiz_result_view(
    request: Request,
    session_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Render completed quiz session score and analysis."""
    quiz_repo = QuizRepository(session)
    await quiz_repo.complete_session(session_id)
    sess_with_answers = await quiz_repo.get_session_with_answers(session_id)

    return templates.TemplateResponse(
        request=request,
        name="quiz/result.html",
        context={
            "session": sess_with_answers,
        },
    )
