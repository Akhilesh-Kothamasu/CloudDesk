"""SQLAlchemy 2 entities for CloudDesk.

Portable models using JSON columns and String(36) UUIDs to support both
SQLite (local demo and offline tests) and PostgreSQL / Supabase (production).
"""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.schemas.common import (
    ActionStatus,
    ApprovalStatus,
    Category,
    Channel,
    CustomerStatus,
    EscalationPriority,
    EscalationStatus,
    MemoryType,
    Severity,
    SubscriptionPlan,
    TicketStatus,
    UserRole,
    WorkflowEventType,
    WorkflowStatus,
)


def _generate_uuid() -> str:
    """Generate a String(36) UUID string."""
    return str(uuid.uuid4())


class Profile(Base):
    """User profile for support platform staff (viewer, agent, admin)."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=UserRole.VIEWER.value
    )
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Customer(Base):
    """Customer entity holding account status, tier, and lifetime value."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SubscriptionPlan.FREE.value
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=CustomerStatus.ACTIVE.value
    )
    region: Mapped[str] = mapped_column(
        String(50), nullable=False, default="us-east"
    )
    lifetime_value: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan"
    )
    workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace", back_populates="customer", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="customer", cascade="all, delete-orphan"
    )
    customer_memory: Mapped[list["CustomerMemory"]] = relationship(
        "CustomerMemory", back_populates="customer", cascade="all, delete-orphan"
    )


class Product(Base):
    """Product catalog item for pricing and subscriptions."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SubscriptionPlan.FREE.value
    )
    base_price: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Subscription(Base):
    """Customer subscription plan, quota limits, and billing terms."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SubscriptionPlan.FREE.value
    )
    seats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )
    mrr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    storage_quota_gb: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    storage_used_gb: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    api_rate_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=120
    )
    renews_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="subscriptions"
    )


class Workspace(Base):
    """Customer organization workspace and integrations."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    storage_used_gb: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    integrations: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    sso_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="workspaces"
    )


class Ticket(Base):
    """Support ticket with classification, status, routing, and escalation."""

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    ticket_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TicketStatus.NEW.value
    )
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=Severity.LOW.value
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=Category.OTHER.value
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(50), nullable=False, default=Channel.EMAIL.value
    )
    assigned_to: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    escalation_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    approval_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ApprovalStatus.NOT_REQUIRED.value
    )
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")
    messages: Mapped[list["TicketMessage"]] = relationship(
        "TicketMessage", back_populates="ticket", cascade="all, delete-orphan"
    )
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun", back_populates="ticket", cascade="all, delete-orphan"
    )
    resolution_actions: Mapped[list["ResolutionAction"]] = relationship(
        "ResolutionAction", back_populates="ticket", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest", back_populates="ticket", cascade="all, delete-orphan"
    )
    escalations: Mapped[list["Escalation"]] = relationship(
        "Escalation", back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketMessage(Base):
    """Conversation message in a ticket thread."""

    __tablename__ = "ticket_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="customer"
    )
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attachments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")


class SupportArticle(Base):
    """Knowledge base article for RAG retrieval."""

    __tablename__ = "support_articles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=Category.OTHER.value
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Incident(Base):
    """Active or past service incidents that may impact customer tickets."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="investigating"
    )
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=Severity.MEDIUM.value
    )
    affected_services: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class WorkflowRun(Base):
    """Execution run of the LangGraph multi-agent workflow."""

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=WorkflowStatus.RUNNING.value
    )
    current_node: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    errors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    token_usage: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="workflow_runs"
    )
    events: Mapped[list["WorkflowEvent"]] = relationship(
        "WorkflowEvent", back_populates="workflow_run", cascade="all, delete-orphan"
    )


class WorkflowEvent(Base):
    """Detailed observability event emitted during workflow execution."""

    __tablename__ = "workflow_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    node: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    workflow_run: Mapped["WorkflowRun"] = relationship(
        "WorkflowRun", back_populates="events"
    )


class ResolutionAction(Base):
    """Action planned or executed by the resolution agent."""

    __tablename__ = "resolution_actions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ActionStatus.PLANNED.value
    )
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="resolution_actions"
    )


class ApprovalRequest(Base):
    """Human-in-the-loop approval request gating sensitive tool execution."""

    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False)
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    risk_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="high"
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ai"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ApprovalStatus.PENDING.value
    )
    decided_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="approval_requests"
    )


class Escalation(Base):
    """Policy-mandated or specialist-requested human escalation record."""

    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    ticket_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EscalationPriority.NORMAL.value
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EscalationStatus.OPEN.value
    )
    created_by: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ai"
    )
    assigned_team: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="escalations"
    )


class CustomerMemory(Base):
    """Long-term customer memory notes recalled during workflow executions."""

    __tablename__ = "customer_memory"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MemoryType.NOTE.value
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_ticket_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="customer_memory"
    )


class AuditLog(Base):
    """Audit log entry for security and compliance recording every mutation."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user"
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    request_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

