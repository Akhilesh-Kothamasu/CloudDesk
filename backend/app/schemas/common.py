"""Common enums and types for CloudDesk domain model.

Authority for categories, statuses, severities, and roles across backend,
workflows, database models, and API contracts.
"""

from enum import StrEnum


class Category(StrEnum):
    """Ticket categories.

    Exactly 10 categories supported by the platform.
    Any new category must be added here first.
    """

    LOGIN_ISSUE = "login_issue"
    BILLING = "billing"
    API_FAILURE = "api_failure"
    WORKSPACE_PERMISSIONS = "workspace_permissions"
    STORAGE_QUOTA = "storage_quota"
    INTEGRATION = "integration"
    FEATURE_REQUEST = "feature_request"
    ACCOUNT = "account"
    SECURITY = "security"
    OTHER = "other"


class TicketStatus(StrEnum):
    """Lifecycle statuses for support tickets."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    WAITING_ON_APPROVAL = "waiting_on_approval"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Severity(StrEnum):
    """Ticket severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Channel(StrEnum):
    """Intake channels for tickets."""

    EMAIL = "email"
    CHAT = "chat"
    WEB = "web"
    API = "api"


class UserRole(StrEnum):
    """RBAC user roles. Viewer (1) < Agent (2) < Admin (3)."""

    VIEWER = "viewer"
    AGENT = "agent"
    ADMIN = "admin"


class CustomerStatus(StrEnum):
    """Customer account statuses."""

    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CHURNED = "churned"


class SubscriptionPlan(StrEnum):
    """Subscription tiers."""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class ApprovalStatus(StrEnum):
    """Status of tool execution human approval gates."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EscalationPriority(StrEnum):
    """Priority levels for human escalation."""

    NORMAL = "normal"
    URGENT = "urgent"


class EscalationStatus(StrEnum):
    """Status of routed escalations."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class MemoryType(StrEnum):
    """Categories of long-term customer memory notes."""

    PREFERENCE = "preference"
    PAST_ISSUE = "past_issue"
    TROUBLESHOOTING = "troubleshooting"
    NOTE = "note"


class WorkflowStatus(StrEnum):
    """Overall status of a LangGraph workflow execution run."""

    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class WorkflowEventType(StrEnum):
    """Event types recorded during workflow execution trace."""

    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    TOOL_CALLED = "tool_called"
    LLM_CALLED = "llm_called"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESOLVED = "approval_resolved"
    ERROR = "error"
    WORKFLOW_COMPLETED = "workflow_completed"


class ActionStatus(StrEnum):
    """Execution status of planned resolution actions."""

    PLANNED = "planned"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"

