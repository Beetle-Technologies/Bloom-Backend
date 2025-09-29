from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from src.core.helpers import optional
from src.core.types import GUID
from src.domain.enums import InventoryActionType


class InventoryActionBase(BaseModel):
    """Base inventory action schema with common fields."""

    inventory_id: GUID = Field(..., description="ID of the inventory entry")
    action_type: InventoryActionType = Field(..., description="Type of action performed")
    quantity: int = Field(..., gt=0, description="Quantity affected by the action")
    reason: Optional[str] = Field(None, description="Optional reason for the action")


class InventoryActionCreate(InventoryActionBase):
    """Schema for creating a new inventory action."""


@optional
class InventoryActionUpdate(InventoryActionBase):
    """Schema for updating an inventory action."""


class InventoryActionResponse(InventoryActionBase):
    """Schema for inventory action response data."""

    id: GUID
    created_datetime: str
    updated_datetime: Optional[str]
