"""Tests for .env.example coverage, hygiene, and Makefile targets."""

from pathlib import Path
import re
import subprocess

from backend.app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_env_example_exists():
    """Verify .env.example exists at the project root."""
    env_example = REPO_ROOT / ".env.example"
    assert env_example.is_file(), ".env.example must exist at repo root"


def test_env_example_covers_all_settings_fields():
    """Verify every field defined in Settings is represented in .env.example."""
    env_example_path = REPO_ROOT / ".env.example"
    content = env_example_path.read_text(encoding="utf-8")

    # Extract all variable names defined in .env.example (format: VAR_NAME=...)
    defined_vars = set(re.findall(r"^[A-Z0-9_]+(?==)", content, flags=re.MULTILINE))

    settings_fields = set(Settings.model_fields.keys())

    missing = settings_fields - defined_vars
    assert not missing, f"Variables missing from .env.example: {missing}"


def test_env_example_contains_only_placeholders():
    """Verify .env.example does not contain real API keys or sensitive secrets."""
    env_example_path = REPO_ROOT / ".env.example"
    content = env_example_path.read_text(encoding="utf-8")

    # Values must not start with real API key prefixes (e.g. sk-..., ghp_...)
    assert not re.search(r"=\s*sk-[A-Za-z0-9]{20,}", content), (
        "Real secret key found in .env.example"
    )
    assert not re.search(r"=\s*ghp_[A-Za-z0-9]{20,}", content), (
        "Real GitHub token found in .env.example"
    )

    # Passwords should be empty or contain placeholder text
    for line in content.splitlines():
        if "PASSWORD" in line and "=" in line:
            val = line.split("=", 1)[1].strip()
            assert "super" not in val and "real" not in val


def test_no_env_file_tracked_in_git():
    """Ensure no real .env file is tracked in Git."""
    try:
        result = subprocess.run(
            ["git", "ls-files", ".env"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "", "A real .env file must never be committed to git"
    except FileNotFoundError:
        # If git binary is not found in test environment, verify .gitignore excludes it
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert ".env" in gitignore


def test_makefile_exists_and_contains_standard_targets():
    """Verify Makefile exists and contains all required targets from CLAUDE.md §14."""
    makefile_path = REPO_ROOT / "Makefile"
    assert makefile_path.is_file(), "Makefile must exist at repo root"

    content = makefile_path.read_text(encoding="utf-8")
    required_targets = [
        "setup",
        "backend",
        "test",
        "lint",
        "seed",
        "ingest",
        "demo",
        "mcp",
        "terraform-validate",
        "smoke",
    ]

    for target in required_targets:
        pattern = rf"^{re.escape(target)}:"
        assert re.search(pattern, content, flags=re.MULTILINE), (
            f"Target '{target}' missing from Makefile"
        )
