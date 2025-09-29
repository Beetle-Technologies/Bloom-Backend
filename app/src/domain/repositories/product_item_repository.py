from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import ProductStatus
from src.domain.models.product_item import ProductItem
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.product_item import ProductItemCreate, ProductItemUpdate

logger = get_logger(__name__)


class ProductItemRepository(BaseRepository[ProductItem, ProductItemCreate, ProductItemUpdate]):
    """
    Repository for managing product items in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProductItem, session)

    async def get_by_friendly_id(self, friendly_id: str) -> ProductItem | None:
        """Get product item by friendly ID."""
        try:
            return await self.find_one_by_or_none(friendly_id=friendly_id)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_repository.get_by_friendly_id:: error while getting product item by friendly_id {friendly_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product item",
                detail="An error occurred while retrieving product item by friendly ID.",
                metadata={"friendly_id": friendly_id},
            ) from e

    async def get_items_by_product(self, product_id: GUID) -> Sequence[ProductItem]:
        """Get all product items for a specific product."""
        try:
            query = select(ProductItem).where(ProductItem.product_id == product_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_repository.get_items_by_product:: error while getting items for product {product_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product items",
                detail="An error occurred while retrieving product items for product.",
                metadata={"product_id": product_id},
            ) from e

    async def get_items_by_status(self, status: ProductStatus) -> Sequence[ProductItem]:
        """Get all product items with a specific status."""
        try:
            query = select(ProductItem).where(ProductItem.status == status)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_repository.get_items_by_status:: error while getting items by status {status}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product items",
                detail="An error occurred while retrieving product items by status.",
                metadata={"status": status},
            ) from e
