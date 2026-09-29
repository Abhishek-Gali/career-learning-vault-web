"""Dashboard routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.analytics.coverage import CoverageAnalyzer
from qf_app.analytics.stats import DatasetStatsCalculator
from qf_app.analytics.user_analytics import UserAnalyticsEngine
from qf_app.core.date_window import compute_research_window
from qf_app.core.paths import TEMPLATES_DIR
from qf_app.db.engine import get_db_session

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Render primary study & research overview dashboard."""
    stats_calc = DatasetStatsCalculator(session)
    stats = await stats_calc.get_summary_stats()

    cov_calc = CoverageAnalyzer(session)
    coverage = await cov_calc.get_domain_coverage()

    user_calc = UserAnalyticsEngine(session)
    weak_topics = await user_calc.get_weak_topics()

    win_start, win_end = compute_research_window(months=6)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "stats": stats,
            "coverage": coverage,
            "weak_topics": weak_topics,
            "window_start": win_start.isoformat(),
            "window_end": win_end.isoformat(),
        },
    )
