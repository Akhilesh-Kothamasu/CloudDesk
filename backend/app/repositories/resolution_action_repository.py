"""Resolution action repository for planned, approved, and executed agent tools."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import ResolutionAction
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.common import ActionStatus


class ResolutionActionRepository(BaseRepository[ResolutionAction]):
    """Repository handling resolution action lifecycle."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(ResolutionAction, session)

    async def get_by_ticket_id(self, ticket_id: str) -> list[ResolutionAction]:
        """Fetch all planned and executed actions for a ticket ordered chronologically."""
        stmt = (
            select(ResolutionAction)
            .where(ResolutionAction.ticket_id == ticket_id)
            .order_by(ResolutionAction.created_at.asc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def create_action(
        self,
        ticket_id: str,
        tool: str,
        arguments: dict[str, Any],
        requires_approval: bool = False,
        status: str = ActionStatus.PLANNED.value,
    ) -> ResolutionAction:
        """Create and persist an action planned by the resolution agent."""
        action = ResolutionAction(
            ticket_id=ticket_id,
            tool=tool,
            arguments=arguments,
            requires_approval=requires_approval,
            status=status,
        )
        self.session.add(action)
        await self._flush()
        return action

    async def update_status(
        self,
        action_id: str,
        status: str,
        result: dict[str, Any] | None = None,
    ) -> ResolutionAction | None:
        """Update action execution status and store result payload."""
        action = await self.get_by_id(action_id)
        if not action:
            return None

        action.status = status
        if result is not None:
            action.result = result
        if status == ActionStatus.EXECUTED.value and not action.executed_at:
            action.executed_at = datetime.now(timezone.utc)

        await self._flush()
        return action

