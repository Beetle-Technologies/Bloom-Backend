from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import ProductStatus
from src.domain.models.product import Product
from src.domain.repositories.product_repository import ProductRepository
from src.domain.schemas.product import ProductCreate, ProductUpdate

logger = get_logger(__name__)


class ProductService:
    """Service for managing products."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repository = ProductRepository(session)

    async def get_product_by_id(self, product_id: GUID) -> Product | None:
        """Get product by ID."""
        return await self.product_repository.find_one_by_and_none(id=product_id)

    async def get_product_by_friendly_id(self, friendly_id: str) -> Product | None:
        """Get product by friendly ID."""
        return await self.product_repository.get_by_friendly_id(friendly_id)

    async def get_products_by_supplier(self, supplier_account_id: GUID) -> list[Product]:
        """Get all products for a specific supplier."""
        return list(await self.product_repository.get_products_by_supplier(supplier_account_id))

    async def get_products_by_status(self, status: ProductStatus) -> list[Product]:
        """Get all products with a specific status."""
        return list(await self.product_repository.get_products_by_status(status))

    async def get_products_by_category(self, category_id: GUID) -> list[Product]:
        """Get all products in a specific category."""
        return list(await self.product_repository.get_products_by_category(category_id))

    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        return await self.product_repository.create(product_data)

    async def update_product(self, product_id: GUID, product_data: ProductUpdate) -> Product | None:
        """Update a product."""
        return await self.product_repository.update(product_id, product_data)

    async def delete_product(self, product_id: GUID) -> bool:
        """Soft delete a product."""
        # Note: This would need to be implemented in the repository if not already available
        # For now, just return False
        return False
