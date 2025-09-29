from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from src.core.helpers import optional
from src.core.types import GUID
from src.domain.enums import InventoriableType


class InventoryBase(BaseModel):
    """Base inventory schema with common fields."""

    inventoriable_type: InventoriableType = Field(..., description="Type of item being inventoried")
    inventoriable_id: GUID = Field(..., description="Reference to the product or product item")
    quantity_in_stock: int = Field(default=0, ge=0, description="The total quantity in stock")
    reserved_stock: int = Field(default=0, ge=0, description="The quantity reserved for pending orders")


class InventoryCreate(InventoryBase):
    """Schema for creating a new inventory entry."""


@optional
class InventoryUpdate(InventoryBase):
    """Schema for updating an inventory entry."""


class InventoryResponse(InventoryBase):
    """Schema for inventory response data."""

    id: GUID
    available_stock: int
    created_datetime: str
    updated_datetime: Optional[str]
