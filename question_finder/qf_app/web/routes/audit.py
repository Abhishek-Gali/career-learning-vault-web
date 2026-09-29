"""Audit log and rejection review routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import get_db_session
from qf_app.db.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/audit")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
async def audit_view(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Render audit logs and rejection records."""
    repo = AuditRepository(session)
    logs = await repo.list_recent_logs(limit=50)
    rejections = await repo.list_rejections(limit=50)

    return templates.TemplateResponse(
        request=request,
        name="audit/log.html",
        context={
            "logs": logs,
            "rejections": rejections,
        },
    )
