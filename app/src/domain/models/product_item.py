from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional
from uuid import UUID

from sqlalchemy import TEXT, Boolean, CheckConstraint, Column, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC
from sqlmodel import Field, Relationship
from src.core.database.mixins import DeletableMixin, FriendlyMixin, GUIDMixin, SearchableMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import ProductStatus

if TYPE_CHECKING:
    from src.domain.models import Account, Category, Currency, Product


class ProductItem(
    GUIDMixin,
    FriendlyMixin,
    DeletableMixin,
    SearchableMixin,
    TimestampMixin,
    table=True,
):
    """
    Represents a customized version of a product for sale.
    This model mirrors the Product model with nullable fields that are populated by triggers.

    Attributes:
        id (GUID): The unique identifier for the product item.
        friendly_id (str | None): A URL-friendly identifier for the product item.
        product_id (GUID): Reference to the original product being resold.
        seller_account_id (GUID): Reference to the reseller account.
        name (str | None): Item name (copied from product if null, overrideable).
        description (str | None): Item description (copied from product if null, overrideable).
        price (Decimal | None): Item price (calculated from product price + markup if null).
        markup_percentage (Decimal): Markup percentage applied to original product price.
        currency_id (UUID | None): Currency ID (copied from product if null, overrideable).
        category_id (GUID | None): Category ID (copied from product if null, overrideable).
        status (ProductStatus | None): Item status (copied from product if null, overrideable).
        search_vector (str | None): Full-text search vector for the product item.
        search_text (str | None): Full-text search text for the product item.
        is_digital (bool | None): Whether item is digital (copied from product if null, overrideable).
        attributes (Dict[str, Any] | None): Custom attributes (merged with product attributes if null).
        created_datetime (datetime): The timestamp when the product item was created.
        updated_datetime (datetime | None): The timestamp when the product item was last updated.
        deleted_datetime (datetime | None): The timestamp when the product item was deleted.
    """

    __table_args__ = (
        Index("idx_product_item_search_vector", "search_vector", postgresql_using="gin"),
        Index("idx_product_item_attributes", "attributes", postgresql_using="gin"),
        CheckConstraint(
            "markup_percentage >= 0",
            name="chk_product_item_markup_percentage_non_negative",
        ),
        UniqueConstraint("product_id", "seller_account_id", name="uq_product_item_seller"),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "friendly_id",
        "product_id",
        "seller_account_id",
        "name",
        "description",
        "price",
        "markup_percentage",
        "currency_id",
        "category_id",
        "status",
        "is_digital",
        "search_vector",
        "search_text",
        "attributes",
        "created_datetime",
        "updated_datetime",
        "deleted_datetime",
    ]

    # Core references
    product_id: GUID = Field(foreign_key="products.id", nullable=False, index=True)
    seller_account_id: GUID = Field(foreign_key="accounts.id", nullable=False, index=True)
    markup_percentage: Decimal = Field(
        sa_column=Column(NUMERIC(6, 2), nullable=False, default=0),
        description="Markup percentage applied to original product price",
    )

    # Nullable fields that mirror Product model (populated by triggers if null)
    name: str | None = Field(
        sa_column=Column(TEXT(), nullable=True, index=True),
        description="Item name (copied from product if null, overrideable)",
    )
    description: str | None = Field(
        sa_column=Column(TEXT(), nullable=True),
        description="Item description (copied from product if null, overrideable)",
    )
    price: Decimal | None = Field(
        sa_column=Column(NUMERIC(12, 2), nullable=True),
        description="Item price (calculated from product price + markup if null)",
    )
    currency_id: UUID | None = Field(
        foreign_key="currency.id",
        nullable=True,
        default=None,
        description="Currency ID (copied from product if null, overrideable)",
    )
    category_id: GUID | None = Field(
        foreign_key="category.id",
        default=None,
        index=True,
        description="Category ID (copied from product if null, overrideable)",
    )
    status: ProductStatus | None = Field(
        sa_column=Column(TEXT(), nullable=True, index=True),
        description="Item status (copied from product if null, overrideable)",
    )
    is_digital: bool | None = Field(
        sa_column=Column(Boolean(), nullable=True),
        description="Whether item is digital (copied from product if null, overrideable)",
    )
    attributes: Dict[str, Any] | None = Field(
        sa_column=Column(JSONB, nullable=True),
        description="Custom attributes (merged with product attributes if null)",
    )

    # Relationships
    product: "Product" = Relationship()
    seller: "Account" = Relationship()
    currency: Optional["Currency"] = Relationship()
    category: Optional["Category"] = Relationship()
