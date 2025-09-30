from typing import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.cart_item import CartItem
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import CartItemCreate, CartItemUpdate

logger = get_logger(__name__)


class CartItemRepository(BaseRepository[CartItem, CartItemCreate, CartItemUpdate]):
    """
    Repository for managing cart items in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CartItem, session)

    async def get_items_by_cart(self, cart_id: GUID) -> Sequence[CartItem]:
        """Get all cart items for a specific cart."""
        try:
            query = select(CartItem).where(CartItem.cart_id == cart_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.cart_item_repository.get_items_by_cart:: error while getting items for cart {cart_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve cart items",
                detail="An error occurred while retrieving cart items for cart.",
                metadata={"cart_id": str(cart_id)},
            ) from e

    async def get_item_by_cart_and_cartable(
        self, cart_id: GUID, cartable_type: str, cartable_id: GUID
    ) -> CartItem | None:
        """Get cart item by cart, cartable type, and cartable ID."""
        try:
            return await self.find_one_by_and_none(
                cart_id=cart_id, cartable_type=cartable_type, cartable_id=cartable_id
            )
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.cart_item_repository.get_item_by_cart_and_cartable:: error while getting item for cart {cart_id}, {cartable_type}:{cartable_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve cart item",
                detail="An error occurred while retrieving cart item.",
                metadata={
                    "cart_id": str(cart_id),
                    "cartable_type": cartable_type,
                    "cartable_id": str(cartable_id),
                },
            ) from e
