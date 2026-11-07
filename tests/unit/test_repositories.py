"""Unit tests for the repository layer across all domain entities."""

from datetime import datetime, timezone
from typing import Any, Coroutine
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.core.database import Base
from backend.app.models.entities import (
    ApprovalRequest,
    AuditLog,
    Customer,
    CustomerMemory,
    Escalation,
    Incident,
    Product,
    Profile,
    ResolutionAction,
    Subscription,
    SupportArticle,
    Ticket,
    TicketMessage,
    WorkflowEvent,
    WorkflowRun,
    Workspace,
)
from backend.app.repositories import (
    ApprovalRepository,
    AuditLogRepository,
    BaseRepository,
    CustomerMemoryRepository,
    CustomerRepository,
    EscalationRepository,
    IncidentRepository,
    ProductRepository,
    ProfileRepository,
    ResolutionActionRepository,
    SubscriptionRepository,
    SupportArticleRepository,
    TicketMessageRepository,
    TicketRepository,
    WorkflowRepository,
    WorkspaceRepository,
)
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
    WorkflowStatus,
)


def run_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute a coroutine synchronously without creating socketpairs or event loops."""
    while True:
        try:
            coro.send(None)
        except StopIteration as e:
            return e.value


@pytest.fixture
def db_session():
    """Create in-memory SQLite engine and session for unit testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_base_repository_crud(db_session):
    """Verify generic BaseRepository operations (get, list, count, update, delete)."""
    repo = BaseRepository[Product](Product, db_session)

    # Create
    product = Product(name="CloudDesk Basic", code="CD-BASIC", tier="free", base_price=0.0)
    created = run_sync(repo.create(product))
    assert created.id is not None

    # Get by id
    fetched = run_sync(repo.get_by_id(created.id))
    assert fetched is not None
    assert fetched.code == "CD-BASIC"

    # Count & List
    count = run_sync(repo.count())
    assert count == 1
    items = run_sync(repo.list_all())
    assert len(items) == 1

    # Update
    fetched.name = "CloudDesk Starter"
    updated = run_sync(repo.update(fetched))
    assert updated.name == "CloudDesk Starter"

    # Delete
    deleted = run_sync(repo.delete(created.id))
    assert deleted is True
    assert run_sync(repo.get_by_id(created.id)) is None
    assert run_sync(repo.count()) == 0


def test_ticket_repository_queries_and_stats(db_session):
    """Verify TicketRepository filtering, search, grouping, and metrics."""
    cust_repo = CustomerRepository(db_session)
    ticket_repo = TicketRepository(db_session)

    customer = Customer(
        name="Alice Corp",
        email="alice@corp.com",
        company="Alice Corp",
        plan_name=SubscriptionPlan.ENTERPRISE.value,
    )
    run_sync(cust_repo.create(customer))

    # Create tickets
    t1 = Ticket(
        ticket_number="CD-1001",
        subject="SSO login failure",
        body="SSO logins failing across company",
        status=TicketStatus.NEW.value,
        severity=Severity.CRITICAL.value,
        category=Category.LOGIN_ISSUE.value,
        customer_id=customer.id,
    )
    t2 = Ticket(
        ticket_number="CD-1002",
        subject="Refund request for unused seats",
        body="Charged for 8 seats but only using 5",
        status=TicketStatus.WAITING_ON_APPROVAL.value,
        severity=Severity.MEDIUM.value,
        category=Category.BILLING.value,
        customer_id=customer.id,
    )
    t3 = Ticket(
        ticket_number="CD-1003",
        subject="API rate limit inquiry",
        body="Hitting 429 during nightly export",
        status=TicketStatus.RESOLVED.value,
        severity=Severity.LOW.value,
        category=Category.API_FAILURE.value,
        customer_id=customer.id,
        resolved_at=datetime.now(timezone.utc),
    )
    run_sync(ticket_repo.create(t1))
    run_sync(ticket_repo.create(t2))
    run_sync(ticket_repo.create(t3))

    # Search & filters
    items, total = run_sync(ticket_repo.list_tickets(search="unused seats"))
    assert total == 1
    assert items[0].ticket_number == "CD-1002"

    items, total = run_sync(ticket_repo.list_tickets(category=Category.LOGIN_ISSUE.value))
    assert total == 1
    assert items[0].ticket_number == "CD-1001"

    items, total = run_sync(ticket_repo.list_tickets(severity=Severity.CRITICAL.value))
    assert total == 1

    # Fetch by number
    fetched_t1 = run_sync(ticket_repo.get_by_ticket_number("CD-1001"))
    assert fetched_t1 is not None
    assert fetched_t1.id == t1.id

    # Group counts
    status_counts = run_sync(ticket_repo.count_by_status())
    assert status_counts[TicketStatus.NEW.value] == 1
    assert status_counts[TicketStatus.WAITING_ON_APPROVAL.value] == 1
    assert status_counts[TicketStatus.RESOLVED.value] == 1

    sev_counts = run_sync(ticket_repo.count_by_severity())
    assert sev_counts[Severity.CRITICAL.value] == 1

    cat_counts = run_sync(ticket_repo.count_by_category())
    assert cat_counts[Category.BILLING.value] == 1

    resolved_today = run_sync(ticket_repo.count_resolved_today())
    assert resolved_today == 1

    # Update ticket status
    updated = run_sync(
        ticket_repo.update_ticket(
            t1.id,
            status=TicketStatus.RESOLVED.value,
            tags=["sso", "fixed"],
        )
    )
    assert updated.status == TicketStatus.RESOLVED.value
    assert updated.resolved_at is not None
    assert updated.tags == ["sso", "fixed"]


