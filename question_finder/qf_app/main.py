"""FastAPI application main module and ASGI entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from qf_app.core.logging import get_logger, setup_logging
from qf_app.core.paths import STATIC_DIR, ensure_data_dirs
from qf_app.db.engine import AsyncSessionFactory, engine
from qf_app.db.fts import init_fts5
from qf_app.db.models.base import Base
from qf_app.pipeline.scheduler import init_scheduler, shutdown_scheduler
from qf_app.web.routes import audit, dashboard, questions, quiz, research, settings, sources

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event lifespan."""
    setup_logging()
    ensure_data_dirs()
    logger.info("Initializing database tables and FTS5 index...")

    # Create tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize FTS5 table
    async with AsyncSessionFactory() as session:
        await init_fts5(session)

    # Start background scheduler
    init_scheduler()

    logger.info("CLF-C02 Researcher Web UI ready at http://127.0.0.1:8000")
    yield

    shutdown_scheduler()
    await engine.dispose()
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="CLF-C02 Recent Practice Question Researcher",
        description="Local-first AWS Certified Cloud Practitioner practice research and study tool.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Mount static assets
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register Web Routers
    app.include_router(dashboard.router)
    app.include_router(questions.router)
    app.include_router(quiz.router)
    app.include_router(sources.router)
    app.include_router(research.router)
    app.include_router(audit.router)
    app.include_router(settings.router)

    @app.get("/reader", include_in_schema=False)
    async def reader_shortcut(request: Request):
        from fastapi.responses import RedirectResponse
        query_str = f"?{request.url.query}" if request.url.query else ""
        root = request.scope.get("root_path", "")
        return RedirectResponse(url=f"{root}/questions/reader{query_str}", status_code=303)

    return app


app = create_app()
