from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoriableType
from src.domain.models.inventory import Inventory
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import InventoryCreate, InventoryUpdate

logger = get_logger(__name__)


class InventoryRepository(BaseRepository[Inventory, InventoryCreate, InventoryUpdate]):
    """
    Repository for managing inventory in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Inventory, session)

    async def get_by_item(self, inventoriable_type: InventoriableType, inventoriable_id: GUID) -> Inventory | None:
        """Get inventory by inventoriable item."""
        try:
            return await self.find_one_by_or_none(
                inventoriable_type=inventoriable_type, inventoriable_id=inventoriable_id
            )
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.inventory_repository.get_by_item:: error while getting inventory by item {inventoriable_type}:{inventoriable_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve inventory",
                detail="An error occurred while retrieving inventory.",
                metadata={
                    "inventoriable_type": inventoriable_type,
                    "inventoriable_id": inventoriable_id,
                },
            ) from e

    async def get_inventory_for_account(self, account_id: GUID) -> Sequence[Inventory]:
        """Get all inventory entries for an account."""
        try:
            # This would require joining with the inventoriable items to filter by account
            # For now, return all - this might need refinement based on business logic
            query = select(Inventory)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.inventory_repository.get_inventory_for_account:: error while getting inventory for account {account_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve inventory",
                detail="An error occurred while retrieving inventory for account.",
                metadata={"account_id": account_id},
            ) from e

    async def update_stock_levels(
        self, inventory_id: GUID, quantity_in_stock: int, reserved_stock: int
    ) -> Inventory | None:
        """Update stock levels for an inventory entry."""
        try:
            inventory = await self.find_one_by_and_none(id=inventory_id)
            if not inventory:
                return None

            update_data = InventoryUpdate(quantity_in_stock=quantity_in_stock, reserved_stock=reserved_stock)
            return await self.update(inventory_id, update_data)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.inventory_repository.update_stock_levels:: error while updating stock levels for inventory {inventory_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to update inventory stock levels",
                detail="An error occurred while updating inventory stock levels.",
                metadata={"inventory_id": inventory_id},
            ) from e
