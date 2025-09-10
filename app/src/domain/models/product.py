from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Column
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC
from sqlmodel import TEXT, Field, Relationship
from src.core.database.mixins import DeletableMixin, FriendlyMixin, GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import ProductStatus

if TYPE_CHECKING:
    from src.domain.models import Account, Category, Currency, ProductItem, ProductItemRequest


class Product(GUIDMixin, FriendlyMixin, DeletableMixin, TimestampMixin, table=True):
    """
    Represents a product in the system.

    Attributes:
        id (GUID): The unique identifier for the product.
        friendly_id (str | None): A url-friendly identifier for the product.
        name (str): The name of the product.
        description (str | None): A description of the product.
        price (Decimal): The base price of the product.
        supplier_account_id (GUID): Reference to the supplier account that provides this product.
        currency_id (UUID): The currency for the product price.
        category_id (GUID | None): The category this product belongs to.
        status (ProductStatus): The current status of the product.
        attributes (dict[str, Any]): JSON data containing flexible product attributes.
        is_digital (bool): Whether the product is a digital good.
        created_datetime (datetime): The timestamp when the product was created.
        updated_datetime (datetime | None): The timestamp when the product was last updated.
        deleted_datetime (datetime | None): The timestamp when the product was deleted.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "friendly_id",
        "name",
        "description",
        "price",
        "supplier_account_id",
        "currency_id",
        "category_id",
        "status",
        "is_digital",
        "attributes",
        "created_datetime",
        "updated_datetime",
        "deleted_datetime",
    ]

    name: str = Field(
        sa_column=Column(TEXT(), nullable=False, index=True),
    )
    description: str | None = Field(
        sa_column=Column(TEXT(), nullable=True),
    )
    price: Decimal = Field(
        sa_column=Column(NUMERIC(12, 2), nullable=False),
    )

    supplier_account_id: GUID = Field(foreign_key="accounts.id", nullable=False, index=True)
    currency_id: UUID = Field(foreign_key="currency.id", nullable=False)
    category_id: GUID | None = Field(foreign_key="category.id", default=None, index=True)

    status: ProductStatus = Field(sa_column=Column(TEXT(), nullable=False, index=True, default=ProductStatus.DRAFT))
    is_digital: bool = Field(sa_column=Column(Boolean(), nullable=False, default=False))
    attributes: dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False, default=dict),
        description="JSON data containing flexible product attributes",
    )

    # Relationships
    supplier: "Account" = Relationship()
    currency: "Currency" = Relationship()
    category: Optional["Category"] = Relationship(back_populates="products")
    product_items: List["ProductItem"] = Relationship(back_populates="product")
    resale_requests: List["ProductItemRequest"] = Relationship(back_populates="product")
