"""Pytest test harness configuration for CloudDesk.

Configures offline environment variables before application or settings imports,
and provides common fixtures for API, configuration, and authentication.
"""

from collections.abc import Generator
import os
from typing import Any

# CRITICAL: Set offline environment variables BEFORE importing app or settings
os.environ["DEMO_MODE"] = "true"
os.environ["ENVIRONMENT"] = "development"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["LLM_API_KEY"] = ""
os.environ["LLM_MODEL"] = "fake"
os.environ["VECTOR_STORE"] = "memory"
os.environ["USE_FAKE_REDIS"] = "true"
os.environ["REDIS_URL"] = ""
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["CHECKPOINT_DB_PATH"] = ":memory:"
os.environ["JWT_SECRET"] = "demo-test-secret-key-offline"
os.environ["LOG_LEVEL"] = "DEBUG"

import pytest
from fastapi import FastAPI

from backend.app.core.config import Settings, get_settings
from backend.app.main import create_app

# Clear cached settings so environment variables take effect
get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_test_environment() -> Generator[None, None, None]:
    """Ensure cached settings and dependency overrides are reset for each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings() -> Settings:
    """Provide a fresh instance of offline test settings."""
    return get_settings()


@pytest.fixture
def app() -> FastAPI:
    """Provide an isolated FastAPI application instance for testing."""
    return create_app()


@pytest.fixture
def agent_headers() -> dict[str, str]:
    """Authorization headers for agent role."""
    return {"Authorization": "Bearer demo-agent-token"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    """Authorization headers for admin role."""
    return {"Authorization": "Bearer demo-admin-token"}


@pytest.fixture
def viewer_headers() -> dict[str, str]:
    """Authorization headers for viewer role."""
    return {"Authorization": "Bearer demo-viewer-token"}

