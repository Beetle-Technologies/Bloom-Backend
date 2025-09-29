from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import ProductItemRequestStatus
from src.domain.models.product_item_request import ProductItemRequest
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.product_item_request import ProductItemRequestCreate, ProductItemRequestUpdate

logger = get_logger(__name__)


class ProductItemRequestRepository(
    BaseRepository[ProductItemRequest, ProductItemRequestCreate, ProductItemRequestUpdate]
):
    """
    Repository for managing product item requests in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProductItemRequest, session)

    async def get_requests_by_seller(self, seller_account_id: GUID) -> Sequence[ProductItemRequest]:
        """Get all requests from a specific seller."""
        try:
            query = select(ProductItemRequest).where(ProductItemRequest.seller_account_id == seller_account_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_request_repository.get_requests_by_seller:: error while getting requests for seller {seller_account_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product item requests",
                detail="An error occurred while retrieving product item requests for seller.",
                metadata={"seller_account_id": seller_account_id},
            ) from e

    async def get_requests_by_supplier(self, supplier_account_id: GUID) -> Sequence[ProductItemRequest]:
        """Get all requests to a specific supplier."""
        try:
            query = select(ProductItemRequest).where(ProductItemRequest.supplier_account_id == supplier_account_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_request_repository.get_requests_by_supplier:: error while getting requests for supplier {supplier_account_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product item requests",
                detail="An error occurred while retrieving product item requests for supplier.",
                metadata={"supplier_account_id": supplier_account_id},
            ) from e

    async def get_requests_by_product(self, product_id: GUID) -> Sequence[ProductItemRequest]:
        """Get all requests for a specific product."""
        try:
            query = select(ProductItemRequest).where(ProductItemRequest.product_id == product_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_request_repository.get_requests_by_product:: error while getting requests for product {product_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product item requests",
                detail="An error occurred while retrieving product item requests for product.",
                metadata={"product_id": product_id},
            ) from e

    async def get_requests_by_status(self, status: ProductItemRequestStatus) -> Sequence[ProductItemRequest]:
        """Get all requests with a specific status."""
        try:
            query = select(ProductItemRequest).where(ProductItemRequest.status == status)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.product_item_request_repository.get_requests_by_status:: error while getting requests by status {status}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve product item requests",
                detail="An error occurred while retrieving product item requests by status.",
                metadata={"status": status},
            ) from e
