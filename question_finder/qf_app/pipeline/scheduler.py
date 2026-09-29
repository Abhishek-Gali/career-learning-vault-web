"""Local APScheduler integration for automated refresh cycles."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from qf_app.core.logging import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def init_scheduler() -> AsyncIOScheduler:
    """Initialize in-process background scheduler."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Local APScheduler started.")
    return scheduler


def shutdown_scheduler() -> None:
    """Shutdown background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Local APScheduler stopped.")
