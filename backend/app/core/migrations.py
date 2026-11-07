"""Migration discovery, validation, and runner for CloudDesk.

Manages ordered SQL migrations located in `database/migrations/` to track schema
evolution in PostgreSQL / Supabase.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class Migration:
    """Represents a discrete SQL migration file."""

    version: int
    name: str
    path: Path
    sql: str


def get_migrations_directory() -> Path:
    """Return the resolved path to the migrations directory."""
    # Look for database/migrations relative to repo root
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "database" / "migrations"
        if candidate.is_dir():
            return candidate
    # Fallback to repo root default
    return Path("database/migrations").resolve()


def get_migrations(migrations_dir: Path | None = None) -> list[Migration]:
    """Discover, parse, and sort all migration files in alphanumeric order."""
    directory = migrations_dir or get_migrations_directory()
    if not directory.exists():
        return []

    pattern = re.compile(r"^(\d{4})_(.+)\.sql$")
    migrations: list[Migration] = []

    for file_path in sorted(directory.glob("*.sql")):
        match = pattern.match(file_path.name)
        if match:
            version_int = int(match.group(1))
            name = match.group(2)
            sql_content = file_path.read_text(encoding="utf-8")
            migrations.append(
                Migration(
                    version=version_int,
                    name=name,
                    path=file_path,
                    sql=sql_content,
                )
            )

    return sorted(migrations, key=lambda m: m.version)


def validate_migrations(migrations_dir: Path | None = None) -> list[str]:
    """Validate sequential numbering, naming format, and content sanity.

    Returns a list of validation error descriptions. An empty list signifies success.
    """
    directory = migrations_dir or get_migrations_directory()
    if not directory.exists():
        return [f"Migrations directory not found: {directory}"]

    files = sorted(directory.glob("*.sql"))
    if not files:
        return ["No migration files found in migrations directory"]

    errors: list[str] = []
    pattern = re.compile(r"^(\d{4})_(.+)\.sql$")
    expected_version = 1

    for file_path in files:
        match = pattern.match(file_path.name)
        if not match:
            errors.append(
                f"File '{file_path.name}' does not follow '000N_<name>.sql' naming convention"
            )
            continue

        version = int(match.group(1))
        if version != expected_version:
            errors.append(
                f"Expected migration version {expected_version:04d}, but found '{file_path.name}'"
            )

        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            errors.append(f"Migration file '{file_path.name}' is empty")

        expected_version += 1

    return errors

