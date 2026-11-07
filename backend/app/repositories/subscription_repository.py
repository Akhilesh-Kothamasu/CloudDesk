"""Subscription repository for customer quotas, tiers, and limits."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import Subscription
from backend.app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository handling customer subscription records."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Subscription, session)

    async def get_by_customer_id(self, customer_id: str) -> Subscription | None:
        """Fetch primary subscription for a customer."""
        stmt = (
            select(Subscription)
            .where(Subscription.customer_id == customer_id)
            .order_by(Subscription.created_at.desc())
        )
        result = await self._execute(stmt)
        return result.scalars().first()

    async def get_active_by_customer_id(self, customer_id: str) -> Subscription | None:
        """Fetch active subscription for a customer."""
        stmt = (
            select(Subscription)
            .where(Subscription.customer_id == customer_id)
            .where(Subscription.status == "active")
            .order_by(Subscription.created_at.desc())
        )
        result = await self._execute(stmt)
        return result.scalars().first()

