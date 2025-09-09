from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, UniqueConstraint
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Wishlist


class WishlistItem(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an item in a wishlist (product or resale product).

    Attributes:\n
        id (GUID): The unique identifier for the wishlist item.
        wishlist_id (GUID): ID of the wishlist.
        wishable_type (str): Type of entity in the wishlist ('product' or 'resale_product').
        wishable_id (GUID): ID of the entity in the wishlist.
        created_datetime (datetime): When the item was added.
        updated_datetime (datetime | None): When the item was last updated.
    """

    __table_args__ = (
        UniqueConstraint(
            "wishlist_id",
            "wishable_id",
            "wishable_type",
            name="uq_wishlist_item_wishlist_type",
        ),
        CheckConstraint(
            "priority >= 1 AND priority <= 5", name="chk_wishlist_item_priority_range"
        ),
    )

    SELECTABLE_FIELDS = [
        "id",
        "wishlist_id",
        "wishable_type",
        "wishable_id",
        "priority",
        "created_datetime",
        "updated_datetime",
    ]

    wishlist_id: GUID = Field(foreign_key="wishlists.id", nullable=False, index=True)
    wishable_type: str = Field(max_length=50, nullable=False, index=True)
    wishable_id: GUID = Field(nullable=False, index=True)
    priority: int = Field(default=1, nullable=False)

    # Relationships
    wishlist: "Wishlist" = Relationship(back_populates="items")
