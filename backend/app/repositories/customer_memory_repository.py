"""Customer memory repository for persistent customer context and preference notes."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import CustomerMemory
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.common import MemoryType


class CustomerMemoryRepository(BaseRepository[CustomerMemory]):
    """Repository handling long-term customer memory notes."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(CustomerMemory, session)

    async def get_by_customer_id(
        self, customer_id: str, limit: int = 10
    ) -> list[CustomerMemory]:
        """Fetch latest memory notes for a customer."""
        stmt = (
            select(CustomerMemory)
            .where(CustomerMemory.customer_id == customer_id)
            .order_by(CustomerMemory.created_at.desc())
            .limit(limit)
        )
        result = await self._execute(stmt)
        return list(result.scalars().all())

    async def create_memory(
        self,
        customer_id: str,
        content: str,
        memory_type: str = MemoryType.NOTE.value,
        source_ticket_id: str | None = None,
    ) -> CustomerMemory:
        """Create and persist a new customer memory note."""
        memory = CustomerMemory(
            customer_id=customer_id,
            content=content,
            memory_type=memory_type,
            source_ticket_id=source_ticket_id,
        )
        self.session.add(memory)
        await self._flush()
        return memory

