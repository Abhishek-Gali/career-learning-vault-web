"""Fetcher for the official AWS CLF-C02 exam guide."""

import hashlib
from pathlib import Path
import httpx
from qf_app.core.logging import get_logger
from qf_app.core.paths import CURRICULUM_CACHE_DIR

logger = get_logger(__name__)

OFFICIAL_EXAM_GUIDE_URL = (
    "https://d1.awsstatic.com/training-and-certification/docs-cloud-practitioner/AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf"
)


class CurriculumFetcher:
    """Retrieves and caches the official AWS CLF-C02 exam guide PDF."""

    def __init__(self, cache_dir: Path = CURRICULUM_CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_exam_guide_pdf(self, url: str = OFFICIAL_EXAM_GUIDE_URL) -> bytes | None:
        """Download exam guide PDF or return cached version if network fails."""
        cached_file = self.cache_dir / "exam_guide.pdf"

        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200 and len(response.content) > 1000:
                    cached_file.write_bytes(response.content)
                    logger.info("Successfully fetched and cached official AWS exam guide PDF.")
                    return response.content
        except Exception as err:
            logger.warning("Network fetch for exam guide failed (%s). Checking local cache.", err)

        if cached_file.exists():
            logger.info("Using cached exam guide PDF from %s", cached_file)
            return cached_file.read_bytes()

        return None
