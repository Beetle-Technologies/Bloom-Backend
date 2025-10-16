from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.decorators import transactional
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoriableType
from src.domain.models.cart import Cart
from src.domain.models.cart_item import CartItem
from src.domain.models.product import Product
from src.domain.models.product_item import ProductItem
from src.domain.repositories.cart_item_repository import CartItemRepository
from src.domain.repositories.cart_repository import CartRepository
from src.domain.schemas import AuthSessionState, CartCreate, CartItemCreate, CartItemUpdate
from src.domain.services.catalog_service import CatalogService
from src.domain.services.inventory_service import InventoryService
from src.libs.query_engine import BaseQueryEngineParams

logger = get_logger(__name__)


class CartService:
    """Service for managing carts."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cart_repository = CartRepository(session=self.session)
        self.cart_item_repository = CartItemRepository(session=self.session)
        self.inventory_service = InventoryService(session=self.session)
        self.catalog_service = CatalogService(session=self.session)

    async def get_cart_by_friendly_id(self, friendly_id: str, auth_state: AuthSessionState) -> Cart | None:
        """Get cart by friendly ID with items, cartables, and one attachment each."""
        try:
            cart = await self.cart_repository.query(
                params=BaseQueryEngineParams(
                    filters={
                        "friendly_id__eq": friendly_id,
                        "account_type_info_id__eq": str(auth_state.type_info_id),
                    }
                )
            )
            if not cart:
                return None

            items = await self.cart_item_repository.get_items_by_cart(cart.id)
            cart.items = list(items)

            for item in cart.items:
                cartable = await self._get_cartable(item.cartable_type, item.cartable_id)
                if cartable is not None:
                    item.name = cartable.name
                    item.quantity = item.quantity
                    item.currency = cartable.currency
                    item.price = cartable.price
                    item.attachment = await self._get_one_attachment(item.cartable_type, item.cartable_id)

            return cart
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.cart_service.get_cart_by_friendly_id:: Service error getting cart {friendly_id}: {se}"
            )
            raise se
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.cart_service.get_cart_by_friendly_id:: Error getting cart {friendly_id}: {e}"
            )
            raise errors.ServiceError("Failed to retrieve cart") from e

    async def _get_cartable(self, cartable_type: str, cartable_id: GUID) -> Product | ProductItem | None:
        if cartable_type == "Product":
            from src.domain.repositories.product_repository import ProductRepository

            product_repo = ProductRepository(session=self.session)
            return await product_repo.query(
                params=BaseQueryEngineParams(filters={"id__eq": str(cartable_id)}, include=["currency"])
            )
        elif cartable_type == "ProductItem":
            from src.domain.repositories.product_item_repository import ProductItemRepository

            product_item_repo = ProductItemRepository(session=self.session)
            return await product_item_repo.query(
                params=BaseQueryEngineParams(filters={"id__eq": str(cartable_id)}, include=["currency"])
            )
        return None

    async def _get_one_attachment(self, cartable_type: str, cartable_id: GUID) -> dict | None:
        attachments = await self.catalog_service._get_attachments_for_catalog_item(cartable_type, cartable_id)
        return attachments[0] if attachments else None

    async def create_cart_if_not_exists(self, auth_state: AuthSessionState) -> Cart:
        existing_cart = await self.cart_repository.get_cart_by_account_type_info(auth_state.type_info_id)
        if existing_cart:
            return existing_cart

        cart_data = CartCreate(account_type_info_id=auth_state.type_info_id)
        return await self.cart_repository.create(cart_data)

    @transactional
    async def add_to_cart(self, item_fid: str, quantity: int, auth_state: AuthSessionState) -> CartItem:
        try:
            cart = await self.create_cart_if_not_exists(auth_state)

            item, _ = await self.catalog_service.get_catalog_item(item_fid, auth_state)
            if not item:
                raise errors.NotFoundError("Cart item not found")

            cartable_type = "Product" if isinstance(item, Product) else "ProductItem"
            cartable_id = item.id

            inventoriable_type = (
                InventoriableType.PRODUCT if cartable_type == "Product" else InventoriableType.PRODUCT_ITEM
            )
            inventory = await self.inventory_service.get_inventory_by_item(inventoriable_type, cartable_id)
            if not inventory or inventory.available_stock < quantity:
                raise errors.ServiceError(f"Insufficient stock for item {item.name}", status=400)

            existing_item = await self.cart_item_repository.get_item_by_cart_and_cartable(
                cart.id, cartable_type, cartable_id
            )

            if existing_item:
                new_quantity = existing_item.quantity + quantity
                if inventory.available_stock < new_quantity:
                    raise errors.ServiceError("Insufficient stock for total quantity", status=400)

                update_data = CartItemUpdate(quantity=new_quantity)
                updated_item = await self.cart_item_repository.update(existing_item.id, update_data)

                if not updated_item:
                    raise errors.ServiceError("Failed to update cart item")

                return updated_item
            else:
                cart_item_data = CartItemCreate(
                    cart_id=cart.id,
                    cartable_type=cartable_type,
                    cartable_id=cartable_id,
                    quantity=quantity,
                )
                return await self.cart_item_repository.create(cart_item_data)
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.cart_service.add_to_cart:: Service error adding item {item_fid} to cart: {se}"
            )
            raise se
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.cart_service.add_to_cart:: Error adding item {item_fid} to cart: {e}"
            )
            raise errors.ServiceError("Failed to add item to cart") from e

    async def update_cart_item(
        self, cart_fid: str, item_fid: str, quantity: int, auth_state: AuthSessionState
    ) -> CartItem | None:
        try:
            cart = await self.cart_repository.query(
                params=BaseQueryEngineParams(
                    filters={
                        "friendly_id__eq": cart_fid,
                        "account_type_info_id__eq": str(auth_state.type_info_id),
                    }
                )
            )
            if not cart:
                raise errors.NotFoundError("Cart not found")

            item, _ = await self.catalog_service.get_catalog_item(item_fid, auth_state)
            cartable_type = "Product" if isinstance(item, Product) else "ProductItem"
            inventoriable_type = (
                InventoriableType.PRODUCT if cartable_type == "Product" else InventoriableType.PRODUCT_ITEM
            )
            inventory = await self.inventory_service.get_inventory_by_item(inventoriable_type, item.id)
            if not inventory or inventory.available_stock < quantity:
                raise errors.ServiceError("Insufficient stock", status=400)

            cart_item = await self.cart_item_repository.get_item_by_cart_and_cartable(cart.id, cartable_type, item.id)
            if not cart_item:
                raise errors.NotFoundError("Cart item not found")

            update_data = CartItemUpdate(quantity=quantity)
            return await self.cart_item_repository.update(cart_item.id, update_data)
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.cart_service.update_cart_item:: Service error updating item {item_fid} in cart {cart_fid}: {se}"
            )
            raise se
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.cart_service.update_cart_item:: Error updating item {item_fid} in cart {cart_fid}: {e}"
            )
            raise errors.ServiceError("Failed to update cart item") from e

    async def remove_from_cart(self, cart_fid: str, item_fid: str, auth_state: AuthSessionState) -> bool:
        try:
            cart = await self.cart_repository.query(
                params=BaseQueryEngineParams(
                    filters={
                        "friendly_id__eq": cart_fid,
                        "account_type_info_id__eq": str(auth_state.type_info_id),
                    }
                )
            )
            if not cart:
                raise errors.NotFoundError("Cart not found")

            item, _ = await self.catalog_service.get_catalog_item(item_fid, auth_state)
            cartable_type = "Product" if isinstance(item, Product) else "ProductItem"
            cart_item = await self.cart_item_repository.get_item_by_cart_and_cartable(cart.id, cartable_type, item.id)
            if not cart_item:
                raise errors.NotFoundError("Cart item not found")

            return await self.cart_item_repository.delete(cart_item.id)
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.cart_service.remove_from_cart:: Service error removing item {item_fid} from cart {cart_fid}: {se}"
            )
            raise se
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.cart_service.remove_from_cart:: Error removing item {item_fid} from cart {cart_fid}: {e}"
            )
            raise errors.ServiceError("Failed to remove item from cart") from e

    @transactional
    async def clear_cart(self, cart_fid: str, auth_state: AuthSessionState) -> bool:

        try:
            cart = await self.cart_repository.query(
                params=BaseQueryEngineParams(
                    filters={
                        "friendly_id__eq": cart_fid,
                        "account_type_info_id__eq": str(auth_state.type_info_id),
                    }
                )
            )
            if not cart:
                raise errors.NotFoundError("Cart not found")

            items = await self.cart_item_repository.get_items_by_cart(cart.id)
            for item in items:
                await self.cart_item_repository.delete(item.id)
            return True
        except errors.ServiceError as se:
            logger.error(f"src.domain.services.cart_service.clear_cart:: Service error clearing cart {cart_fid}: {se}")
            raise se
        except errors.DatabaseError as e:
            logger.exception(f"src.domain.services.cart_service.clear_cart:: Error clearing cart {cart_fid}: {e}")
            raise errors.ServiceError("Failed to clear cart") from e
