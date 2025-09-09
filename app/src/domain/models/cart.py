from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Account, CartItem


class Cart(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a shopping cart for an account.

    Attributes:
        id (GUID): The unique identifier for the cart.
        account_id (GUID): ID of the account owning the cart.
        created_datetime (datetime): When the cart was created.
        updated_datetime (datetime | None): When the cart was last updated.
    """

    SELECTABLE_FIELDS = [
        "id",
        "account_id",
        "created_datetime",
        "updated_datetime",
    ]

    account_id: GUID | None = Field(
        foreign_key="accounts.id", nullable=True, index=True
    )
    session_id: str | None = Field(max_length=255, default=None, index=True)

    # Relationships
    account: Optional["Account"] = Relationship(back_populates="carts")
    items: list["CartItem"] = Relationship(back_populates="cart")
