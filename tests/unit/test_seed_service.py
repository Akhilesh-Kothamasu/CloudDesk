"""Unit tests for seed service and demo bootstrap logic."""

from typing import Any, Coroutine
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.core.database import Base
from backend.app.models.entities import (
    Customer,
    Incident,
    Product,
    Profile,
    Subscription,
    SupportArticle,
    Ticket,
    TicketMessage,
    Workspace,
)
from backend.app.services.seed_service import bootstrap_demo_data


def run_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute a coroutine synchronously without creating socket loopback overhead."""
    while True:
        try:
            coro.send(None)
        except StopIteration as e:
            return e.value


@pytest.fixture
def db_session():
    """In-memory SQLite database session fixture."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_bootstrap_demo_data_empty_db(db_session):
    """Verify bootstrap_demo_data populates all expected entities when database is empty."""
    stats = run_sync(bootstrap_demo_data(session=db_session, force=False))

    assert stats["profiles"] == 3
    assert stats["products"] == 4
    assert stats["customers"] == 8
    assert stats["subscriptions"] == 8
    assert stats["workspaces"] == 8
    assert stats["incidents"] == 2
    assert stats["articles"] == 15
    assert stats["tickets"] == 13
    assert stats["messages"] == 13

    # Check database rows
    profiles = db_session.execute(select(Profile)).scalars().all()
    assert len(profiles) == 3

    customers = db_session.execute(select(Customer)).scalars().all()
    assert len(customers) == 8

    tickets = db_session.execute(select(Ticket)).scalars().all()
    assert len(tickets) == 13

    articles = db_session.execute(select(SupportArticle)).scalars().all()
    assert len(articles) == 15


def test_bootstrap_demo_data_idempotent(db_session):
    """Verify running bootstrap_demo_data twice does not duplicate rows."""
    stats1 = run_sync(bootstrap_demo_data(session=db_session, force=False))
    assert stats1["tickets"] == 13

    # Second run without force
    stats2 = run_sync(bootstrap_demo_data(session=db_session, force=False))
    assert stats2["tickets"] == 0
    assert stats2["customers"] == 0

    tickets = db_session.execute(select(Ticket)).scalars().all()
    assert len(tickets) == 13

    customers = db_session.execute(select(Customer)).scalars().all()
    assert len(customers) == 8


def test_seeded_ticket_cd1002_and_cd1005(db_session):
    """Verify specific scenario tickets CD-1002 (Refund) and CD-1005 (Breach)."""
    run_sync(bootstrap_demo_data(session=db_session, force=False))

    # CD-1002: Refund request
    stmt_1002 = select(Ticket).where(Ticket.ticket_number == "CD-1002")
    t1002 = db_session.execute(stmt_1002).scalars().first()
    assert t1002 is not None
    assert t1002.category == "billing"
    assert t1002.severity == "medium"
    assert "8 seats" in t1002.body

    # Initial message in thread
    msg_stmt = select(TicketMessage).where(TicketMessage.ticket_id == t1002.id)
    msg = db_session.execute(msg_stmt).scalars().first()
    assert msg is not None
    assert msg.role == "customer"
    assert msg.body == t1002.body

    # CD-1005: Security breach escalation
    stmt_1005 = select(Ticket).where(Ticket.ticket_number == "CD-1005")
    t1005 = db_session.execute(stmt_1005).scalars().first()
    assert t1005 is not None
    assert t1005.category == "security"
    assert t1005.severity == "critical"
    assert t1005.escalation_required is True

