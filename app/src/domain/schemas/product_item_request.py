from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from src.core.helpers import optional
from src.core.types import GUID
from src.domain.enums import ProductItemRequestStatus


class ProductItemRequestBase(BaseModel):
    """Base product item request schema with common fields."""

    seller_account_id: GUID = Field(..., description="ID of the requesting seller account")
    supplier_account_id: GUID = Field(..., description="ID of the supplier account")
    product_id: GUID = Field(..., description="ID of the product to resell")
    requested_quantity: int = Field(..., gt=0, description="Quantity requested")
    status: ProductItemRequestStatus = Field(
        default=ProductItemRequestStatus.PENDING, description="Status of the request"
    )
    mode: str = Field(
        default="implicit",
        max_length=50,
        description="Request mode (implicit or explicit)",
    )


class ProductItemRequestCreate(ProductItemRequestBase):
    """Schema for creating a new product item request."""


@optional
class ProductItemRequestUpdate(ProductItemRequestBase):
    """Schema for updating a product item request."""


class ProductItemRequestResponse(ProductItemRequestBase):
    """Schema for product item request response data."""

    id: GUID
    created_datetime: str
    updated_datetime: Optional[str]
