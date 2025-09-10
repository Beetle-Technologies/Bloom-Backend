from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.dialects.postgresql import NUMERIC
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Order


class OrderItem(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an item in an order (product or resale product).

    Attributes:
        id (GUID): The unique identifier for the order item.
        order_id (GUID): ID of the order.
        orderable_type (str): Type of entity being ordered ('product' or 'resale_product').
        orderable_id (GUID): ID of the entity being ordered.
        quantity (int): Quantity ordered.
        price (Decimal): Price per unit at time of order.
        created_datetime (datetime): When the item was added.
        updated_datetime (datetime | None): When the item was last updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "order_id",
        "orderable_type",
        "orderable_id",
        "quantity",
        "price",
        "created_datetime",
        "updated_datetime",
    ]

    order_id: GUID = Field(foreign_key="orders.id", nullable=False, index=True)
    orderable_type: str = Field(max_length=50, nullable=False, index=True)
    orderable_id: GUID = Field(nullable=False, index=True)
    quantity: int = Field(nullable=False)
    price: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))

    # Relationships
    order: "Order" = Relationship(back_populates="items")
