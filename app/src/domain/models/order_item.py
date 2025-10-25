from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.dialects.postgresql import NUMERIC
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import CreatedDateTimeMixin, GUIDMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Order


class OrderItem(GUIDMixin, CreatedDateTimeMixin, table=True):
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
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "order_id",
        "orderable_type",
        "orderable_id",
        "quantity",
        "unit_price",
        "subtotal",
        "tax_rate",
        "tax_amount",
        "discount_rate",
        "discount_amount",
        "total",
        "created_datetime",
    ]

    order_id: GUID = Field(foreign_key="orders.id", nullable=False, index=True)
    orderable_type: str = Field(max_length=50, nullable=False, index=True)
    orderable_id: GUID = Field(nullable=False, index=True)
    quantity: int = Field(nullable=False)
    unit_price: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))
    subtotal: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))
    tax_rate: Decimal = Field(sa_column=Column(NUMERIC(5, 2), nullable=False, default=Decimal("0.00")))
    tax_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00")))
    discount_rate: Decimal = Field(sa_column=Column(NUMERIC(5, 2), nullable=False, default=Decimal("0.00")))
    discount_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00")))
    total: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))

    # Relationships
    order: "Order" = Relationship(back_populates="items")

    def calculate_total(self):
        self.subtotal = self.unit_price * Decimal(str(self.quantity))

        self.discount_amount = self.subtotal * (self.discount_rate / Decimal("100"))

        amount_after_discount = self.subtotal - self.discount_amount

        self.tax_amount = amount_after_discount * (self.tax_rate / Decimal("100"))

        self.total = amount_after_discount + self.tax_amount
