"""Audit log repository for immutable security and mutation event logging."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import AuditLog
from backend.app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository handling audit log recording and compliance queries."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(AuditLog, session)

    async def record(
        self,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        actor_type: str = "user",
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Create and persist an immutable audit log entry."""
        log_entry = AuditLog(
            actor=actor,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            request_id=request_id,
        )
        self.session.add(log_entry)
        await self._flush()
        return log_entry

    async def list_logs(
        self,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Fetch filtered and paginated audit logs ordered newest first."""
        base_query = select(AuditLog)

        if actor:
            base_query = base_query.where(AuditLog.actor == actor)
        if action:
            base_query = base_query.where(AuditLog.action == action)
        if resource_type:
            base_query = base_query.where(AuditLog.resource_type == resource_type)

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_res = await self._execute(count_stmt)
        total = int(count_res.scalar_one() or 0)

        # Retrieve page
        page_stmt = (
            base_query.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        page_res = await self._execute(page_stmt)
        items = list(page_res.scalars().all())

        return items, total

