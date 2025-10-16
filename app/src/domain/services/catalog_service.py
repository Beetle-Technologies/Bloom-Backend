from __future__ import annotations

from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.decorators import transactional
from src.core.dependencies import get_storage_service
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoriableType, InventoryActionType, ProductItemRequestStatus, ProductStatus
from src.domain.models.inventory import Inventory
from src.domain.models.inventory_action import InventoryAction
from src.domain.models.product import Product
from src.domain.models.product_item import ProductItem
from src.domain.repositories.attachment_repository import AttachmentBlobRepository, AttachmentRepository
from src.domain.repositories.inventory_action_repository import InventoryActionRepository
from src.domain.repositories.product_item_repository import ProductItemRepository
from src.domain.repositories.product_repository import ProductRepository
from src.domain.schemas import (
    AdjustInventoryRequest,
    AuthSessionState,
    CatalogItemCreateRequest,
    CatalogItemUpdateRequest,
    InventoryActionCreate,
    InventoryCreate,
    ProductCreate,
    ProductItemCreate,
    ProductItemRequestCreate,
    RequestItemRequest,
)
from src.domain.services.attachment_service import AttachmentService
from src.domain.services.inventory_action_service import InventoryActionService
from src.domain.services.inventory_service import InventoryService
from src.domain.services.product_item_request_service import ProductItemRequestService
from src.domain.services.product_item_service import ProductItemService
from src.domain.services.product_service import ProductService
from src.libs.query_engine import BaseQueryEngineParams, GeneralPaginationRequest, GeneralPaginationResponse

logger = get_logger(__name__)


