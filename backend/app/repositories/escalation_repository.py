"""Escalation repository for policy escalations and human routing."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import Escalation
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.common import EscalationPriority, EscalationStatus


class EscalationRepository(BaseRepository[Escalation]):
    """Repository handling human escalation routing and tracking."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Escalation, session)

    async def list_escalations(
        self,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Escalation]:
        """Fetch filtered and paginated escalations."""
        stmt = select(Escalation)
        if status:
            stmt = stmt.where(Escalation.status == status)

        stmt = stmt.order_by(Escalation.created_at.desc()).offset(offset).limit(limit)
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_by_ticket_id(self, ticket_id: str) -> Escalation | None:
        """Fetch latest escalation record for a given ticket."""
        stmt = (
            select(Escalation)
            .where(Escalation.ticket_id == ticket_id)
            .order_by(Escalation.created_at.desc())
        )
        result = await self._execute(stmt)
        return result.scalars().first()

    async def create_escalation(
        self,
        ticket_id: str,
        ticket_number: str,
        reason: str,
        priority: str = EscalationPriority.NORMAL.value,
        assigned_team: str = "Support Lead",
        created_by: str = "ai",
        note: str | None = None,
    ) -> Escalation:
        """Create and persist a new escalation."""
        escalation = Escalation(
            ticket_id=ticket_id,
            ticket_number=ticket_number,
            reason=reason,
            priority=priority,
            assigned_team=assigned_team,
            created_by=created_by,
            note=note,
            status=EscalationStatus.OPEN.value,
        )
        self.session.add(escalation)
        await self._flush()
        return escalation

    async def update_status(
        self,
        escalation_id: str,
        status: str,
        note: str | None = None,
    ) -> Escalation | None:
        """Update escalation status (e.g. open -> acknowledged -> resolved)."""
        escalation = await self.get_by_id(escalation_id)
        if not escalation:
            return None

        escalation.status = status
        if note is not None:
            escalation.note = note
        if status == EscalationStatus.RESOLVED.value and not escalation.resolved_at:
            escalation.resolved_at = datetime.now(timezone.utc)

        await self._flush()
        return escalation

