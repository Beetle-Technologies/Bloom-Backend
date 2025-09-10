from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar, Optional

from sqlalchemy import VARCHAR, CheckConstraint
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import FriendlyMixin, GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import OrderStatus

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo, OrderInvoice, OrderItem


class Order(GUIDMixin, FriendlyMixin, TimestampMixin, table=True):
    """
    Represents an order placed by an account.

    Attributes:
        id (GUID): The unique identifier for the order.
        friendly_id (str): A human-readable identifier for the order.
        account_type_info_id (GUID | None): ID of the account type info placing the order.
        session_id (str | None): Session identifier for guest orders.
        status (OrderStatus): Current status of the order.
        total_amount (Decimal): Total amount of the order.
        created_datetime (datetime): When the order was created.
        updated_datetime (datetime | None): When the order was last updated.
    """

    __table_args__ = (
        CheckConstraint(
            "account_type_info_id IS NOT NULL OR session_id IS NOT NULL",
            name="chk_account_type_info_id_or_session_id_not_null",
        ),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "account_type_info_id",
        "status",
        "total_amount",
        "created_datetime",
        "updated_datetime",
    ]

    account_type_info_id: GUID | None = Field(
        foreign_key="account_type_infos.id", nullable=True, index=True, default=None
    )
    status: OrderStatus = Field(sa_column=Column(VARCHAR(150), nullable=False, default=OrderStatus.PENDING))

    session_id: str | None = Field(max_length=255, default=None, nullable=True, index=True)
    total_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))

    # Relationships
    account_type_info: Optional["AccountTypeInfo"] = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    invoices: list["OrderInvoice"] = Relationship(back_populates="order")
