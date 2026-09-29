"""Question Bank routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import get_db_session
from qf_app.db.repositories.question_repo import QuestionRepository

router = APIRouter(prefix="/questions")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
async def list_questions_view(
    request: Request,
    q: str | None = Query(default=None),
    domain: int | None = Query(default=None),
    source_kind: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=10, le=2000),
    order: str = Query(default="asc"),
    jump_to: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    """Render filterable, searchable question bank ordered from 1 to last or newest."""
    repo = QuestionRepository(session)

    # If jump_to is provided, compute the page that contains jump_to
    if jump_to is not None and jump_to > 0:
        page = max(1, (jump_to - 1) // limit + 1)

    offset = (page - 1) * limit
    questions, total = await repo.list_questions(
        domain=domain,
        source_kind=source_kind,
        search_query=q,
        limit=limit,
        offset=offset,
        order_dir=order,
    )

    total_pages = max(1, (total + limit - 1) // limit)
    start_idx = offset + 1 if total > 0 else 0
    end_idx = min(offset + limit, total)

    return templates.TemplateResponse(
        request=request,
        name="questions/list.html",
        context={
            "questions": questions,
            "total_count": total,
            "search_query": q,
            "selected_domain": domain,
            "selected_kind": source_kind,
            "current_page": page,
            "total_pages": total_pages,
            "limit": limit,
            "order_dir": order,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "jump_to": jump_to,
        },
    )


@router.get("/reader", response_class=HTMLResponse)
async def sequential_reader_view(
    request: Request,
    domain: int | None = Query(default=None),
    batch: int = Query(default=100, ge=10, le=1500),
    page: int = Query(default=1, ge=1),
    jump_to: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    """Render distraction-free sequential study reader (Question 1 to Last)."""
    repo = QuestionRepository(session)

    if jump_to is not None and jump_to > 0:
        page = max(1, (jump_to - 1) // batch + 1)

    offset = (page - 1) * batch
    questions, total = await repo.list_questions(
        domain=domain,
        limit=batch,
        offset=offset,
        order_dir="asc",
    )
    total_pages = max(1, (total + batch - 1) // batch)
    start_idx = offset + 1 if total > 0 else 0
    end_idx = min(offset + batch, total)

    return templates.TemplateResponse(
        request=request,
        name="questions/reader.html",
        context={
            "questions": questions,
            "total_count": total,
            "selected_domain": domain,
            "current_page": page,
            "total_pages": total_pages,
            "batch": batch,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "jump_to": jump_to,
        },
    )


@router.get("/{question_id}", response_class=HTMLResponse)
async def question_detail_view(
    request: Request,
    question_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Render full question details, verification evidence, and provenance."""
    repo = QuestionRepository(session)
    question = await repo.get_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return templates.TemplateResponse(
        request=request,
        name="questions/detail.html",
        context={
            "q": question,
        },
    )
