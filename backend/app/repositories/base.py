"""Base repository providing generic CRUD operations for SQLAlchemy models.

Compatible with both AsyncSession (FastAPI production / async engines) and
Session (synchronous SQLite harnesses).
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic repository providing common database CRUD methods."""

    def __init__(self, model: type[ModelT], session: AsyncSession | Session) -> None:
        self.model = model
        self.session = session

    async def _execute(self, stmt: Any) -> Any:
        """Execute a statement on either an AsyncSession or Session."""
        if isinstance(self.session, AsyncSession):
            return await self.session.execute(stmt)
        return self.session.execute(stmt)

    async def _flush(self) -> None:
        """Flush pending changes to the database."""
        if isinstance(self.session, AsyncSession):
            await self.session.flush()
        else:
            self.session.flush()

    async def _commit(self) -> None:
        """Commit the current transaction."""
        if isinstance(self.session, AsyncSession):
            await self.session.commit()
        else:
            self.session.commit()

    async def _rollback(self) -> None:
        """Roll back the current transaction."""
        if isinstance(self.session, AsyncSession):
            await self.session.rollback()
        else:
            self.session.rollback()

    async def get_by_id(self, id_: str) -> ModelT | None:
        """Fetch a single record by primary key."""
        if isinstance(self.session, AsyncSession):
            return await self.session.get(self.model, id_)
        return self.session.get(self.model, id_)

    async def list_all(self, offset: int = 0, limit: int = 100) -> list[ModelT]:
        """Fetch a page of records."""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total rows for this entity."""
        stmt = select(func.count()).select_from(self.model)
        result = await self._execute(stmt)
        return int(result.scalar_one() or 0)

    async def create(self, entity: ModelT) -> ModelT:
        """Add and flush an entity."""
        self.session.add(entity)
        await self._flush()
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Flush changes to an existing entity."""
        await self._flush()
        return entity

    async def delete(self, id_: str) -> bool:
        """Delete an entity by primary key."""
        entity = await self.get_by_id(id_)
        if entity is None:
            return False
        if isinstance(self.session, AsyncSession):
            await self.session.delete(entity)
        else:
            self.session.delete(entity)
        await self._flush()
        return True

