"""Workspace repository for customer workspaces and integration configs."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import Workspace
from backend.app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository handling workspace records."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Workspace, session)

    async def get_by_customer_id(self, customer_id: str) -> list[Workspace]:
        """Fetch all workspaces owned by a customer."""
        stmt = (
            select(Workspace)
            .where(Workspace.customer_id == customer_id)
            .order_by(Workspace.created_at.asc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_primary_by_customer_id(self, customer_id: str) -> Workspace | None:
        """Fetch the primary (first created) workspace for a customer."""
        stmt = (
            select(Workspace)
            .where(Workspace.customer_id == customer_id)
            .order_by(Workspace.created_at.asc())
        )
        result = await self._execute(stmt)
        return result.scalars().first()

