from typing import TYPE_CHECKING, ClassVar, Optional

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship
from src.core.database.mixins import FriendlyMixin, GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo, CartItem


class Cart(GUIDMixin, FriendlyMixin, TimestampMixin, table=True):
    """
    Represents a shopping cart for an account.

    Attributes:
        id (GUID): The unique identifier for the cart.
        friendly_id (str): A human-readable identifier for the cart.
        account_type_info_id (GUID): ID of the account type info owning the cart.
        session_id (str | None): Session identifier for guest carts.
        created_datetime (datetime): When the cart was created.
        updated_datetime (datetime | None): When the cart was last updated.
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
        "session_id",
        "created_datetime",
        "updated_datetime",
    ]

    account_type_info_id: GUID | None = Field(
        foreign_key="account_type_infos.id", nullable=True, index=True, default=None
    )
    session_id: str | None = Field(max_length=255, default=None, nullable=True, index=True)

    # Relationships
    account_type_info: Optional["AccountTypeInfo"] = Relationship(back_populates="carts")
    items: list["CartItem"] = Relationship(back_populates="cart")