def test_ticket_message_repository(db_session):
    """Verify TicketMessageRepository message creation and internal filtering."""
    cust_repo = CustomerRepository(db_session)
    ticket_repo = TicketRepository(db_session)
    msg_repo = TicketMessageRepository(db_session)

    customer = run_sync(
        cust_repo.create(
            Customer(name="Bob", email="bob@demo.com", company="Bob Inc")
        )
    )
    ticket = run_sync(
        ticket_repo.create(
            Ticket(
                ticket_number="CD-1004",
                subject="Quota issue",
                body="Storage full",
                customer_id=customer.id,
            )
        )
    )

    # Create customer message
    msg1 = run_sync(
        msg_repo.create_message(
            ticket_id=ticket.id,
            author_name="Bob",
            body="My upload failed due to quota",
            role="customer",
            internal=False,
        )
    )
    # Create internal agent note
    msg2 = run_sync(
        msg_repo.create_message(
            ticket_id=ticket.id,
            author_name="Agent Sam",
            body="Customer has 10GB quota, currently at 9.9GB",
            role="agent",
            internal=True,
        )
    )

    # Fetch with and without internal
    all_msgs = run_sync(msg_repo.get_messages_by_ticket_id(ticket.id, include_internal=True))
    assert len(all_msgs) == 2

    public_msgs = run_sync(msg_repo.get_messages_by_ticket_id(ticket.id, include_internal=False))
    assert len(public_msgs) == 1
    assert public_msgs[0].id == msg1.id


def test_customer_and_relations_repositories(db_session):
    """Verify CustomerRepository, SubscriptionRepository, and WorkspaceRepository."""
    cust_repo = CustomerRepository(db_session)
    sub_repo = SubscriptionRepository(db_session)
    ws_repo = WorkspaceRepository(db_session)

    customer = run_sync(
        cust_repo.create(
            Customer(
                name="Charlie",
                email="charlie@enterprise.com",
                company="Enterprise Corp",
                plan_name=SubscriptionPlan.ENTERPRISE.value,
            )
        )
    )

    sub = run_sync(
        sub_repo.create(
            Subscription(
                customer_id=customer.id,
                plan=SubscriptionPlan.ENTERPRISE.value,
                seats=25,
                mrr=1250.0,
                status="active",
            )
        )
    )

    ws = run_sync(
        ws_repo.create(
            Workspace(
                customer_id=customer.id,
                name="Primary HQ",
                integrations=["slack", "jira"],
            )
        )
    )

    # Test search
    items, total = run_sync(cust_repo.search_customers(search="Enterprise"))
    assert total == 1
    assert items[0].email == "charlie@enterprise.com"

    # Test subscription & workspace queries
    fetched_sub = run_sync(sub_repo.get_active_by_customer_id(customer.id))
    assert fetched_sub is not None
    assert fetched_sub.seats == 25

    workspaces = run_sync(ws_repo.get_by_customer_id(customer.id))
    assert len(workspaces) == 1
    assert workspaces[0].name == "Primary HQ"

    primary_ws = run_sync(ws_repo.get_primary_by_customer_id(customer.id))
    assert primary_ws is not None


