from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.product import Product
from src.domain.repositories.product_repository import ProductRepository
from src.domain.schemas.product import ProductCreate, ProductUpdate

logger = get_logger(__name__)


class ProductService:
    """Service for managing products."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repository = ProductRepository(session)

    async def get_product(self, product_id: GUID) -> Product | None:
        """Get a product by ID."""
        try:
            return await self.product_repository.find_one_by(id=product_id)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_service.get_product:: error while getting product by id {product_id}: {e}"
            )
            raise errors.ServiceError(
                detail="Failed to retrieve product",
            ) from e

    async def get_product_by_friendly_id(self, friendly_id: str) -> Product | None:
        """Get a product by friendly ID."""
        try:
            return await self.product_repository.get_by_friendly_id(friendly_id)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_service.get_product_by_friendly_id:: error while getting product by friendly id {friendly_id}: {e}"
            )
            raise errors.ServiceError(
                detail="Failed to retrieve product",
            ) from e

    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        try:
            return await self.product_repository.create(product_data)
        except errors.DatabaseError as e:
            logger.exception(f"src.domain.services.product_service.create_product:: error while creating product: {e}")
            raise errors.ServiceError(
                message="Failed to create product",
                detail="An error occurred while creating the product.",
            ) from e

    async def update_product(self, product_id: GUID, product_data: ProductUpdate) -> Product | None:
        """Update a product."""
        try:
            return await self.product_repository.update(product_id, product_data)
        except errors.DatabaseError as e:
            logger.exception(f"src.domain.services.product_service.update_product:: error while updating product: {e}")
            raise errors.ServiceError(
                message="Failed to update product",
                detail="An error occurred while updating the product.",
            ) from e

    async def get_products_by_supplier(self, supplier_account_id: GUID) -> list[Product]:
        """Get all products for a supplier."""
        try:
            result = await self.product_repository.get_products_by_supplier(supplier_account_id)
            return list(result)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_service.get_products_by_supplier:: error while getting products for supplier {supplier_account_id}: {e}"
            )
            raise errors.ServiceError(
                detail="Failed to retrieve products",
            ) from e
