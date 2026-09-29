"""Sources management routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import get_db_session
from qf_app.db.repositories.source_repo import SourceRepository

router = APIRouter(prefix="/sources")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
async def list_sources_view(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Render registered sources and health statistics."""
    repo = SourceRepository(session)
    sources = await repo.list_sources()
    return templates.TemplateResponse(request=request, name="sources/list.html", context={"sources": sources})
