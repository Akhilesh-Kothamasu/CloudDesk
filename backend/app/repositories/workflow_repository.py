"""Workflow repository for runs, state persistence, events, and observability metrics."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import WorkflowEvent, WorkflowRun
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.common import WorkflowStatus


class WorkflowRepository(BaseRepository[WorkflowRun]):
    """Repository handling workflow runs, execution state, and observability events."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(WorkflowRun, session)

    async def get_latest_run(self, ticket_id: str) -> WorkflowRun | None:
        """Fetch the most recent workflow run for a ticket."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.ticket_id == ticket_id)
            .order_by(WorkflowRun.created_at.desc())
        )
        result = await self._execute(stmt)
        return result.scalars().first()

    async def create_run(
        self,
        ticket_id: str,
        status: str = WorkflowStatus.RUNNING.value,
        state: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        """Initialize and persist a new workflow run."""
        run = WorkflowRun(
            ticket_id=ticket_id,
            status=status,
            state=state or {},
            errors=[],
            token_usage={},
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self._flush()
        return run

    async def update_run(
        self,
        run_id: str,
        status: str | None = None,
        current_node: str | None = None,
        state: dict[str, Any] | None = None,
        errors: list[str] | None = None,
        token_usage: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        finished: bool = False,
    ) -> WorkflowRun | None:
        """Update run attributes, state dictionary, or finish timestamp."""
        run = await self.get_by_id(run_id)
        if not run:
            return None

        if status is not None:
            run.status = status
        if current_node is not None:
            run.current_node = current_node
        if state is not None:
            run.state = state
        if errors is not None:
            run.errors = errors
        if token_usage is not None:
            run.token_usage = token_usage
        if duration_ms is not None:
            run.duration_ms = duration_ms
        if finished and not run.finished_at:
            run.finished_at = datetime.now(timezone.utc)

        await self._flush()
        return run

    async def get_recent_runs(self, limit: int = 10) -> list[WorkflowRun]:
        """Fetch latest workflow runs across all tickets."""
        stmt = (
            select(WorkflowRun)
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def record_event(
        self,
        workflow_id: str,
        ticket_id: str,
        event_type: str,
        message: str,
        node: str | None = None,
        tool: str | None = None,
        duration_ms: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        """Create and persist an observability event emitted by a workflow node or tool."""
        event = WorkflowEvent(
            workflow_id=workflow_id,
            ticket_id=ticket_id,
            event_type=event_type,
            message=message,
            node=node,
            tool=tool,
            duration_ms=duration_ms,
            payload=payload or {},
        )
        self.session.add(event)
        await self._flush()
        return event

    async def list_events_for_ticket(self, ticket_id: str) -> list[WorkflowEvent]:
        """Fetch all observability events for a ticket ordered chronologically."""
        stmt = (
            select(WorkflowEvent)
            .where(WorkflowEvent.ticket_id == ticket_id)
            .order_by(WorkflowEvent.created_at.asc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def list_events_for_run(self, workflow_id: str) -> list[WorkflowEvent]:
        """Fetch all observability events for a specific workflow run."""
        stmt = (
            select(WorkflowEvent)
            .where(WorkflowEvent.workflow_id == workflow_id)
            .order_by(WorkflowEvent.created_at.asc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def get_workflow_stats(self) -> dict[str, Any]:
        """Aggregate summary metrics for the agent observability page."""
        total_stmt = select(func.count(WorkflowRun.id))
        total_res = await self._execute(total_stmt)
        runs_total = int(total_res.scalar_one() or 0)

        completed_stmt = select(func.count(WorkflowRun.id)).where(
            WorkflowRun.status == WorkflowStatus.COMPLETED.value
        )
        completed_res = await self._execute(completed_stmt)
        runs_completed = int(completed_res.scalar_one() or 0)

        failed_stmt = select(func.count(WorkflowRun.id)).where(
            WorkflowRun.status == WorkflowStatus.FAILED.value
        )
        failed_res = await self._execute(failed_stmt)
        runs_failed = int(failed_res.scalar_one() or 0)

        avg_dur_stmt = select(func.avg(WorkflowRun.duration_ms)).where(
            WorkflowRun.duration_ms.isnot(None)
        )
        avg_dur_res = await self._execute(avg_dur_stmt)
        avg_duration_ms = float(avg_dur_res.scalar_one() or 0.0)

        return {
            "runs_total": runs_total,
            "runs_completed": runs_completed,
            "runs_failed": runs_failed,
            "avg_duration_ms": round(avg_duration_ms, 2),
            "total_tokens": 0,
            "total_estimated_cost_usd": 0.0,
        }

