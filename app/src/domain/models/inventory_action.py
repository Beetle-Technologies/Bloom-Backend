from typing import TYPE_CHECKING

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import InventoryActionType

if TYPE_CHECKING:
    from src.domain.models import Inventory


class InventoryAction(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an action performed on inventory (e.g., stock in, transfer).

    Attributes:
        id (GUID): The unique identifier for the action.
        inventory_id (GUID): ID of the inventory entry.
        action_type (InventoryActionType): Type of action.
        quantity (int): Quantity affected.
        reason (str | None): Optional reason for the action.
        created_datetime (datetime): When the action occurred.
        updated_datetime (datetime | None): When the action was last updated.
    """

    SELECTABLE_FIELDS = [
        "id",
        "inventory_id",
        "action_type",
        "quantity",
        "reason",
        "created_datetime",
        "updated_datetime",
    ]

    inventory_id: GUID = Field(foreign_key="inventory.id", nullable=False, index=True)
    action_type: InventoryActionType = Field(sa_column=Column(TEXT(), nullable=False))
    quantity: int = Field(nullable=False)
    reason: str | None = Field(sa_column=Column(TEXT(), nullable=True))

    inventory: "Inventory" = Relationship(back_populates="actions")
