"""Repository for Audit Logs and Rejection Records."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.db.models.audit import AuditLog, RejectionRecord


class AuditRepository:
    """Manages audit trails and rejection logging."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_decision(
        self,
        entity_type: str,
        entity_id: int,
        operation: str,
        decision: str,
        reason: str,
        run_id: int | None = None,
        evidence_reference: str | None = None,
        component: str = "PIPELINE",
    ) -> AuditLog:
        """Create structured audit trail entry."""
        log = AuditLog(
            run_id=run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            decision=decision,
            reason=reason,
            evidence_reference=evidence_reference,
            component=component,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def record_rejection(
        self,
        entity_type: str,
        entity_id: str,
        reason: str,
        evidence: str = "",
        component: str = "VALIDATOR",
    ) -> RejectionRecord:
        """Record rejected URL or malformed question."""
        rec = RejectionRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            evidence=evidence,
            component=component,
        )
        self.session.add(rec)
        await self.session.commit()
        await self.session.refresh(rec)
        return rec

    async def list_recent_logs(self, limit: int = 50) -> list[AuditLog]:
        """Fetch latest audit logs."""
        stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_rejections(self, limit: int = 50) -> list[RejectionRecord]:
        """Fetch latest rejection records."""
        stmt = select(RejectionRecord).order_by(RejectionRecord.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
