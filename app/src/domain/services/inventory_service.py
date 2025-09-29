from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.decorators import transactional
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoriableType, InventoryActionType
from src.domain.models.inventory import Inventory
from src.domain.repositories.inventory_action_repository import InventoryActionRepository
from src.domain.repositories.inventory_repository import InventoryRepository
from src.domain.schemas.inventory import InventoryCreate, InventoryUpdate
from src.domain.schemas.inventory_action import InventoryActionCreate

logger = get_logger(__name__)


class InventoryService:
    """Service for managing inventory operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.inventory_repository = InventoryRepository(session)
        self.inventory_action_repository = InventoryActionRepository(session)

    async def get_inventory_by_item(
        self, inventoriable_type: InventoriableType, inventoriable_id: GUID
    ) -> Inventory | None:
        """Get inventory for a specific item."""
        return await self.inventory_repository.get_by_item(inventoriable_type, inventoriable_id)

    async def create_inventory(self, inventory_data: InventoryCreate) -> Inventory:
        """Create a new inventory entry."""
        try:
            # Check if inventory already exists for this item
            existing = await self.get_inventory_by_item(
                inventory_data.inventoriable_type, inventory_data.inventoriable_id
            )
            if existing:
                raise errors.ServiceError(
                    message="Inventory already exists",
                    detail=f"Inventory for {inventory_data.inventoriable_type}:{inventory_data.inventoriable_id} already exists",
                )

            return await self.inventory_repository.create(inventory_data)
        except Exception as e:
            logger.exception(f"Error creating inventory: {e}")
            raise

    async def update_inventory(self, inventory_id: GUID, inventory_data: InventoryUpdate) -> Inventory | None:
        """Update an inventory entry."""
        return await self.inventory_repository.update(inventory_id, inventory_data)

    @transactional
    async def adjust_stock(
        self,
        inventoriable_type: InventoriableType,
        inventoriable_id: GUID,
        quantity_change: int,
        action_type: InventoryActionType,
        reason: str | None = None,
    ) -> Inventory:
        # Get or create inventory
        inventory = await self.get_inventory_by_item(inventoriable_type, inventoriable_id)
        if not inventory:
            # Create inventory with zero stock
            inventory_data = InventoryCreate(
                inventoriable_type=inventoriable_type,
                inventoriable_id=inventoriable_id,
                quantity_in_stock=0,
                reserved_stock=0,
            )
            inventory = await self.create_inventory(inventory_data)

        # Calculate new stock levels
        new_quantity = inventory.quantity_in_stock + quantity_change
        if new_quantity < 0:
            raise errors.ServiceError(
                message="Insufficient stock",
                detail=f"Cannot reduce stock below zero. Current: {inventory.quantity_in_stock}, Requested change: {quantity_change}",
            )

        # Update inventory
        update_data = InventoryUpdate(
            quantity_in_stock=new_quantity,
            reserved_stock=inventory.reserved_stock,  # Keep reserved stock as is
        )
        updated_inventory = await self.update_inventory(inventory.id, update_data)
        if not updated_inventory:
            raise errors.ServiceError(
                message="Failed to update inventory",
                detail="Could not update inventory stock levels",
            )

        # Record the action
        action_data = InventoryActionCreate(
            inventory_id=inventory.id,
            action_type=action_type,
            quantity=abs(quantity_change),
            reason=reason,
        )
        await self.inventory_action_repository.create(action_data)

        return updated_inventory

    @transactional
    async def reserve_stock(
        self,
        inventoriable_type: InventoriableType,
        inventoriable_id: GUID,
        quantity: int,
    ) -> Inventory:
        inventory = await self.get_inventory_by_item(inventoriable_type, inventoriable_id)
        if not inventory:
            raise errors.NotFoundError(
                message="Inventory not found",
                detail=f"No inventory found for {inventoriable_type}:{inventoriable_id}",
            )

        if not inventory.can_reserve(quantity):
            raise errors.ServiceError(
                message="Insufficient available stock",
                detail=f"Cannot reserve {quantity} items. Available: {inventory.available_stock}",
            )

        update_data = InventoryUpdate(
            quantity_in_stock=inventory.quantity_in_stock,
            reserved_stock=inventory.reserved_stock + quantity,
        )
        updated_inventory = await self.update_inventory(inventory.id, update_data)
        if not updated_inventory:
            raise errors.ServiceError(message="Failed to update inventory", detail="Could not reserve stock")
        return updated_inventory

    @transactional
    async def release_stock(
        self,
        inventoriable_type: InventoriableType,
        inventoriable_id: GUID,
        quantity: int,
    ) -> Inventory:
        inventory = await self.get_inventory_by_item(inventoriable_type, inventoriable_id)
        if not inventory:
            raise errors.NotFoundError(
                message="Inventory not found",
                detail=f"No inventory found for {inventoriable_type}:{inventoriable_id}",
            )

        new_reserved = inventory.reserved_stock - quantity
        if new_reserved < 0:
            raise errors.ServiceError(
                message="Cannot release more stock than reserved",
                detail=f"Reserved: {inventory.reserved_stock}, Requested release: {quantity}",
            )

        update_data = InventoryUpdate(quantity_in_stock=inventory.quantity_in_stock, reserved_stock=new_reserved)
        updated_inventory = await self.update_inventory(inventory.id, update_data)
        if not updated_inventory:
            raise errors.ServiceError(message="Failed to update inventory", detail="Could not release stock")
        return updated_inventory
