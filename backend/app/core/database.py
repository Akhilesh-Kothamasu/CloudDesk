"""Database engine, session management, and Base for CloudDesk.

Supports asynchronous SQLite (offline/demo) and PostgreSQL (cloud/Supabase).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base class for all CloudDesk SQLAlchemy models."""

    def __repr__(self) -> str:
        attrs = ", ".join(
            f"{k}={v!r}"
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({attrs})"


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    """Return or initialize the singleton AsyncEngine."""
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        db_url = settings.DATABASE_URL

        # Ensure directory exists for local file-based SQLite databases
        if db_url.startswith("sqlite+aiosqlite:///") and not db_url.startswith(
            "sqlite+aiosqlite:///:memory:"
        ):
            db_path = db_url.replace("sqlite+aiosqlite:///", "")
            parent_dir = Path(db_path).parent
            if parent_dir and not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

        connect_args: dict[str, Any] = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        _engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            connect_args=connect_args,
        )
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return session factory, ensuring engine is initialized."""
    get_async_engine()
    assert _session_factory is not None
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for async database session (outside HTTP requests)."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables(engine: AsyncEngine | None = None) -> None:
    """Create all database tables registered on Base.metadata."""
    target_engine = engine or get_async_engine()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(engine: AsyncEngine | None = None) -> None:
    """Drop all database tables registered on Base.metadata."""
    target_engine = engine or get_async_engine()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def reset_engine() -> None:
    """Reset engine and session factory singletons (useful in testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None

