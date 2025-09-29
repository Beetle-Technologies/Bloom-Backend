from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.product_item import ProductItem
from src.domain.repositories.product_item_repository import ProductItemRepository
from src.domain.schemas import ProductItemCreate, ProductItemUpdate

from app.src.libs.query_engine.schemas import BaseQueryEngineParams

logger = get_logger(__name__)


class ProductItemService:
    """Service for managing product items."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_item_repository = ProductItemRepository(session)

    async def get_product_item(self, product_item_id: GUID) -> ProductItem | None:
        try:
            return await self.product_item_repository.find_one_by(id=product_item_id)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_item_service.get_product_item:: error while getting product item by id {product_item_id}: {e}"
            )
            raise errors.ServiceError(
                detail="Failed to retrieve product item",
                status=500,
            ) from e

    async def get_product_item_by_friendly_id(self, friendly_id: str) -> ProductItem | None:
        try:
            return await self.product_item_repository.get_by_friendly_id(friendly_id)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_item_service.get_product_item_by_friendly_id:: error while getting product item by friendly id {friendly_id}: {e}"
            )
            raise errors.ServiceError(
                detail="Failed to retrieve product item",
                status=500,
            ) from e

    async def create_product_item(self, product_item_data: ProductItemCreate) -> ProductItem:
        try:
            existing_product_item_by_product_id = await self.product_item_repository.query(
                params=BaseQueryEngineParams(filters={"product_id": product_item_data.product_id})
            )
            if existing_product_item_by_product_id:
                raise errors.ServiceError(
                    message="Product item already exists for this product",
                    detail=f"Product item for product_id:{product_item_data.product_id} already exists",
                )

            return await self.product_item_repository.create(product_item_data)
        except errors.ServiceError as e:
            logger.exception(f"src.domain.services.product_item_service.create_product_item:: {e}")
            raise e
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_item_service.create_product_item:: error while creating product item: {e}"
            )
            raise errors.ServiceError(
                message="Failed to create product item",
                detail="An error occurred while creating the product item.",
                status=500,
            ) from e

    async def update_product_item(
        self, product_item_id: GUID, product_item_data: ProductItemUpdate
    ) -> ProductItem | None:

        try:
            return await self.product_item_repository.update(product_item_id, product_item_data)
        except errors.ServiceError as se:
            logger.exception(f"src.domain.services.product_item_service.update_product_item:: {se}")
            raise se
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.product_item_service.update_product_item:: error while updating product item: {e}"
            )
            raise errors.ServiceError(
                message="Failed to update product item",
                detail="An error occurred while updating the product item.",
                status=500,
            ) from e
