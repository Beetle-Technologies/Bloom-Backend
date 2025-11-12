from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from src.core.helpers import optional
from src.core.types import GUID
from src.domain.enums import ProductStatus


class ProductItemBase(BaseModel):
    """Base product item schema with common fields."""

    product_id: Optional[GUID] = Field(None, description="Reference to the original product")
    seller_account_id: GUID = Field(..., description="Reference to the reseller account")
    markup_percentage: Decimal = Field(
        default=Decimal(0),
        ge=0,
        description="Markup percentage applied to original product price",
    )
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Item name (overrideable)")
    description: Optional[str] = Field(None, description="Item description (overrideable)")
    price: Optional[Decimal] = Field(None, gt=0, description="Item price (calculated if null)")
    currency_id: Optional[UUID] = Field(None, description="Currency ID (overrideable)")
    category_id: Optional[GUID] = Field(None, description="Category ID (overrideable)")
    status: Optional[ProductStatus] = Field(None, description="Item status (overrideable)")
    is_digital: Optional[bool] = Field(None, description="Whether item is digital (overrideable)")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Custom attributes (overrideable)")


class ProductItemCreate(ProductItemBase):
    """Schema for creating a new product item."""

    id: Optional[GUID] = None


@optional
class ProductItemUpdate(ProductItemBase):
    """Schema for updating a product item."""


class ProductItemResponse(ProductItemBase):
    """Schema for product item response data."""

    id: GUID
    friendly_id: Optional[str]
    created_datetime: str
    updated_datetime: Optional[str]
    deleted_datetime: Optional[str]
