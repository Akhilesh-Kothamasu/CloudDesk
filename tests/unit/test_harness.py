"""Tests for the offline pytest harness and fixtures."""

import os
from fastapi import FastAPI
import pytest

from backend.app.core.config import Settings


def test_offline_env_vars_active():
    """Verify conftest sets offline environment variables."""
    assert os.environ.get("DEMO_MODE") == "true"
    assert os.environ.get("LLM_PROVIDER") == "fake"
    assert os.environ.get("VECTOR_STORE") == "memory"
    assert os.environ.get("USE_FAKE_REDIS") == "true"
    assert os.environ.get("CHECKPOINT_DB_PATH") == ":memory:"


def test_settings_fixture(test_settings: Settings):
    """Verify test_settings fixture provides offline defaults."""
    assert test_settings.DEMO_MODE is True
    assert test_settings.LLM_PROVIDER == "fake"
    assert test_settings.VECTOR_STORE == "memory"
    assert test_settings.USE_FAKE_REDIS is True
    assert test_settings.CHECKPOINT_DB_PATH == ":memory:"
    assert test_settings.DATABASE_URL == "sqlite+aiosqlite:///:memory:"


def test_auth_headers_fixtures(
    agent_headers: dict[str, str],
    admin_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """Verify auth header fixtures provide bearer token headers."""
    assert "Authorization" in agent_headers
    assert agent_headers["Authorization"].startswith("Bearer ")

    assert "Authorization" in admin_headers
    assert admin_headers["Authorization"].startswith("Bearer ")

    assert "Authorization" in viewer_headers
    assert viewer_headers["Authorization"].startswith("Bearer ")


def test_app_fixture(app: FastAPI):
    """Verify app fixture provides configured FastAPI instance."""
    assert isinstance(app, FastAPI)
    assert app.title == "CloudDesk"

