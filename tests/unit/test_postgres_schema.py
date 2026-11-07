"""Unit tests for PostgreSQL schema, RLS policies, and migrations."""

from pathlib import Path
import re

import pytest

from backend.app.core.database import Base
from backend.app.core.migrations import (
    get_migrations,
    get_migrations_directory,
    validate_migrations,
)
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

EXPECTED_TABLES = {
    "profiles",
    "customers",
    "products",
    "subscriptions",
    "workspaces",
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

TABLES_WITH_UPDATED_AT = {
    "profiles",
    "customers",
    "products",
    "subscriptions",
    "workspaces",
    "tickets",
    "support_articles",
    "incidents",
    "workflow_runs",
}


def test_schema_sql_exists():
    """Verify database/schema.sql exists and is non-empty."""
    schema_path = Path("database/schema.sql")
    assert schema_path.exists(), "database/schema.sql does not exist"
    content = schema_path.read_text(encoding="utf-8")
    assert len(content) > 500, "database/schema.sql is suspiciously short"


def test_schema_sql_declares_all_16_tables():
    """Verify database/schema.sql declares CREATE TABLE for all 16 platform tables."""
    schema_path = Path("database/schema.sql")
    content = schema_path.read_text(encoding="utf-8")

    matches = re.findall(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z_]+)\s*\(",
        content,
        re.IGNORECASE,
    )
    declared_tables = set(matches)

    assert declared_tables == EXPECTED_TABLES
    assert len(declared_tables) == 16


def test_schema_columns_match_sqlalchemy_entities():
    """Verify that all columns in SQLAlchemy entities exist in schema.sql."""
    schema_path = Path("database/schema.sql")
    content = schema_path.read_text(encoding="utf-8")

    # Parse table blocks from schema.sql
    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z_]+)\s*\((.*?)\);",
        re.DOTALL | re.IGNORECASE,
    )
    schema_tables: dict[str, set[str]] = {}
    for table_name, block in table_pattern.findall(content):
        # Extract column names (first word of each line inside CREATE TABLE)
        cols = set()
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("--") or line.startswith("CONSTRAINT"):
                continue
            first_token = line.split()[0].lower()
            if first_token not in {"primary", "foreign", "unique", "check"}:
                cols.add(first_token)
        schema_tables[table_name] = cols

    # Verify every table and column registered in SQLAlchemy metadata
    for table_name, table_obj in Base.metadata.tables.items():
        assert table_name in schema_tables, f"Table {table_name} missing from schema.sql"
        schema_cols = schema_tables[table_name]
        for col in table_obj.columns:
            assert col.name in schema_cols, (
                f"Column '{col.name}' of table '{table_name}' missing from database/schema.sql"
            )


def test_schema_triggers_and_updated_at():
    """Verify set_updated_at trigger function and triggers for tables with updated_at."""
    schema_path = Path("database/schema.sql")
    content = schema_path.read_text(encoding="utf-8")

    assert "CREATE OR REPLACE FUNCTION set_updated_at()" in content

    for table in TABLES_WITH_UPDATED_AT:
        trigger_statement = f"CREATE TRIGGER trg_{table}_updated_at"
        assert trigger_statement in content, f"Trigger missing for table '{table}'"


def test_schema_foreign_keys_and_indexes():
    """Verify foreign keys and key indexes are defined in schema.sql."""
    schema_path = Path("database/schema.sql")
    content = schema_path.read_text(encoding="utf-8")

    # Check essential foreign key references
    assert "REFERENCES customers(id)" in content
    assert "REFERENCES tickets(id)" in content
    assert "REFERENCES workflow_runs(id)" in content
    assert "REFERENCES profiles(id)" in content

    # Check essential indexes
    assert "CREATE INDEX IF NOT EXISTS idx_tickets_ticket_number" in content
    assert "CREATE INDEX IF NOT EXISTS idx_tickets_customer_id" in content
    assert "CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id" in content
    assert "CREATE INDEX IF NOT EXISTS idx_support_articles_slug" in content
    assert "CREATE INDEX IF NOT EXISTS idx_audit_logs_actor" in content


def test_rls_policies_sql_exists_and_covers_all_tables():
    """Verify database/rls_policies.sql enables RLS on all 16 tables with proper policies."""
    rls_path = Path("database/rls_policies.sql")
    assert rls_path.exists(), "database/rls_policies.sql does not exist"
    content = rls_path.read_text(encoding="utf-8")

    # Verify RLS enabled on all 16 tables
    for table in EXPECTED_TABLES:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;" in content, (
            f"RLS not enabled on table '{table}'"
        )
        assert f'ON {table} TO service_role' in content, (
            f"service_role policy missing for table '{table}'"
        )
        assert f'ON {table}' in content

    # Verify role helper function
    assert "CREATE OR REPLACE FUNCTION auth_user_role()" in content

    # Verify staff authenticated policies
    assert "TO authenticated" in content

    # Verify anon policies for public articles and incidents
    assert "ON support_articles FOR SELECT TO anon" in content
    assert "ON incidents FOR SELECT TO anon" in content


def test_migrations_discovery_and_validation():
    """Verify migrations directory, sequential numbering, and integrity."""
    migrations_dir = get_migrations_directory()
    assert migrations_dir.is_dir(), f"Directory not found: {migrations_dir}"

    validation_errors = validate_migrations(migrations_dir)
    assert not validation_errors, f"Migration validation failed: {validation_errors}"

    migrations = get_migrations(migrations_dir)
    assert len(migrations) >= 2, "Expected at least 2 migrations"
    assert migrations[0].version == 1
    assert migrations[0].name == "initial_schema"
    assert migrations[1].version == 2
    assert migrations[1].name == "rls_policies"