def test_workflow_repository(db_session):
    """Verify WorkflowRepository runs, state persistence, events, and metrics."""
    cust_repo = CustomerRepository(db_session)
    ticket_repo = TicketRepository(db_session)
    wf_repo = WorkflowRepository(db_session)

    cust = run_sync(cust_repo.create(Customer(name="D", email="d@d.com", company="D Co")))
    ticket = run_sync(
        ticket_repo.create(
            Ticket(ticket_number="CD-1005", subject="Breach", body="Help", customer_id=cust.id)
        )
    )

    # Create run
    run = run_sync(wf_repo.create_run(ticket.id, status=WorkflowStatus.RUNNING.value))
    assert run.id is not None

    # Update run
    updated_run = run_sync(
        wf_repo.update_run(
            run.id,
            current_node="investigate",
            state={"step": "investigate", "confidence": 0.95},
            status=WorkflowStatus.COMPLETED.value,
            duration_ms=450,
            finished=True,
        )
    )
    assert updated_run.status == WorkflowStatus.COMPLETED.value
    assert updated_run.duration_ms == 450
    assert updated_run.finished_at is not None

    # Record events
    ev1 = run_sync(
        wf_repo.record_event(
            workflow_id=run.id,
            ticket_id=ticket.id,
            event_type="node_started",
            message="Supervisor starting",
            node="supervisor",
        )
    )
    ev2 = run_sync(
        wf_repo.record_event(
            workflow_id=run.id,
            ticket_id=ticket.id,
            event_type="node_completed",
            message="Supervisor completed",
            node="supervisor",
            duration_ms=120,
        )
    )

    events = run_sync(wf_repo.list_events_for_ticket(ticket.id))
    assert len(events) == 2

    # Stats
    stats = run_sync(wf_repo.get_workflow_stats())
    assert stats["runs_total"] == 1
    assert stats["runs_completed"] == 1
    assert stats["avg_duration_ms"] == 450.0


def test_approval_and_escalation_repositories(db_session):
    """Verify ApprovalRepository and EscalationRepository operations."""
    cust_repo = CustomerRepository(db_session)
    ticket_repo = TicketRepository(db_session)
    wf_repo = WorkflowRepository(db_session)
    app_repo = ApprovalRepository(db_session)
    esc_repo = EscalationRepository(db_session)

    cust = run_sync(cust_repo.create(Customer(name="E", email="e@e.com", company="E Co")))
    ticket = run_sync(
        ticket_repo.create(
            Ticket(ticket_number="CD-1006", subject="Refund", body="Seats", customer_id=cust.id)
        )
    )
    run = run_sync(wf_repo.create_run(ticket.id))

    # Approval Request
    approval = run_sync(
        app_repo.create_request(
            ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            workflow_id=run.id,
            action={"tool": "refund", "amount": 150.0},
            reason="Amount exceeds $100 auto threshold",
        )
    )
    pending_list = run_sync(app_repo.list_pending())
    assert len(pending_list) == 1

    pending_ticket = run_sync(app_repo.get_pending_by_ticket_id(ticket.id))
    assert pending_ticket is not None
    assert pending_ticket.id == approval.id

    decided = run_sync(
        app_repo.decide(
            approval.id,
            status=ApprovalStatus.APPROVED.value,
            decision_note="Approved by lead",
        )
    )
    assert decided.status == ApprovalStatus.APPROVED.value
    assert decided.decided_at is not None

    # Escalation
    esc = run_sync(
        esc_repo.create_escalation(
            ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            reason="VIP customer inquiry",
            priority=EscalationPriority.URGENT.value,
        )
    )
    esc_list = run_sync(esc_repo.list_escalations(status=EscalationStatus.OPEN.value))
    assert len(esc_list) == 1

    esc_resolved = run_sync(
        esc_repo.update_status(esc.id, status=EscalationStatus.RESOLVED.value, note="Handled")
    )
    assert esc_resolved.status == EscalationStatus.RESOLVED.value
    assert esc_resolved.resolved_at is not None


