"""Curriculum snapshot manager."""

from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.core.logging import get_logger
from qf_app.curriculum.fetcher import CurriculumFetcher
from qf_app.curriculum.parser import CurriculumParser
from qf_app.db.models.curriculum import CurriculumSnapshot
from qf_app.db.repositories.curriculum_repo import CurriculumRepository

logger = get_logger(__name__)


class CurriculumSnapshotManager:
    """Coordinates curriculum fetching, parsing, and versioned database persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CurriculumRepository(session)
        self.fetcher = CurriculumFetcher()
        self.parser = CurriculumParser()

    async def refresh_curriculum(self, force: bool = False) -> CurriculumSnapshot:
        """Refresh or create the current curriculum snapshot."""
        current_snapshot = await self.repo.get_current_snapshot()
        pdf_bytes = await self.fetcher.fetch_exam_guide_pdf()

        if pdf_bytes:
            parsed = self.parser.parse_pdf_bytes(pdf_bytes)
        else:
            parsed = self.parser.get_fallback_curriculum()

        # Check if unchanged
        if current_snapshot and current_snapshot.content_hash == parsed["content_hash"] and not force:
            logger.info("Current curriculum snapshot is up-to-date (hash: %s).", parsed["content_hash"][:12])
            return current_snapshot

        # Persist new versioned snapshot
        snapshot = await self.repo.save_snapshot(
            exam_code=parsed["exam_code"],
            exam_name=parsed["exam_name"],
            guide_url=parsed["guide_url"],
            content_hash=parsed["content_hash"],
            domains=parsed["domains"],
            raw_text=parsed.get("raw_text"),
        )
        logger.info("Saved new active curriculum snapshot (ID: %d, Hash: %s).", snapshot.id, snapshot.content_hash[:12])
        return snapshot
