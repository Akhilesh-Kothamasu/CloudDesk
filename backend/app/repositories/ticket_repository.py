"""Ticket repository for query, search, filtering, and mutations."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from backend.app.models.entities import Ticket
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.common import TicketStatus


class TicketRepository(BaseRepository[Ticket]):
    """Repository handling all ticket database operations."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Ticket, session)

    async def get_by_ticket_number(self, ticket_number: str) -> Ticket | None:
        """Fetch a ticket by human-readable identifier (e.g. CD-1002)."""
        stmt = select(Ticket).where(Ticket.ticket_number == ticket_number)
        result = await self._execute(stmt)
        return result.scalars().first()

    async def list_tickets(
        self,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        search: str | None = None,
        customer_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Ticket], int]:
        """Fetch filtered and paginated tickets alongside total matching count."""
        base_query = select(Ticket)

        if status:
            base_query = base_query.where(Ticket.status == status)
        if severity:
            base_query = base_query.where(Ticket.severity == severity)
        if category:
            base_query = base_query.where(Ticket.category == category)
        if customer_id:
            base_query = base_query.where(Ticket.customer_id == customer_id)
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Ticket.ticket_number.ilike(search_pattern),
                    Ticket.subject.ilike(search_pattern),
                    Ticket.body.ilike(search_pattern),
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_res = await self._execute(count_stmt)
        total = int(count_res.scalar_one() or 0)

        # Retrieve page
        page_stmt = (
            base_query.order_by(Ticket.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        page_res = await self._execute(page_stmt)
        items = list(page_res.scalars().all())

        return items, total

    async def get_with_details(self, ticket_id: str) -> Ticket | None:
        """Fetch ticket with eagerly loaded related entities for the detail view."""
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(
                selectinload(Ticket.customer),
                selectinload(Ticket.messages),
                selectinload(Ticket.workflow_runs),
                selectinload(Ticket.resolution_actions),
                selectinload(Ticket.approval_requests),
                selectinload(Ticket.escalations),
            )
        )
        result = await self._execute(stmt)
        return result.scalars().first()

    async def count_by_status(self) -> dict[str, int]:
        """Group and count tickets by status."""
        stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        result = await self._execute(stmt)
        return {status: count for status, count in result.all()}

    async def count_by_severity(self) -> dict[str, int]:
        """Group and count tickets by severity."""
        stmt = select(Ticket.severity, func.count(Ticket.id)).group_by(Ticket.severity)
        result = await self._execute(stmt)
        return {severity: count for severity, count in result.all()}

    async def count_by_category(self) -> dict[str, int]:
        """Group and count tickets by category."""
        stmt = select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)
        result = await self._execute(stmt)
        return {cat: count for cat, count in result.all()}

    async def count_resolved_today(self) -> int:
        """Count tickets marked resolved today in UTC."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        stmt = (
            select(func.count(Ticket.id))
            .where(Ticket.status == TicketStatus.RESOLVED.value)
            .where(Ticket.resolved_at >= today_start)
        )
        result = await self._execute(stmt)
        return int(result.scalar_one() or 0)

    async def update_ticket(
        self,
        ticket_id: str,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        assigned_to: str | None = None,
        escalation_required: bool | None = None,
        approval_status: str | None = None,
        tags: list[str] | None = None,
    ) -> Ticket | None:
        """Update ticket attributes and commit changes."""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            return None

        if status is not None:
            ticket.status = status
            if status == TicketStatus.RESOLVED.value and not ticket.resolved_at:
                ticket.resolved_at = datetime.now(timezone.utc)
        if severity is not None:
            ticket.severity = severity
        if category is not None:
            ticket.category = category
        if assigned_to is not None:
            ticket.assigned_to = assigned_to
        if escalation_required is not None:
            ticket.escalation_required = escalation_required
        if approval_status is not None:
            ticket.approval_status = approval_status
        if tags is not None:
            ticket.tags = tags

        await self._flush()
        return ticket

