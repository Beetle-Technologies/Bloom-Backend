from __future__ import annotations

import json
from decimal import Decimal

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.decorators import transactional
from src.core.dependencies import get_storage_service
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoriableType, InventoryActionType, ProductStatus
from src.domain.models.product import Product
from src.domain.models.product_item import ProductItem
from src.domain.repositories.attachment_repository import AttachmentBlobRepository, AttachmentRepository
from src.domain.repositories.product_item_repository import ProductItemRepository
from src.domain.repositories.product_repository import ProductRepository
from src.domain.schemas import (
    DEFAULT_CATALOG_RETURN_FIELDS,
    AuthSessionState,
    CatalogItemCreateRequest,
    InventoryActionCreate,
    InventoryCreate,
    ProductCreate,
)
from src.domain.services.attachment_service import AttachmentService
from src.domain.services.inventory_action_service import InventoryActionService
from src.domain.services.inventory_service import InventoryService
from src.domain.services.product_service import ProductService
from src.libs.query_engine import BaseQueryEngineParams, GeneralPaginationRequest, GeneralPaginationResponse
from src.libs.storage import StorageService

logger = get_logger(__name__)


class CatalogService:
    """Service for catalog browsing based on auth state."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repository = ProductRepository(session=self.session)
        self.product_item_repository = ProductItemRepository(session=self.session)

    async def get_catalog_item(
        self, item_fid: str, auth_state: AuthSessionState | None
    ) -> tuple[Product | ProductItem, list[dict[str, str]]]:
        """
        Get a catalog item by friendly ID, including its attachments.

        Returns the item (Product or ProductItem) and a list of attachment info.
        """
        try:
            if auth_state and auth_state.type.is_supplier():
                item = await self.product_repository.query(
                    params=BaseQueryEngineParams(
                        filters={
                            "friendly_id__eq": item_fid,
                            "supplier_account_id__eq": str(auth_state.id),
                            "status__eq": ProductStatus.ACTIVE,
                        },
                        fields=",".join(DEFAULT_CATALOG_RETURN_FIELDS),
                        include=["currency", "category"],
                    )
                )
                attachable_type = "Product"
            else:
                filters = {"friendly_id__eq": item_fid, "status__eq": ProductStatus.ACTIVE}

                item = await self.product_item_repository.query(
                    params=BaseQueryEngineParams(
                        filters=filters,
                        fields=",".join(DEFAULT_CATALOG_RETURN_FIELDS),
                        include=["currency", "category"],
                    )
                )
                attachable_type = "ProductItem"

            if not item:
                raise errors.NotFoundError(detail="Item not found")

            attachments = await self._get_attachments_for_attachable(attachable_type, item.id)

            return item, attachments
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(f"Error getting catalog item {item_fid}: {e}")
            raise errors.ServiceError(
                detail="Failed to retrieve catalog item",
                status=500,
            ) from e

    async def _get_attachments_for_attachable(self, attachable_type: str, attachable_id: GUID) -> list[dict[str, str]]:
        """
        Get simplified attachment info for an attachable entity.
        """

        try:
            attachment_repo = AttachmentRepository(self.session)
            attachments = await attachment_repo.find_by_attachable(attachable_type, attachable_id)

            result = []
            storage_service = get_storage_service()

            for att in attachments:
                blob_repo = AttachmentBlobRepository(self.session)
                blob = await blob_repo.find_one_by(id=att.blob_id)
                if blob:
                    assert att.friendly_id is not None, "Attachment friendly_id should not be None"

                    attachment_service = AttachmentService(self.session)
                    download_response = await attachment_service.get_attachment_download_url(
                        attachment_fid=att.friendly_id,
                        storage_service=storage_service,
                    )
                    result.append(
                        {
                            "id": str(att.id),
                            "friendly_id": att.friendly_id,
                            "name": att.name,
                            "url": download_response.download_url,
                        }
                    )

            return result
        except Exception as e:
            logger.exception(f"Error getting attachments for {attachable_type}:{attachable_id}: {e}")
            return []

    async def browse_catalog(
        self,
        auth_state: AuthSessionState | None,
        pagination: GeneralPaginationRequest,
    ) -> GeneralPaginationResponse[Product] | GeneralPaginationResponse[ProductItem]:
        """
        Browse the catalog based on auth state, including attachments for each item.
        """
        try:
            result = await self._browse_catalog_internal(auth_state, pagination)

            for item in result.items:
                attachable_type = "Product" if isinstance(item, Product) else "ProductItem"
                item.attachments = await self._get_attachments_for_attachable(attachable_type, item.id)

            return result
        except errors.ServiceError as se:
            logger.exception(f"src.domain.services.catalog_service.browse_catalog:: error while browsing catalog: {se}")
            raise se
        except errors.DatabaseError as e:
            logger.exception(f"src.domain.services.catalog_service.browse_catalog:: error while browsing catalog: {e}")
            raise errors.ServiceError(
                detail="Failed to browse catalog",
                status=500,
            ) from e

    async def _browse_catalog_internal(
        self,
        auth_state: AuthSessionState | None,
        pagination: GeneralPaginationRequest,
    ) -> GeneralPaginationResponse[Product] | GeneralPaginationResponse[ProductItem]:
        """
        Internal browse method without attachments.
        """

        if auth_state is None or auth_state.type.is_user():
            return await self.product_item_repository.find(pagination=pagination)
        elif auth_state.type.is_supplier():
            pagination.filters = pagination.filters or {}
            pagination.filters["supplier_account_id__eq"] = str(auth_state.id)
            return await self.product_repository.find(pagination=pagination)
        elif auth_state.type.is_business():
            pagination.filters = pagination.filters or {}
            pagination.filters["seller_account_id__eq"] = str(auth_state.id)
            return await self.product_item_repository.find(pagination=pagination)
        else:
            return await self.product_item_repository.find(pagination=pagination)

    @transactional
    async def create_catalog_item(
        self,
        form_data: CatalogItemCreateRequest,
        auth_state: AuthSessionState,
        storage_service: StorageService,
    ) -> Product:
        """
        Create a new catalog item (product) with inventory, inventory action, and attachments.
        """

        try:
            product_attributes = {}
            if form_data.attributes:
                product_attributes = json.loads(form_data.attributes)

            product_data = ProductCreate(
                name=form_data.name,
                description=form_data.description,
                price=Decimal(form_data.price),
                supplier_account_id=auth_state.id,
                currency_id=form_data.currency_id,
                category_id=form_data.category_id,
                is_digital=form_data.is_digital,
                attributes=product_attributes,
            )

            product_service = ProductService(self.session)
            inventory_service = InventoryService(self.session)
            inventory_action_service = InventoryActionService(self.session)
            attachment_service = AttachmentService(self.session)

            product = await product_service.create_product(product_data)

            inventory_data = InventoryCreate(
                inventoriable_type=InventoriableType.PRODUCT,
                inventoriable_id=product.id,
                quantity_in_stock=form_data.initial_stock,
                reserved_stock=0,
            )
            inventory = await inventory_service.create_inventory(inventory_data)

            if form_data.initial_stock > 0:
                action_data = InventoryActionCreate(
                    inventory_id=inventory.id,
                    action_type=InventoryActionType.STOCK_IN,
                    quantity=form_data.initial_stock,
                    reason="Initial stock for new product",
                )
                await inventory_action_service.create_action(action_data)

            if form_data.attachments and form_data.attachment_names:
                if len(form_data.attachments) != len(form_data.attachment_names):
                    raise errors.ServiceError(
                        detail="Number of attachments must match number of names",
                        status=400,
                    )

                for file, attachment_name in zip(form_data.attachments, form_data.attachment_names):
                    await attachment_service.upload_attachment(
                        file=file,
                        name=attachment_name,
                        attachable_type="Product",
                        attachable_id=product.id,
                        uploaded_by=auth_state.id,
                        storage_service=storage_service,
                    )

            return product
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.catalog_service.create_catalog_item:: Error in create_catalog_item: {se.detail}"
            )
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.create_catalog_item:: Unexpected error in create_catalog_item: {e}"
            )
            raise errors.ServiceError(
                detail="Failed to create catalog item",
                status=500,
            ) from e
