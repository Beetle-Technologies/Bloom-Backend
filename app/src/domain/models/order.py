from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import VARCHAR
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import OrderStatus

if TYPE_CHECKING:
    from src.domain.models import Account, OrderInvoice, OrderItem


class Order(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an order placed by an account.

    Attributes:
        id (GUID): The unique identifier for the order.
        account_id (GUID): ID of the account placing the order.
        status (OrderStatus): Current status of the order.
        total_amount (Decimal): Total amount of the order.
        created_datetime (datetime): When the order was created.
        updated_datetime (datetime | None): When the order was last updated.
    """

    SELECTABLE_FIELDS = [
        "id",
        "account_id",
        "status",
        "total_amount",
        "created_datetime",
        "updated_datetime",
    ]

    account_id: GUID = Field(foreign_key="accounts.id", nullable=False, index=True)
    status: OrderStatus = Field(
        sa_column=Column(VARCHAR(150), nullable=False, default=OrderStatus.PENDING)
    )
    total_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))

    # Relationships
    account: "Account" = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    invoices: list["OrderInvoice"] = Relationship(back_populates="order")
