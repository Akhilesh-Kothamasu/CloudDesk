"""Support article repository for knowledge base management and RAG retrieval."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.entities import SupportArticle
from backend.app.repositories.base import BaseRepository


class SupportArticleRepository(BaseRepository[SupportArticle]):
    """Repository handling knowledge base articles."""

    def __init__(self, session: AsyncSession | Session) -> None:
        super().__init__(SupportArticle, session)

    async def get_by_slug(self, slug: str) -> SupportArticle | None:
        """Fetch article by unique human-readable slug."""
        stmt = select(SupportArticle).where(SupportArticle.slug == slug)
        result = await self._execute(stmt)
        return result.scalars().first()

    async def list_articles(
        self,
        category: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[SupportArticle], int]:
        """Search and paginate knowledge articles with category filter."""
        base_query = select(SupportArticle)

        if category:
            base_query = base_query.where(SupportArticle.category == category)
        if search:
            pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    SupportArticle.title.ilike(pattern),
                    SupportArticle.summary.ilike(pattern),
                    SupportArticle.content.ilike(pattern),
                    SupportArticle.slug.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_res = await self._execute(count_stmt)
        total = int(count_res.scalar_one() or 0)

        # Fetch page
        page_stmt = (
            base_query.order_by(SupportArticle.title.asc())
            .offset(offset)
            .limit(limit)
        )
        page_res = await self._execute(page_stmt)
        items = list(page_res.scalars().all())

        return items, total

