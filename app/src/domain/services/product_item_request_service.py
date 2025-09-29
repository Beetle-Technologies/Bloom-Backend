from __future__ import annotations

from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import ProductItemRequestStatus
from src.domain.models.product_item_request import ProductItemRequest
from src.domain.repositories.product_item_request_repository import ProductItemRequestRepository
from src.domain.schemas.product_item_request import ProductItemRequestCreate, ProductItemRequestUpdate

logger = get_logger(__name__)


class ProductItemRequestService:
    """Service for managing product item requests."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_item_request_repository = ProductItemRequestRepository(session)

    async def get_request_by_id(self, request_id: GUID) -> ProductItemRequest | None:
        """Get product item request by ID."""
        return await self.product_item_request_repository.find_one_by_and_none(id=request_id)

    async def get_requests_by_seller(self, seller_account_id: GUID) -> Sequence[ProductItemRequest]:
        """Get all requests from a specific seller."""
        return await self.product_item_request_repository.get_requests_by_seller(seller_account_id)

    async def get_requests_by_supplier(self, supplier_account_id: GUID) -> Sequence[ProductItemRequest]:
        """Get all requests to a specific supplier."""
        return await self.product_item_request_repository.get_requests_by_supplier(supplier_account_id)

    async def get_requests_by_product(self, product_id: GUID) -> Sequence[ProductItemRequest]:
        """Get all requests for a specific product."""
        return await self.product_item_request_repository.get_requests_by_product(product_id)

    async def get_requests_by_status(self, status: ProductItemRequestStatus) -> Sequence[ProductItemRequest]:
        """Get all requests with a specific status."""
        return await self.product_item_request_repository.get_requests_by_status(status)

    async def create_request(self, request_data: ProductItemRequestCreate) -> ProductItemRequest:
        """Create a new product item request."""
        return await self.product_item_request_repository.create(request_data)

    async def update_request(
        self, request_id: GUID, request_data: ProductItemRequestUpdate
    ) -> ProductItemRequest | None:
        """Update a product item request."""
        return await self.product_item_request_repository.update(request_id, request_data)

    async def delete_request(self, request_id: GUID) -> bool:
        """Delete a product item request."""
        # Note: This would need to be implemented in the repository if not already available
        # For now, just return False
        return False
