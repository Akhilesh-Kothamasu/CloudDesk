"""Ticket message repository for thread messages and audit communications."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import TicketMessage
from backend.app.repositories.base import BaseRepository


class TicketMessageRepository(BaseRepository[TicketMessage]):
    """Repository handling ticket conversation message operations."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(TicketMessage, session)

    async def get_messages_by_ticket_id(
        self, ticket_id: str, include_internal: bool = True
    ) -> list[TicketMessage]:
        """Fetch all messages for a ticket ordered chronologically."""
        stmt = (
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.created_at.asc())
        )
        if not include_internal:
            stmt = stmt.where(TicketMessage.internal.is_(False))

        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def create_message(
        self,
        ticket_id: str,
        author_name: str,
        body: str,
        role: str = "customer",
        internal: bool = False,
        attachments: list[dict[str, Any]] | None = None,
    ) -> TicketMessage:
        """Create and persist a new message in a ticket thread."""
        message = TicketMessage(
            ticket_id=ticket_id,
            author_name=author_name,
            body=body,
            role=role,
            internal=internal,
            attachments=attachments or [],
        )
        self.session.add(message)
        await self._flush()
        return message

