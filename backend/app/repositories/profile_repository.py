"""Profile repository for platform users (viewers, agents, admins)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import Profile
from backend.app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    """Repository handling staff and user profile records."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Profile, session)

    async def get_by_email(self, email: str) -> Profile | None:
        """Fetch staff profile by email address."""
        stmt = select(Profile).where(Profile.email == email)
        result = await self._execute(stmt)
        return result.scalars().first()

    async def list_by_role(self, role: str) -> list[Profile]:
        """Fetch all staff profiles with a specific role."""
        stmt = (
            select(Profile)
            .where(Profile.role == role)
            .order_by(Profile.full_name.asc())
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

