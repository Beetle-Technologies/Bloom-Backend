from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import NUMERIC
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Order


class OrderInvoice(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an invoice for an order (can be polymorphic if needed for items).

    Attributes:
        id (GUID): The unique identifier for the invoice.
        order_id (GUID): ID of the order.
        invoiceable_type (str | None): Optional type ('product' or 'resale_product' for item-level).
        invoiceable_id (GUID | None): Optional ID for item-level invoicing.
        amount (Decimal): Invoice amount.
        created_datetime (datetime): When the invoice was created.
        updated_datetime (datetime | None): When the invoice was last updated.
    """

    __tablename__ = "order_invoices"  # type: ignore

    SELECTABLE_FIELDS = [
        "id",
        "order_id",
        "invoiceable_type",
        "invoiceable_id",
        "amount",
        "created_datetime",
        "updated_datetime",
    ]

    order_id: GUID = Field(foreign_key="orders.id", nullable=False, index=True)
    invoiceable_type: str | None = Field(max_length=120, nullable=True, index=True)
    invoiceable_id: GUID | None = Field(nullable=True, index=True)
    amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))

    order: "Order" = Relationship(back_populates="invoices")
