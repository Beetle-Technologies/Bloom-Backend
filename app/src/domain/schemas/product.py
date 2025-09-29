from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from src.core.helpers import optional
from src.core.types import GUID
from src.domain.enums import ProductStatus


class ProductBase(BaseModel):
    """Base product schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="The name of the product")
    description: Optional[str] = Field(None, description="A description of the product")
    price: Decimal = Field(..., gt=0, description="The base price of the product")
    supplier_account_id: GUID = Field(..., description="Reference to the supplier account")
    currency_id: UUID = Field(..., description="The currency for the product price")
    category_id: Optional[GUID] = Field(None, description="The category this product belongs to")
    status: ProductStatus = Field(default=ProductStatus.DRAFT, description="The current status of the product")
    is_digital: bool = Field(default=False, description="Whether the product is a digital good")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON data containing flexible product attributes",
    )


class ProductCreate(ProductBase):
    """Schema for creating a new product."""


@optional
class ProductUpdate(ProductBase):
    """Schema for updating a product."""


class ProductResponse(ProductBase):
    """Schema for product response data."""

    id: GUID
    friendly_id: Optional[str]
    created_datetime: str
    updated_datetime: Optional[str]
    deleted_datetime: Optional[str]
