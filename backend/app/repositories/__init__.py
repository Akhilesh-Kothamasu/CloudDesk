"""Repository layer for CloudDesk.

Provides structured SQL access for all domain entities, abstracting database
queries and mutations away from specialist agents and API routers.
"""

from backend.app.repositories.approval_repository import ApprovalRepository
from backend.app.repositories.audit_log_repository import AuditLogRepository
from backend.app.repositories.base import BaseRepository
from backend.app.repositories.customer_memory_repository import (
    CustomerMemoryRepository,
)
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.escalation_repository import EscalationRepository
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.repositories.resolution_action_repository import (
    ResolutionActionRepository,
)
from backend.app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from backend.app.repositories.support_article_repository import (
    SupportArticleRepository,
)
from backend.app.repositories.ticket_message_repository import (
    TicketMessageRepository,
)
from backend.app.repositories.ticket_repository import TicketRepository
from backend.app.repositories.workflow_repository import WorkflowRepository
from backend.app.repositories.workspace_repository import WorkspaceRepository

__all__ = [
    "ApprovalRepository",
    "AuditLogRepository",
    "BaseRepository",
    "CustomerMemoryRepository",
    "CustomerRepository",
    "EscalationRepository",
    "IncidentRepository",
    "ProductRepository",
    "ProfileRepository",
    "ResolutionActionRepository",
    "SubscriptionRepository",
    "SupportArticleRepository",
    "TicketMessageRepository",
    "TicketRepository",
    "WorkflowRepository",
    "WorkspaceRepository",
]

