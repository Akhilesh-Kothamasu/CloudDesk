"""Customer repository for account data, search, and context lookup."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from backend.app.models.entities import Customer
from backend.app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Repository handling customer accounts and profile queries."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Customer, session)

    async def get_by_email(self, email: str) -> Customer | None:
        """Fetch customer record by email address."""
        stmt = select(Customer).where(Customer.email == email)
        result = await self._execute(stmt)
        return result.scalars().first()

    async def search_customers(
        self,
        search: str | None = None,
        plan_name: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Customer], int]:
        """Search and paginate customers by keyword, plan, and status."""
        base_query = select(Customer)

        if plan_name:
            base_query = base_query.where(Customer.plan_name == plan_name)
        if status:
            base_query = base_query.where(Customer.status == status)
        if search:
            pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Customer.name.ilike(pattern),
                    Customer.email.ilike(pattern),
                    Customer.company.ilike(pattern),
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_res = await self._execute(count_stmt)
        total = int(count_res.scalar_one() or 0)

        # Fetch page
        page_stmt = (
            base_query.order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        page_res = await self._execute(page_stmt)
        items = list(page_res.scalars().all())

        return items, total

    async def get_customer_context(self, customer_id: str) -> Customer | None:
        """Fetch customer with subscriptions, workspaces, and memory eagerly loaded."""
        stmt = (
            select(Customer)
            .where(Customer.id == customer_id)
            .options(
                selectinload(Customer.subscriptions),
                selectinload(Customer.workspaces),
                selectinload(Customer.tickets),
                selectinload(Customer.customer_memory),
            )
        )
        result = await self._execute(stmt)
        return result.scalars().first()

