from typing import TYPE_CHECKING, Optional

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import FriendlyMixin, GUIDMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Product


class Category(GUIDMixin, FriendlyMixin, table=True):
    """
    Represents a category in the system.

    Attributes:
        id (GUID): The unique identifier for the category.
        friendly_id (str): A URL-friendly identifier for the category.
        title (str): The title of the category.
        description (str | None): Description of the category.
        parent_id (GUID | None): Reference to parent category for hierarchical structure.
        is_active (bool): Whether the category is active.
        sort_order (int): Sort order for display.
    """

    __tablename__ = "category"  # type: ignore

    ENABLE_FRIENDLY_SLUG = True

    SELECTABLE_FIELDS = [
        "id",
        "friendly_id",
        "title",
        "description",
        "parent_id",
        "is_active",
        "sort_order",
    ]

    title: str = Field(max_length=255, nullable=False, index=True)
    description: str | None = Field(
        sa_column=Column(TEXT(), nullable=True, default=None)
    )
    parent_id: GUID | None = Field(default=None, foreign_key="category.id")
    is_active: bool = Field(default=True, nullable=False)
    sort_order: int = Field(default=0, nullable=False)

    # Relationships
    parent: Optional["Category"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: list["Category"] = Relationship(back_populates="parent")
    products: list["Product"] = Relationship(back_populates="category")
