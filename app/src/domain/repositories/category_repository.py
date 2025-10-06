from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.domain.models.category import Category
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import CategoryCreate, CategoryUpdate

logger = get_logger(__name__)


class CategoryRepository(BaseRepository[Category, CategoryCreate, CategoryUpdate]):
    """
    Repository for managing categories in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Category, session)

    async def find_by_title(self, title: str) -> Category | None:
        """
        Find a category by its title.

        Args:
            title: The category title to search for

        Returns:
            Category | None: The found category or None
        """
        return await self.find_one_by_and_none(title=title)

    async def find_active_categories(self) -> list[Category]:
        """
        Find all active categories.

        Returns:
            list[Category]: List of active categories
        """
        query = select(self.model).where(self.model.is_active == True)  # noqa: E712
        result = await self.session.exec(query)
        return list(result.all())

    async def find_by_parent_id(self, parent_id: str | None) -> list[Category]:
        """
        Find all categories with a specific parent ID.

        Args:
            parent_id: The parent ID to search for (None for root categories)

        Returns:
            list[Category]: List of categories with the specified parent
        """
        query = select(self.model).where(self.model.parent_id == parent_id)
        result = await self.session.exec(query)
        return list(result.all())

    async def find_root_categories(self) -> list[Category]:
        """
        Find all root categories (categories without a parent).

        Returns:
            list[Category]: List of root categories
        """
        return await self.find_by_parent_id(None)

    async def create_if_not_exists(self, schema: CategoryCreate) -> Category:
        """
        Create a category if it doesn't already exist.

        Args:
            schema (CategoryCreate): The category data

        Returns:
            Category: The existing or newly created category
        """
        existing = await self.find_by_title(schema.title)

        if existing:
            return existing

        return await self.create(schema)

    async def bulk_create_if_not_exists(self, schemas: list[CategoryCreate]) -> list[Category]:
        """
        Bulk create categories if they don't already exist.

        Args:
            schemas (list[CategoryCreate]): List of category data to create

        Returns:
            list[Category]: List of existing or newly created categories
        """
        results = []
        for schema in schemas:
            result = await self.create_if_not_exists(schema)
            results.append(result)
        return results
