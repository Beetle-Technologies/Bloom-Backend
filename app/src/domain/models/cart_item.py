from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Cart


class CartItem(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an item in a cart (product or resale product).

    Attributes:
        id (GUID): The unique identifier for the cart item.
        cart_id (GUID): ID of the cart.
        cartable_type (str): Type of entity in the cart ('product' or 'resale_product').
        cartable_id (GUID): ID of the entity in the cart.
        quantity (int): Quantity in the cart.
        created_datetime (datetime): When the item was added.
        updated_datetime (datetime | None): When the item was last updated.
    """

    SELECTABLE_FIELDS = [
        "id",
        "cart_id",
        "cartable_type",
        "cartable_id",
        "quantity",
        "created_datetime",
        "updated_datetime",
    ]

    cart_id: GUID = Field(foreign_key="carts.id", nullable=False, index=True)
    cartable_type: str = Field(max_length=50, nullable=False, index=True)
    cartable_id: GUID = Field(nullable=False, index=True)
    quantity: int = Field(nullable=False)

    # Relationships
    cart: "Cart" = Relationship(back_populates="items")
