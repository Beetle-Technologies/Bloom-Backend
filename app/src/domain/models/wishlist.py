from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import TEXT, Boolean, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo, WishlistItem


class Wishlist(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a wishlist for an account.

    Attributes:\n
        id (GUID): The unique identifier for the wishlist.
        account_id (GUID): ID of the account owning the wishlist.
        name (str | None): Optional name for the wishlist.
        created_datetime (datetime): When the wishlist was created.
        updated_datetime (datetime | None): When the wishlist was last updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "account_type_info_id",
        "name",
        "is_default",
        "created_datetime",
        "updated_datetime",
    ]

    account_type_info_id: GUID = Field(foreign_key="account_type_infos.id", nullable=False, index=True)
    name: str | None = Field(sa_column=Column(TEXT(), nullable=True))
    is_default: bool = Field(
        sa_column=Column(Boolean(), default=False, nullable=False),
    )

    # Relationships
    account_type_info: "AccountTypeInfo" = Relationship(back_populates="wishlists")
    items: list["WishlistItem"] = Relationship(back_populates="wishlist")