def test_resolution_action_and_memory_repositories(db_session):
    """Verify ResolutionActionRepository and CustomerMemoryRepository."""
    cust_repo = CustomerRepository(db_session)
    ticket_repo = TicketRepository(db_session)
    action_repo = ResolutionActionRepository(db_session)
    mem_repo = CustomerMemoryRepository(db_session)

    cust = run_sync(cust_repo.create(Customer(name="F", email="f@f.com", company="F Co")))
    ticket = run_sync(
        ticket_repo.create(
            Ticket(ticket_number="CD-1007", subject="Action test", body="Test", customer_id=cust.id)
        )
    )

    # Resolution action
    action = run_sync(
        action_repo.create_action(
            ticket_id=ticket.id,
            tool="apply_discount",
            arguments={"discount_percent": 15},
            requires_approval=False,
        )
    )
    actions = run_sync(action_repo.get_by_ticket_id(ticket.id))
    assert len(actions) == 1

    updated_act = run_sync(
        action_repo.update_status(action.id, ActionStatus.EXECUTED.value, result={"status": "applied"})
    )
    assert updated_act.status == ActionStatus.EXECUTED.value
    assert updated_act.executed_at is not None

    # Memory
    mem = run_sync(
        mem_repo.create_memory(
            customer_id=cust.id,
            content="Customer requires German invoices",
            memory_type=MemoryType.PREFERENCE.value,
            source_ticket_id=ticket.id,
        )
    )
    memories = run_sync(mem_repo.get_by_customer_id(cust.id))
    assert len(memories) == 1
    assert memories[0].content == "Customer requires German invoices"


def test_support_article_incident_profile_audit_repositories(db_session):
    """Verify SupportArticleRepository, IncidentRepository, ProfileRepository, AuditLogRepository."""
    article_repo = SupportArticleRepository(db_session)
    incident_repo = IncidentRepository(db_session)
    profile_repo = ProfileRepository(db_session)
    audit_repo = AuditLogRepository(db_session)

    # Article
    art = run_sync(
        article_repo.create(
            SupportArticle(
                slug="reset-mfa",
                title="Reset Multi-Factor Authentication",
                category=Category.LOGIN_ISSUE.value,
                summary="Steps to reset MFA tokens",
                content="To reset MFA, go to settings and click Reset MFA...",
                tags=["mfa", "login"],
            )
        )
    )
    fetched_art = run_sync(article_repo.get_by_slug("reset-mfa"))
    assert fetched_art is not None
    items, total = run_sync(article_repo.list_articles(search="Multi-Factor"))
    assert total == 1

    # Incident
    inc = run_sync(
        incident_repo.create(
            Incident(
                title="US-East API Latency",
                description="Elevated latency observed in US-East",
                status="investigating",
                severity=Severity.HIGH.value,
            )
        )
    )
    active_incidents = run_sync(incident_repo.list_active())
    assert len(active_incidents) == 1
    assert active_incidents[0].title == "US-East API Latency"

    # Profile
    prof = run_sync(
        profile_repo.create(
            Profile(
                email="agent@clouddesk.demo",
                full_name="Agent Sam",
                role=UserRole.AGENT.value,
            )
        )
    )
    fetched_prof = run_sync(profile_repo.get_by_email("agent@clouddesk.demo"))
    assert fetched_prof is not None
    assert fetched_prof.full_name == "Agent Sam"

    agents = run_sync(profile_repo.list_by_role(UserRole.AGENT.value))
    assert len(agents) == 1

    # Audit log
    log = run_sync(
        audit_repo.record(
            actor="agent@clouddesk.demo",
            action="ticket_reply",
            resource_type="ticket",
            resource_id="ticket-123",
            details={"channel": "email"},
            request_id="req-999",
        )
    )
    logs, total = run_sync(audit_repo.list_logs(actor="agent@clouddesk.demo"))
    assert total == 1
    assert logs[0].action == "ticket_reply"
    assert logs[0].request_id == "req-999"
