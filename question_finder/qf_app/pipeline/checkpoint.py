"""Stage checkpointing and run state persistence."""

from sqlalchemy.ext.asyncio import AsyncSession
from qf_app.db.models.research import ResearchRun


class CheckpointManager:
    """Tracks current stage execution inside ResearchRun records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_stage(self, run_id: int, current_stage: str, stats_update: dict | None = None) -> None:
        """Update active pipeline stage and incremental statistics."""
        run = await self.session.get(ResearchRun, run_id)
        if run:
            run.status = f"RUNNING_{current_stage}"
            if stats_update:
                current_stats = dict(run.stats_json or {})
                current_stats.update(stats_update)
                run.stats_json = current_stats
            await self.session.commit()