class CatalogService:
    """Service for catalog browsing based on auth state."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repository = ProductRepository(session=self.session)
        self.product_item_repository = ProductItemRepository(session=self.session)

    async def _get_inventory_for_item(
        self, inventoriable_type: InventoriableType, inventoriable_id: GUID
    ) -> Inventory | None:
        """
        Get inventory for an inventoriable item.
        """
        try:
            inventory_service = InventoryService(self.session)
            return await inventory_service.get_inventory_by_item(inventoriable_type, inventoriable_id)
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.catalog_service._get_inventory_for_item:: Service error getting inventory for {inventoriable_type}:{inventoriable_id}: {se.detail}"
            )
            return None
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service._get_inventory_for_item:: Error getting inventory for {inventoriable_type}:{inventoriable_id}: {e}"
            )
            return None

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

            enriched_items = []
            for item in result.items:
                if hasattr(item, "model_dump"):
                    item_dict = item.model_dump()
                    attachable_type = "Product" if auth_state and auth_state.type.is_supplier() else "ProductItem"
                elif hasattr(item, "_mapping"):
                    item_dict = dict(item._mapping)  # type: ignore
                    attachable_type = "Product" if auth_state and auth_state.type.is_supplier() else "ProductItem"
                else:
                    try:
                        item_dict = {key: getattr(item, key) for key in item.__table__.columns.keys()}  # type: ignore
                        attachable_type = "Product" if isinstance(item, Product) else "ProductItem"
                    except Exception:
                        continue

                item_id = item_dict.get("id")
                if not item_id:
                    continue

                attachments = await self._get_attachments_for_attachable(attachable_type, item_id)

                inventoriable_type = (
                    InventoriableType.PRODUCT if attachable_type == "Product" else InventoriableType.PRODUCT_ITEM
                )
                inventory = await self._get_inventory_for_item(inventoriable_type, item_id)

                item_dict["attachments"] = attachments
                item_dict["inventory"] = (
                    {"quantity_in_stock": inventory.quantity_in_stock, "reserved_stock": inventory.reserved_stock}
                    if inventory
                    else None
                )

                if item_dict["inventory"] is not None:
                    item_dict["inventory"]["available_stock"] = (
                        item_dict["inventory"]["quantity_in_stock"] - item_dict["inventory"]["reserved_stock"]
                    )

                enriched_items.append(item_dict)

            return GeneralPaginationResponse(
                items=enriched_items,
                total_count=result.total_count,
                has_next=result.has_next,
                has_previous=result.has_previous,
                next_cursor=result.next_cursor,
                previous_cursor=result.previous_cursor,
                page=result.page,
                limit=result.limit,
                total_pages=result.total_pages,
                pagination_type=result.pagination_type,
            )
        except errors.ServiceError as se:
            logger.exception(f"src.domain.services.catalog_service.browse_catalog:: error while browsing catalog: {se}")
            raise se
        except errors.DatabaseError as e:
            logger.exception(f"src.domain.services.catalog_service.browse_catalog:: error while browsing catalog: {e}")
            raise errors.ServiceError(
                detail="Failed to browse catalog",
            ) from e

    async def _browse_catalog_internal(
        self,
        auth_state: AuthSessionState | None,
        pagination: GeneralPaginationRequest,
    ) -> GeneralPaginationResponse[Product] | GeneralPaginationResponse[ProductItem]:
        """
        Internal browse method without attachments.
        """
        print("pagination", pagination.model_dump())

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
        item_data: CatalogItemCreateRequest,
        auth_state: AuthSessionState,
    ) -> Product:
        """
        Create a new catalog item (product) with inventory, inventory action, and attachments.
        """

        try:
            product_data = ProductCreate(
                id=item_data.id,
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                supplier_account_id=auth_state.id,
                currency_id=item_data.currency_id,
                category_id=item_data.category_id,
                is_digital=item_data.is_digital,
                attributes=item_data.attributes,
            )

            product_service = ProductService(self.session)
            inventory_service = InventoryService(self.session)
            inventory_action_service = InventoryActionService(self.session)

            product = await product_service.create_product(product_data)

            inventory_data = InventoryCreate(
                inventoriable_type=InventoriableType.PRODUCT,
                inventoriable_id=product.id,
                quantity_in_stock=item_data.initial_stock,
                reserved_stock=0,
            )
            inventory = await inventory_service.create_inventory(inventory_data)

            if item_data.initial_stock > 0:
                action_data = InventoryActionCreate(
                    inventory_id=inventory.id,
                    action_type=InventoryActionType.STOCK_IN,
                    quantity=item_data.initial_stock,
                    reason="Initial stock for new product",
                )
                await inventory_action_service.create_action(action_data)

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
            ) from e

    async def get_catalog_item(
        self, item_fid: str, auth_state: AuthSessionState | None
    ) -> tuple[dict[str, Any], list[dict[str, str]]]:
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
                        # fields=",".join(DEFAULT_CATALOG_RETURN_FIELDS),
                        include=["currency", "category"],
                    )
                )
                attachable_type = "Product"
            else:
                filters = {
                    "friendly_id__eq": item_fid,
                    "status__eq": ProductStatus.ACTIVE,
                }

                item = await self.product_item_repository.query(
                    params=BaseQueryEngineParams(
                        filters=filters,
                        # fields=",".join(DEFAULT_CATALOG_RETURN_FIELDS),
                        include=["currency", "category"],
                    )
                )
                attachable_type = "ProductItem"

            if not item:
                raise errors.NotFoundError(detail="Item not found")

            if hasattr(item, "model_dump"):
                item_dict = item.model_dump()
            elif hasattr(item, "_mapping"):
                item_dict = dict(item._mapping)  # type: ignore
            else:
                try:
                    item_dict = {key: getattr(item, key) for key in item.__table__.columns.keys()}  # type: ignore
                except Exception:
                    raise errors.ServiceError("Failed to convert item to dictionary")

            item_id = item_dict.get("id")
            if not item_id:
                raise errors.ServiceError("Item not found")

            attachments = await self._get_attachments_for_attachable(attachable_type, item_id)

            inventoriable_type = (
                InventoriableType.PRODUCT if attachable_type == "Product" else InventoriableType.PRODUCT_ITEM
            )
            inventory = await self._get_inventory_for_item(inventoriable_type, item_id)

            item_dict["inventory"] = (
                {"quantity_in_stock": inventory.quantity_in_stock, "reserved_stock": inventory.reserved_stock}
                if inventory
                else None
            )

            if item_dict["inventory"] is not None:
                item_dict["inventory"]["available_stock"] = (
                    item_dict["inventory"]["quantity_in_stock"] - item_dict["inventory"]["reserved_stock"]
                )

            return item_dict, attachments
        except errors.ServiceError as se:
            raise se
        except errors.NotFoundError as nfe:
            raise nfe
        except Exception as e:
            logger.exception(f"Error getting catalog item {item_fid}: {e}")
            raise errors.ServiceError(
                detail="Failed to retrieve catalog item",
            ) from e

    async def _get_attachments_for_attachable(self, attachable_type: str, attachable_id: GUID) -> list[dict[str, str]]:
        """
        Get simplified attachment info for an attachable entity.
        """

        try:
            attachment_repo = AttachmentRepository(self.session)

            attachments = await attachment_repo.query_all(
                params=BaseQueryEngineParams(
                    filters={
                        "attachable_type__eq": attachable_type,
                        "attachable_id__eq": str(attachable_id),
                    },
                    fields="id,friendly_id,name,blob_id",
                )
            )

            result = []
            storage_service = get_storage_service()

            for att in attachments:
                blob_repo = AttachmentBlobRepository(self.session)
                blob = await blob_repo.find_one_by(id=att.blob_id)
                if blob:
                    assert att.friendly_id is not None, "Attachment friendly_id should not be None"

                    attachment_service = AttachmentService(self.session)
                    attachment_url = await attachment_service.get_attachment_url(
                        attachment_fid=att.friendly_id,
                        storage_service=storage_service,
                    )
                    result.append(
                        {
                            "friendly_id": att.friendly_id,
                            "name": att.name,
                            "url": attachment_url,
                        }
                    )

            print("Attachment result:", result)

            return result
        except Exception as e:
            logger.exception(f"Error getting attachments for {attachable_type}:{attachable_id}: {e}")
            return []

    async def update_catalog_item(
        self,
        item_fid: str,
        update_data: CatalogItemUpdateRequest,
        auth_state: AuthSessionState,
    ) -> Product | ProductItem:
        """
        Update a catalog item by friendly ID based on auth state.
        """
        try:
            if auth_state.type.is_supplier():
                product = await self.product_repository.get_by_friendly_id(item_fid)
                if not product or product.supplier_account_id != auth_state.id:
                    raise errors.NotFoundError("Product not found or access denied")

                update_dict = update_data.model_dump(exclude_unset=True)
                updated_product = await self.product_repository.update(product.id, update_dict)

                if not updated_product:
                    raise errors.ServiceError("Failed to update product")
                return updated_product
            elif auth_state.type.is_business():
                product_item = await self.product_item_repository.get_by_friendly_id(item_fid)
                if not product_item:
                    raise errors.NotFoundError("Item not found")

                if product_item.seller_account_id != auth_state.id:
                    raise errors.InvalidPermissionError(detail="You do not have permission to update this item")

                update_dict = update_data.model_dump(exclude_unset=True)
                updated_item = await self.product_item_repository.update(product_item.id, update_dict)

                if not updated_item:
                    raise errors.ServiceError("Failed to update product item")
                return updated_item
            else:
                raise errors.ServiceError("Unauthorized to update items")
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.update_catalog_item:: Error updating catalog item {item_fid}: {e}"
            )
            raise errors.ServiceError("Failed to update catalog item")

    async def delete_catalog_item(self, item_fid: str, auth_state: AuthSessionState) -> bool:
        """
        Delete a catalog item by friendly ID based on auth state.
        """

        try:
            if auth_state.type.is_supplier():
                product = await self.product_repository.get_by_friendly_id(item_fid)

                if not product or product.supplier_account_id != auth_state.id:
                    raise errors.NotFoundError("Product not found or access denied")
                return await self.product_repository.delete(product.id)
            elif auth_state.type.is_business():
                product_item = await self.product_item_repository.get_by_friendly_id(item_fid)
                if not product_item or product_item.seller_account_id != auth_state.id:
                    raise errors.NotFoundError("Product item not found or access denied")
                return await self.product_item_repository.delete(product_item.id)
            else:
                raise errors.ServiceError("Unauthorized to delete items")
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.delete_catalog_item:: Error deleting catalog item {item_fid}: {e}"
            )
            raise errors.ServiceError("Failed to delete catalog item")

    @transactional
    async def request_catalog_item(
        self,
        item_fid: str,
        request_data: RequestItemRequest,
        auth_state: AuthSessionState,
    ) -> ProductItem:
        """
        Request a catalog item (create ProductItem with reserved stock).
        """
        try:
            product = await self.product_repository.get_by_friendly_id(item_fid)
            if not product:
                raise errors.NotFoundError("Product not found")

            inventory_service = InventoryService(self.session)
            inventory = await inventory_service.get_inventory_by_item(InventoriableType.PRODUCT, product.id)
            if not inventory:
                raise errors.NotFoundError("Product inventory not found")

            available_stock = inventory.available_stock
            if available_stock <= 0:
                raise errors.ServiceError("No available stock for this product")

            allocated_stock = min(available_stock, request_data.requested_quantity or 1)

            await inventory_service.reserve_stock(InventoriableType.PRODUCT, product.id, allocated_stock)

            product_item_data = ProductItemCreate(
                product_id=product.id,
                name=request_data.name or product.name,
                description=request_data.description or product.description,
                seller_account_id=auth_state.id,
                markup_percentage=request_data.markup_percentage,
                price=None,
                currency_id=None,
                category_id=None,
                status=None,
                is_digital=None,
                attributes=request_data.attributes,
            )
            product_item_service = ProductItemService(self.session)
            product_item = await product_item_service.create_product_item(product_item_data)

            inventory_data = InventoryCreate(
                inventoriable_type=InventoriableType.PRODUCT_ITEM,
                inventoriable_id=product_item.id,
                quantity_in_stock=allocated_stock,
                reserved_stock=0,
            )
            inventory = await inventory_service.create_inventory(inventory_data)

            request_create_data = ProductItemRequestCreate(
                seller_account_id=auth_state.id,
                supplier_account_id=product.supplier_account_id,
                product_id=product.id,
                requested_quantity=allocated_stock,
                status=ProductItemRequestStatus.APPROVED,
                mode=request_data.mode,
            )
            product_item_request_service = ProductItemRequestService(self.session)
            await product_item_request_service.create_request(request_create_data)

            return product_item
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.request_catalog_item:: Error requesting catalog item {item_fid}: {e}"
            )
            raise errors.ServiceError("Failed to request catalog item")

    async def get_catalog_item_inventory(self, item_fid: str, auth_state: AuthSessionState) -> Inventory:
        """
        Get inventory for a catalog item.
        """
        try:
            if auth_state.type.is_supplier():
                product = await self.product_repository.get_by_friendly_id(item_fid)
                if not product or product.supplier_account_id != auth_state.id:
                    raise errors.NotFoundError("Product not found or access denied")
                inventoriable_type = InventoriableType.PRODUCT
                inventoriable_id = product.id
            else:
                raise errors.ServiceError("Unauthorized")

            inventory_service = InventoryService(self.session)
            inventory = await inventory_service.get_inventory_by_item(inventoriable_type, inventoriable_id)
            if not inventory:
                raise errors.NotFoundError("Inventory not found")
            return inventory
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.get_catalog_item_inventory:: Error getting inventory for {item_fid}: {e}"
            )
            raise errors.ServiceError("Failed to get inventory")

    async def get_catalog_item_inventory_history(
        self,
        item_fid: str,
        auth_state: AuthSessionState,
        pagination: GeneralPaginationRequest,
    ) -> GeneralPaginationResponse[InventoryAction]:
        """
        Get paginated inventory history for a catalog item.
        """
        try:
            inventory = await self.get_catalog_item_inventory(item_fid, auth_state)

            pagination.filters = {"inventory_id__eq": str(inventory.id)}

            action_repo = InventoryActionRepository(self.session)
            return await action_repo.find(pagination=pagination)
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.get_catalog_item_inventory_history:: Error getting inventory history for {item_fid}: {e}"
            )
            raise errors.ServiceError("Failed to get inventory history")

    @transactional
    async def adjust_catalog_item_inventory(
        self,
        item_fid: str,
        adjust_data: AdjustInventoryRequest,
        auth_state: AuthSessionState,
    ) -> Inventory:
        """
        Adjust inventory for a catalog item.
        """
        try:
            if auth_state.type.is_supplier():
                product = await self.product_repository.get_by_friendly_id(item_fid)
                if not product or product.supplier_account_id != auth_state.id:
                    raise errors.NotFoundError("Product not found or access denied")
                inventoriable_type = InventoriableType.PRODUCT
                inventoriable_id = product.id
            else:
                raise errors.ServiceError("Unauthorized")

            inventory_service = InventoryService(self.session)
            action_type = (
                InventoryActionType.STOCK_IN if adjust_data.quantity_change > 0 else InventoryActionType.STOCK_OUT
            )
            inventory = await inventory_service.adjust_stock(
                inventoriable_type,
                inventoriable_id,
                adjust_data.quantity_change,
                action_type,
                adjust_data.reason,
            )
            return inventory  # type: ignore
        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(
                f"src.domain.services.catalog_service.adjust_catalog_item_inventory:: Error adjusting inventory for {item_fid}: {e}"
            )
            raise errors.ServiceError("Failed to adjust inventory")
