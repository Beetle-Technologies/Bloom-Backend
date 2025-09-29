from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import ProductStatus
from src.domain.models.product import Product
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.product import ProductCreate, ProductUpdate

logger = get_logger(__name__)


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    """
    Repository for managing products in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    async def get_by_friendly_id(self, friendly_id: str) -> Product | None:
        """Get product by friendly ID."""
        try:
            return await self.find_one_by_or_none(friendly_id=friendly_id)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_repository.get_by_friendly_id:: error while getting product by friendly_id {friendly_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product",
                detail="An error occurred while retrieving product by friendly ID.",
                metadata={"friendly_id": friendly_id},
            ) from e

    async def get_products_by_supplier(self, supplier_account_id: GUID) -> Sequence[Product]:
        """Get all products for a specific supplier."""
        try:
            query = select(Product).where(Product.supplier_account_id == supplier_account_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_repository.get_products_by_supplier:: error while getting products for supplier {supplier_account_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve products",
                detail="An error occurred while retrieving products for supplier.",
                metadata={"supplier_account_id": supplier_account_id},
            ) from e

    async def get_products_by_status(self, status: ProductStatus) -> Sequence[Product]:
        """Get all products with a specific status."""
        try:
            query = select(Product).where(Product.status == status)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_repository.get_products_by_status:: error while getting products by status {status}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve products",
                detail="An error occurred while retrieving products by status.",
                metadata={"status": status},
            ) from e

    async def get_products_by_category(self, category_id: GUID) -> Sequence[Product]:
        """Get all products in a specific category."""
        try:
            query = select(Product).where(Product.category_id == category_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_repository.get_products_by_category:: error while getting products by category {category_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve products",
                detail="An error occurred while retrieving products by category.",
                metadata={"category_id": category_id},
            ) from e
