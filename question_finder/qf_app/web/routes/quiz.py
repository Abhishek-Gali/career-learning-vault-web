"""Interactive Quiz and Study Session routes."""

import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import get_db_session
from qf_app.db.models.question import Question
from qf_app.db.models.quiz import UserAnswer, UserQuizSession
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
    """Initialize a quiz attempt session with matching questions and countdown timer."""
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

    selected_count = min(limit, len(all_qs))
    selected_ids = [q.id for q in random.sample(all_qs, selected_count)]

    # Calculate timer limit based on exam pacing (1.5 min per question, minimum 10 min)
    time_limit_seconds = max(600, selected_count * 90)
    started_at_ts = int(datetime.now(timezone.utc).timestamp())

    quiz_repo = QuizRepository(session)
    quiz_sess = await quiz_repo.create_session(
        mode=mode,
        config_json={
            "question_ids": selected_ids,
            "total": selected_count,
            "time_limit_seconds": time_limit_seconds,
            "started_at_ts": started_at_ts,
        },
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
    """Render current question in the quiz session with back/forth navigator and timer."""
    quiz_sess = await session.get(UserQuizSession, session_id)
    if not quiz_sess:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    q_ids = quiz_sess.config_json.get("question_ids", [])
    if not q_ids:
        raise HTTPException(status_code=400, detail="No questions found in this quiz session")

    # If quiz is marked completed or index is past end, redirect to results
    root = request.scope.get("root_path", "")
    if quiz_sess.completed_at or index > len(q_ids):
        return RedirectResponse(url=f"{root}/quiz/{session_id}/result", status_code=303)

    target_index = max(1, min(index, len(q_ids)))
    target_qid = q_ids[target_index - 1]

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

    ordered_options = sorted(
        question.options,
        key=lambda o: (o.original_position if o.original_position is not None else 0, o.option_key),
    )

    quiz_repo = QuizRepository(session)

    # Fetch user's existing answer for this question if previously answered
    user_answer = await quiz_repo.get_user_answer(session_id, target_qid)
    existing_selection = user_answer.selected_option_keys if user_answer else []

    # Fetch all answers to build navigator palette
    all_answers = await quiz_repo.get_session_answers(session_id)
    answered_qids = {a.question_id: a for a in all_answers if a.selected_option_keys}

    palette = [
        {
            "index": i + 1,
            "question_id": qid,
            "is_current": (i + 1 == target_index),
            "is_answered": (qid in answered_qids),
        }
        for i, qid in enumerate(q_ids)
    ]

    # Calculate remaining time
    time_limit_seconds = quiz_sess.config_json.get("time_limit_seconds", len(q_ids) * 90)
    started_at_ts = quiz_sess.config_json.get("started_at_ts")
    if not started_at_ts:
        started_at_ts = int(quiz_sess.started_at.timestamp())

    now_ts = int(datetime.now(timezone.utc).timestamp())
    elapsed_seconds = max(0, now_ts - started_at_ts)
    remaining_seconds = max(0, time_limit_seconds - elapsed_seconds)

    return templates.TemplateResponse(
        request=request,
        name="quiz/question.html",
        context={
            "session_id": session_id,
            "current_index": target_index,
            "total_questions": len(q_ids),
            "has_prev": target_index > 1,
            "prev_index": target_index - 1,
            "has_next": target_index < len(q_ids),
            "next_index": target_index + 1,
            "mode": quiz_sess.mode,
            "q": question,
            "shuffled_options": ordered_options,
            "existing_selection": existing_selection,
            "palette": palette,
            "answered_count": len(answered_qids),
            "remaining_seconds": remaining_seconds,
            "time_limit_seconds": time_limit_seconds,
        },
    )


@router.post("/{session_id}/submit")
async def submit_quiz_answer(
    request: Request,
    session_id: int,
    question_id: int = Form(...),
    current_index: int = Form(...),
    target_index: int | None = Form(default=None),
    action: str = Form(default="next"),
    selected_options: list[str] = Form(default=[]),
    session: AsyncSession = Depends(get_db_session),
):
    """Record or update answer and navigate forward, backward, or to results."""
    quiz_repo = QuizRepository(session)

    if selected_options:
        stmt = select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
        question = (await session.execute(stmt)).scalar_one_or_none()

        if question:
            correct_keys = set(o.option_key for o in question.options if o.is_correct)
            user_keys = set(selected_options)
            is_correct = (correct_keys == user_keys)

            await quiz_repo.record_answer(
                session_id=session_id,
                question_id=question_id,
                selected_option_keys=list(user_keys),
                is_correct=is_correct,
            )

    root = request.scope.get("root_path", "")

    if action == "finish":
        return RedirectResponse(url=f"{root}/quiz/{session_id}/result", status_code=303)

    if target_index is not None:
        next_idx = target_index
    elif action == "prev":
        next_idx = max(1, current_index - 1)
    else:
        next_idx = current_index + 1

    quiz_sess = await session.get(UserQuizSession, session_id)
    q_ids = quiz_sess.config_json.get("question_ids", []) if quiz_sess else []

    if next_idx > len(q_ids):
        return RedirectResponse(url=f"{root}/quiz/{session_id}/result", status_code=303)

    return RedirectResponse(url=f"{root}/quiz/{session_id}/play?index={next_idx}", status_code=303)


@router.get("/{session_id}/result", response_class=HTMLResponse)
async def quiz_result_view(
    request: Request,
    session_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Render completed quiz session score, metrics, and question-by-question breakdown."""
    quiz_repo = QuizRepository(session)
    await quiz_repo.complete_session(session_id)

    quiz_sess = await session.get(UserQuizSession, session_id)
    if not quiz_sess:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    q_ids = quiz_sess.config_json.get("question_ids", [])

    # Fetch all questions in this session with full relationships eagerly loaded
    if q_ids:
        stmt = (
            select(Question)
            .where(Question.id.in_(q_ids))
            .options(
                selectinload(Question.options),
                selectinload(Question.sources),
                selectinload(Question.services),
            )
        )
        questions_map = {q.id: q for q in (await session.execute(stmt)).scalars().all()}
    else:
        questions_map = {}

    # Fetch user answers
    answers_stmt = select(UserAnswer).where(UserAnswer.session_id == session_id)
    user_answers_map = {a.question_id: a for a in (await session.execute(answers_stmt)).scalars().all()}

    # Construct comprehensive question breakdown
    breakdown = []
    correct_count = 0
    for idx, qid in enumerate(q_ids):
        q_obj = questions_map.get(qid)
        if not q_obj:
            continue
        ans_obj = user_answers_map.get(qid)
        selected_keys = ans_obj.selected_option_keys if ans_obj else []
        is_correct = ans_obj.is_correct if ans_obj else False
        if is_correct:
            correct_count += 1

        breakdown.append({
            "index": idx + 1,
            "question": q_obj,
            "selected_keys": selected_keys,
            "is_answered": len(selected_keys) > 0,
            "is_correct": is_correct,
        })

    total_q = len(q_ids) if q_ids else len(breakdown)
    score_pct = round((correct_count / total_q) * 100.0, 1) if total_q > 0 else 0.0

    quiz_sess.total_questions = total_q
    quiz_sess.correct_count = correct_count
    quiz_sess.score_percentage = score_pct
    await session.commit()

    return templates.TemplateResponse(
        request=request,
        name="quiz/result.html",
        context={
            "session": quiz_sess,
            "breakdown": breakdown,
            "total_questions": total_q,
            "correct_count": correct_count,
            "score_percentage": score_pct,
        },
    )
