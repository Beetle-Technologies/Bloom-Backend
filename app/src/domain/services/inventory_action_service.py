from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoryActionType
from src.domain.models.inventory_action import InventoryAction
from src.domain.repositories.inventory_action_repository import InventoryActionRepository
from src.domain.schemas.inventory_action import InventoryActionCreate, InventoryActionUpdate

logger = get_logger(__name__)


class InventoryActionService:
    """Service for managing inventory actions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.inventory_action_repository = InventoryActionRepository(session)

    async def get_actions_for_inventory(self, inventory_id: GUID) -> Sequence[InventoryAction]:
        """Get all actions for a specific inventory entry."""
        return await self.inventory_action_repository.get_actions_for_inventory(inventory_id)

    async def get_actions_by_type(self, action_type: InventoryActionType) -> Sequence[InventoryAction]:
        """Get all actions of a specific type."""
        return await self.inventory_action_repository.get_actions_by_type(action_type)

    async def create_action(self, action_data: InventoryActionCreate) -> InventoryAction:
        """Create a new inventory action."""
        return await self.inventory_action_repository.create(action_data)

    async def update_action(self, action_id: GUID, action_data: InventoryActionUpdate) -> InventoryAction | None:
        """Update an inventory action."""
        return await self.inventory_action_repository.update(action_id, action_data)
