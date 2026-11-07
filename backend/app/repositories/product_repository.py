"""Product repository for catalog and tier lookup."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import Product
from backend.app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository handling product catalog items."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(Product, session)

    async def get_by_code(self, code: str) -> Product | None:
        """Fetch product by unique product code (e.g. CD-PRO)."""
        stmt = select(Product).where(Product.code == code)
        result = await self._execute(stmt)
        return result.scalars().first()

    async def list_products(self) -> list[Product]:
        """Fetch all product items ordered by name."""
        stmt = select(Product).order_by(Product.name.asc())
        result = await self._execute(stmt)
        return list(result.scalars().all())

