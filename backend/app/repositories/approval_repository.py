"""Approval repository for human-in-the-loop gates and sensitive action authorizations."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import ApprovalRequest
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.common import ApprovalStatus


class ApprovalRepository(BaseRepository[ApprovalRequest]):
    """Repository handling human approval requests and decisions."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(ApprovalRequest, session)

    async def list_pending(self) -> list[ApprovalRequest]:
        """Fetch all pending approval requests ordered chronologically."""
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.status == ApprovalStatus.PENDING.value)
            .order_by(ApprovalRequest.created_at.asc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_pending_by_ticket_id(
        self, ticket_id: str
    ) -> ApprovalRequest | None:
        """Fetch active pending approval request for a ticket if any exists."""
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.ticket_id == ticket_id)
            .where(ApprovalRequest.status == ApprovalStatus.PENDING.value)
            .order_by(ApprovalRequest.created_at.desc())
        )
        result = await self._execute(stmt)
        return result.scalars().first()

    async def create_request(
        self,
        ticket_id: str,
        ticket_number: str,
        workflow_id: str,
        action: dict[str, Any],
        risk_level: str = "high",
        reason: str = "",
        requested_by: str = "ai",
    ) -> ApprovalRequest:
        """Create and persist a new approval request for a sensitive action."""
        request = ApprovalRequest(
            ticket_id=ticket_id,
            ticket_number=ticket_number,
            workflow_id=workflow_id,
            action=action,
            risk_level=risk_level,
            reason=reason,
            requested_by=requested_by,
            status=ApprovalStatus.PENDING.value,
        )
        self.session.add(request)
        await self._flush()
        return request

    async def decide(
        self,
        approval_id: str,
        status: str,
        decided_by: str | None = None,
        decision_note: str | None = None,
    ) -> ApprovalRequest | None:
        """Record decision (approved/rejected) on an approval request."""
        approval = await self.get_by_id(approval_id)
        if not approval:
            return None

        approval.status = status
        approval.decided_by = decided_by
        approval.decision_note = decision_note
        approval.decided_at = datetime.now(timezone.utc)

        await self._flush()
        return approval

