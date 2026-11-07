"""Unit tests validating sample data files, 13 scenario tickets, and 15 KB articles."""

import json
from pathlib import Path
import re
import yaml

from backend.app.schemas.common import Category, Channel, Severity

EXPECTED_TICKETS = [
    ("CD-1001", "login_issue", "critical"),
    ("CD-1002", "billing", "medium"),
    ("CD-1003", "api_failure", "high"),
    ("CD-1004", "storage_quota", "medium"),
    ("CD-1005", "security", "critical"),
    ("CD-1006", "other", "critical"),
    ("CD-1007", "workspace_permissions", "medium"),
    ("CD-1008", "integration", "medium"),
    ("CD-1009", "account", "high"),
    ("CD-1010", "feature_request", "low"),
    ("CD-1011", "billing", "high"),
    ("CD-1012", "login_issue", "high"),
    ("CD-1013", "security", "critical"),
]


def test_sample_data_files_exist():
    """Verify all required sample data JSON files exist."""
    base_dir = Path("sample_data")
    assert base_dir.is_dir(), "sample_data directory does not exist"

    required_files = [
        "products.json",
        "customers.json",
        "subscriptions.json",
        "workspaces.json",
        "incidents.json",
        "previous_resolutions.json",
        "tickets.json",
    ]
    for filename in required_files:
        file_path = base_dir / filename
        assert file_path.is_file(), f"Missing sample data file: {filename}"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert len(data) > 0, f"Sample data file {filename} is empty"


def test_knowledge_base_articles_count_and_front_matter():
    """Verify exactly 15 markdown articles exist with valid YAML front matter."""
    kb_dir = Path("sample_data/knowledge_base")
    assert kb_dir.is_dir(), "sample_data/knowledge_base directory does not exist"

    md_files = list(kb_dir.glob("*.md"))
    assert len(md_files) == 15, f"Expected 15 KB articles, found {len(md_files)}"

    fm_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    valid_categories = {c.value for c in Category}

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        match = fm_pattern.match(content)
        assert match is not None, f"Article '{md_file.name}' missing YAML front matter"

        fm = yaml.safe_load(match.group(1))
        assert "title" in fm, f"Article '{md_file.name}' missing 'title'"
        assert "category" in fm, f"Article '{md_file.name}' missing 'category'"
        assert fm["category"] in valid_categories, (
            f"Article '{md_file.name}' category '{fm['category']}' not in Category enum"
        )
        assert "tags" in fm and isinstance(fm["tags"], list), (
            f"Article '{md_file.name}' tags must be a list"
        )
        assert "summary" in fm, f"Article '{md_file.name}' missing 'summary'"

        body = match.group(2).strip()
        assert len(body) > 100, f"Article '{md_file.name}' body is too short"


def test_tickets_json_has_thirteen_exact_scenario_tickets():
    """Verify tickets.json contains CD-1001 through CD-1013 with matching contract categories."""
    tickets_path = Path("sample_data/tickets.json")
    tickets = json.loads(tickets_path.read_text(encoding="utf-8"))

    assert len(tickets) == 13

    ticket_map = {t["ticket_number"]: t for t in tickets}
    valid_categories = {c.value for c in Category}
    valid_severities = {s.value for s in Severity}
    valid_channels = {ch.value for ch in Channel}

    for num, expected_cat, expected_sev in EXPECTED_TICKETS:
        assert num in ticket_map, f"Missing scenario ticket {num}"
        t = ticket_map[num]
        assert t["category"] == expected_cat, (
            f"{num} category mismatch: expected {expected_cat}, got {t['category']}"
        )
        assert t["severity"] == expected_sev, (
            f"{num} severity mismatch: expected {expected_sev}, got {t['severity']}"
        )
        assert t["category"] in valid_categories
        assert t["severity"] in valid_severities
        assert t["channel"] in valid_channels
        assert len(t["body"]) > 20
        assert "customer_id" in t


def test_customers_json_has_eight_customers_across_all_tiers():
    """Verify customers.json has exactly 8 customers covering free, pro, business, enterprise."""
    customers_path = Path("sample_data/customers.json")
    customers = json.loads(customers_path.read_text(encoding="utf-8"))

    assert len(customers) == 8

    tiers = {c["plan_name"] for c in customers}
    assert tiers == {"free", "pro", "business", "enterprise"}

    for c in customers:
        assert "id" in c
        assert "email" in c
        assert "company" in c
        assert "status" in c


def test_seed_sql_contains_seed_statements():
    """Verify database/seed.sql exists and contains valid inserts for tickets and customers."""
    seed_sql = Path("database/seed.sql")
    assert seed_sql.is_file(), "database/seed.sql does not exist"
    content = seed_sql.read_text(encoding="utf-8")

    assert "INSERT INTO profiles" in content
    assert "INSERT INTO customers" in content
    assert "INSERT INTO products" in content
    assert "INSERT INTO subscriptions" in content
    assert "INSERT INTO workspaces" in content
    assert "INSERT INTO tickets" in content
    assert "CD-1001" in content
    assert "CD-1002" in content
    assert "CD-1013" in content

