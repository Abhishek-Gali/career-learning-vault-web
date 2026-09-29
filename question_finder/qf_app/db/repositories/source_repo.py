"""Repository for Sources, SourcePages, and SourceSnapshots."""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qf_app.db.models.source import Source, SourcePage, SourceSnapshot


class SourceRepository:
    """Manages sources, pages, and historical snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_source(
        self,
        name: str,
        domain: str,
        tier: str = "UNVERIFIED",
        priority: int = 50,
        rate_limit: float = 1.5,
        license_info: str = "Educational Reference",
        notes: str = "",
    ) -> Source:
        """Find existing source by domain or insert new one."""
        stmt = select(Source).where(Source.domain == domain)
        result = await self.session.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            source = Source(
                name=name,
                domain=domain,
                tier=tier,
                priority=priority,
                rate_limit=rate_limit,
                license_info=license_info,
                notes=notes,
            )
            self.session.add(source)
            await self.session.commit()
            await self.session.refresh(source)
        return source

    async def list_sources(self) -> list[Source]:
        """List all registered sources with page counts."""
        stmt = select(Source).options(selectinload(Source.pages)).order_by(Source.priority.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_page_by_url(self, canonical_url: str) -> SourcePage | None:
        """Find page by its canonical URL."""
        stmt = select(SourcePage).where(SourcePage.canonical_url == canonical_url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_page(
        self,
        source_id: int | None,
        url: str,
        canonical_url: str,
        title: str = "",
        content_type: str = "text/html",
        etag: str | None = None,
        last_modified: str | None = None,
        content_hash: str | None = None,
        published_at: datetime | None = None,
        updated_at: datetime | None = None,
        date_source: str | None = None,
        date_confidence: str = "UNKNOWN",
    ) -> SourcePage:
        """Insert or update a discovered SourcePage."""
        page = await self.get_page_by_url(canonical_url)
        if not page:
            page = SourcePage(
                source_id=source_id,
                url=url,
                canonical_url=canonical_url,
                title=title,
                content_type=content_type,
                etag=etag,
                last_modified=last_modified,
                content_hash=content_hash,
                published_at=published_at,
                updated_at=updated_at,
                date_source=date_source,
                date_confidence=date_confidence,
            )
            self.session.add(page)
        else:
            page.title = title or page.title
            page.etag = etag or page.etag
            page.last_modified = last_modified or page.last_modified
            page.content_hash = content_hash or page.content_hash
            page.published_at = published_at or page.published_at
            page.updated_at = updated_at or page.updated_at
            page.date_source = date_source or page.date_source
            page.date_confidence = date_confidence or page.date_confidence

        await self.session.commit()
        await self.session.refresh(page)
        return page

    async def add_snapshot(
        self,
        page_id: int,
        content_hash: str,
        status_code: int = 200,
        content_length: int = 0,
    ) -> SourceSnapshot:
        """Create a point-in-time snapshot record."""
        snapshot = SourceSnapshot(
            page_id=page_id,
            content_hash=content_hash,
            status_code=status_code,
            content_length=content_length,
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot
