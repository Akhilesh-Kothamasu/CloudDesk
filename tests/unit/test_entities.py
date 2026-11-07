"""Unit tests for domain enums, SQLAlchemy entities, and database schema."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.core.database import Base, create_tables
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
from backend.app.schemas.common import (
    Category,
    Channel,
    CustomerStatus,
    EscalationPriority,
    EscalationStatus,
    Severity,
    SubscriptionPlan,
    TicketStatus,
    UserRole,
)


def test_category_enum_exact_ten():
    """Verify Category enum contains exactly the 10 defined categories."""
    expected_categories = {
        "login_issue",
        "billing",
        "api_failure",
        "workspace_permissions",
        "storage_quota",
        "integration",
        "feature_request",
        "account",
        "security",
        "other",
    }
    actual_categories = {c.value for c in Category}

    assert actual_categories == expected_categories
    assert len(Category) == 10


def test_domain_enums():
    """Verify domain enums contain expected contract values."""
    assert {s.value for s in TicketStatus} == {
        "new",
        "in_progress",
        "waiting_on_customer",
        "waiting_on_approval",
        "escalated",
        "resolved",
        "closed",
    }
    assert {s.value for s in Severity} == {"low", "medium", "high", "critical"}
    assert {c.value for c in Channel} == {"email", "chat", "web", "api"}
    assert {r.value for r in UserRole} == {"viewer", "agent", "admin"}
    assert {s.value for s in CustomerStatus} == {
        "active",
        "trial",
        "past_due",
        "churned",
    }
    assert {p.value for p in SubscriptionPlan} == {
        "free",
        "pro",
        "business",
        "enterprise",
    }


def test_metadata_contains_all_sixteen_tables():
    """Verify Base.metadata has registered exactly the 16 required tables."""
    expected_tables = {
        "profiles",
        "customers",
        "subscriptions",
        "workspaces",
        "products",
        "tickets",
        "ticket_messages",
        "support_articles",
        "incidents",
        "workflow_runs",
        "workflow_events",
        "resolution_actions",
        "approval_requests",
        "escalations",
        "customer_memory",
        "audit_logs",
    }
    actual_tables = set(Base.metadata.tables.keys())

    assert actual_tables == expected_tables
    assert len(actual_tables) == 16


def test_create_tables_and_crud_sqlite_memory():
    """Verify table creation and entity CRUD operations on in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Create a customer
        customer = Customer(
            name="Alice Demo",
            email="alice@example.com",
            company="Acme Corp",
            plan_name=SubscriptionPlan.ENTERPRISE.value,
        )
        session.add(customer)
        session.flush()

        assert len(customer.id) == 36
        assert str(customer).startswith("Customer(")

        # Create a ticket
        ticket = Ticket(
            ticket_number="CD-1002",
            subject="Refund request",
            body="Charged for 8 seats but only using 5.",
            category=Category.BILLING.value,
            severity=Severity.MEDIUM.value,
            customer_id=customer.id,
            channel=Channel.EMAIL.value,
            tags=["billing", "refund"],
        )
        session.add(ticket)
        session.flush()

        assert len(ticket.id) == 36
        assert ticket.customer_id == customer.id
        assert ticket.tags == ["billing", "refund"]

        # Create a message
        msg = TicketMessage(
            ticket_id=ticket.id,
            author_name="Alice Demo",
            body="Please process the refund.",
        )
        session.add(msg)

        # Create a workflow run
        wf_run = WorkflowRun(
            ticket_id=ticket.id,
            status="running",
            state={"step": "classify"},
        )
        session.add(wf_run)
        session.flush()

        # Create workflow event
        event = WorkflowEvent(
            workflow_id=wf_run.id,
            ticket_id=ticket.id,
            node="supervisor",
            event_type="node_start",
            message="Node supervisor started",
            payload={"action": "start"},
        )
        session.add(event)

        # Create approval request
        approval = ApprovalRequest(
            ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            workflow_id=wf_run.id,
            action={"tool": "refund", "amount": 120.00},
            reason="Exceeds $100 auto-refund threshold",
            status="pending",
        )
        session.add(approval)

        # Create resolution action
        action = ResolutionAction(
            ticket_id=ticket.id,
            tool="apply_discount",
            arguments={"discount_pct": 10},
        )
        session.add(action)

        # Create escalation
        esc = Escalation(
            ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            reason="High severity VIP client",
            priority="p1",
            assigned_team="Billing",
        )
        session.add(esc)

        # Create customer memory
        mem = CustomerMemory(
            customer_id=customer.id,
            memory_type="note",
            content="Prefers email notifications",
        )
        session.add(mem)

        # Create audit log
        audit = AuditLog(
            action="ticket_created",
            actor="alice@example.com",
            actor_type="user",
            resource_type="ticket",
            resource_id=ticket.id,
            details={"source": "unit_test"},
        )
        session.add(audit)

        # Create incident
        incident = Incident(
            title="Authentication Outage",
            description="SSO logins failing",
            severity="critical",
            status="investigating",
        )
        session.add(incident)

        # Create product, subscription, workspace, profile, article
        profile = Profile(
            email="agent@clouddesk.internal",
            full_name="Agent Smith",
            role=UserRole.AGENT.value,
        )
        product = Product(
            name="CloudDesk Pro",
            code="CD-PRO",
        )
        sub = Subscription(
            customer_id=customer.id,
            plan=SubscriptionPlan.PRO.value,
        )
        workspace = Workspace(
            customer_id=customer.id,
            name="Acme Primary Workspace",
        )
        article = SupportArticle(
            title="Reset MFA instructions",
            slug="reset-mfa",
            category=Category.LOGIN_ISSUE.value,
            content="Follow these steps to reset MFA...",
        )
        session.add_all([profile, product, sub, workspace, article])
        session.commit()

        # Query customer with tickets
        result = session.execute(
            select(Customer).where(Customer.email == "alice@example.com")
        )
        fetched_customer = result.scalar_one()
        assert fetched_customer.company == "Acme Corp"

        # Query ticket
        t_result = session.execute(
            select(Ticket).where(Ticket.ticket_number == "CD-1002")
        )
        fetched_ticket = t_result.scalar_one()
        assert fetched_ticket.category == "billing"
        assert fetched_ticket.tags == ["billing", "refund"]

        # Query approval
        a_result = session.execute(
            select(ApprovalRequest).where(ApprovalRequest.ticket_id == ticket.id)
        )
        fetched_approval = a_result.scalar_one()
        assert fetched_approval.action == {"tool": "refund", "amount": 120.00}

    engine.dispose()
