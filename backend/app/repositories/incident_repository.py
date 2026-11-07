"""Incident repository for service outages and customer impact correlation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import Incident
from backend.app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    """Repository handling platform service incidents."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Incident, session)

    async def list_active(self) -> list[Incident]:
        """Fetch ongoing incidents (investigating or identified)."""
        stmt = (
            select(Incident)
            .where(Incident.status.in_(["investigating", "identified", "monitoring"]))
            .order_by(Incident.started_at.desc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def list_all_incidents(
        self,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Incident]:
        """Fetch paginated incidents with optional status filter."""
        stmt = select(Incident)
        if status:
            stmt = stmt.where(Incident.status == status)

        stmt = stmt.order_by(Incident.started_at.desc()).offset(offset).limit(limit)
        result = await self._execute(stmt)
        return list(result.scalars().all())

