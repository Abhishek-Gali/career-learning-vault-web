"""Research runs and manual trigger routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import AsyncSessionFactory, get_db_session
from qf_app.db.models.research import ResearchRun
from qf_app.pipeline.orchestrator import ResearchPipeline

router = APIRouter(prefix="/research")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def run_pipeline_task():
    """Background task executing a full research run."""
    async with AsyncSessionFactory() as session:
        pipeline = ResearchPipeline(session)
        await pipeline.run(months=6, recent_source_target=1000)


@router.get("", response_class=HTMLResponse)
async def list_runs_view(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Render list of research executions."""
    stmt = select(ResearchRun).order_by(ResearchRun.id.desc())
    runs = list((await session.execute(stmt)).scalars().all())
    return templates.TemplateResponse(request=request, name="research/runs.html", context={"runs": runs})


@router.post("/trigger")
async def trigger_run_action(request: Request, background_tasks: BackgroundTasks):
    """Trigger a new research run in the background."""
    background_tasks.add_task(run_pipeline_task)
    root = request.scope.get("root_path", "")
    return RedirectResponse(url=f"{root}/research", status_code=303)
