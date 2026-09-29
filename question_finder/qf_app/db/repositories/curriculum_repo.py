"""Repository for Curriculum Snapshots, Domains, and Tasks."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.db.models.curriculum import CurriculumDomain, CurriculumSnapshot, CurriculumTask


class CurriculumRepository:
    """Manages official AWS CLF-C02 syllabus snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_current_snapshot(self) -> CurriculumSnapshot | None:
        """Fetch the active curriculum snapshot with domains and task statements."""
        stmt = (
            select(CurriculumSnapshot)
            .where(CurriculumSnapshot.is_current == True)
            .options(
                selectinload(CurriculumSnapshot.domains).selectinload(CurriculumDomain.tasks)
            )
            .order_by(CurriculumSnapshot.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_snapshot(
        self,
        exam_code: str,
        exam_name: str,
        guide_url: str,
        content_hash: str,
        domains: list[dict],
        raw_text: str | None = None,
    ) -> CurriculumSnapshot:
        """Persist a new curriculum snapshot, deactivating previous ones."""
        # Deactivate old snapshots
        stmt = select(CurriculumSnapshot).where(CurriculumSnapshot.is_current == True)
        old_snapshots = (await self.session.execute(stmt)).scalars().all()
        for old in old_snapshots:
            old.is_current = False

        # Create new active snapshot
        snapshot = CurriculumSnapshot(
            exam_code=exam_code,
            exam_name=exam_name,
            guide_url=guide_url,
            content_hash=content_hash,
            is_current=True,
            raw_text=raw_text,
        )
        self.session.add(snapshot)
        await self.session.flush()

        # Add Domains and Tasks
        for d in domains:
            domain = CurriculumDomain(
                snapshot_id=snapshot.id,
                domain_number=d["number"],
                domain_name=d["name"],
                weighting=d["weighting"],
            )
            self.session.add(domain)
            await self.session.flush()

            for t in d.get("tasks", []):
                task = CurriculumTask(
                    domain_id=domain.id,
                    task_number=t["number"],
                    task_statement=t["statement"],
                    knowledge_items=t.get("keywords", []),
                )
                self.session.add(task)

        await self.session.commit()
        return await self.get_current_snapshot()
