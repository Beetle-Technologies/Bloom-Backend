from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo


class Review(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a review for a product or resale product.

    Attributes:
        id (GUID): The unique identifier for the review.
        reviewable_type (str): Type of entity being reviewed ('product' or 'resale_product').
        reviewable_id (GUID): ID of the entity being reviewed.
        account_id (GUID): ID of the account leaving the review.
        rating (int): Rating from 1-5.
        comment (str | None): Optional review comment.
        created_datetime (datetime): When the review was created.
        updated_datetime (datetime | None): When the review was last updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "reviewable_type",
        "reviewable_id",
        "account_type_info_id",
        "rating",
        "comment",
        "created_datetime",
        "updated_datetime",
    ]

    reviewable_type: str = Field(max_length=50, nullable=False, index=True)
    reviewable_id: GUID = Field(nullable=False, index=True)
    account_type_info_id: GUID = Field(foreign_key="account_type_infos.id", nullable=False, index=True)
    rating: int = Field(ge=1, le=5, nullable=False)
    comment: str | None = Field(sa_column=Column(TEXT(), nullable=True))

    # Relationships
    account_type_info: "AccountTypeInfo" = Relationship(back_populates="reviews")
