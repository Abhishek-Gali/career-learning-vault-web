"""Settings overview route."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from qf_app.config.settings import get_settings
from qf_app.core import paths
from qf_app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/settings")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
async def settings_view(request: Request):
    """Render active configuration and filesystem storage paths."""
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="settings/index.html",
        context={
            "settings": settings,
            "paths": paths,
        },
    )
