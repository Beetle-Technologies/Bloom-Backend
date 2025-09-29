from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import InventoryActionType
from src.domain.models.inventory_action import InventoryAction
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import InventoryActionCreate, InventoryActionUpdate

logger = get_logger(__name__)


class InventoryActionRepository(BaseRepository[InventoryAction, InventoryActionCreate, InventoryActionUpdate]):
    """
    Repository for managing inventory actions in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InventoryAction, session)

    async def get_actions_for_inventory(self, inventory_id: GUID) -> Sequence[InventoryAction]:
        """Get all actions for a specific inventory entry."""
        try:
            query = select(InventoryAction).where(InventoryAction.inventory_id == inventory_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.inventory_action_repository.get_actions_for_inventory:: error while getting actions for inventory {inventory_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve inventory actions",
                detail="An error occurred while retrieving inventory actions.",
                metadata={"inventory_id": inventory_id},
            ) from e

    async def get_actions_by_type(self, action_type: InventoryActionType) -> Sequence[InventoryAction]:
        """Get all actions of a specific type."""
        try:
            query = select(InventoryAction).where(InventoryAction.action_type == action_type)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.inventory_action_repository.get_actions_by_type:: error while getting actions by type {action_type}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve inventory actions",
                detail="An error occurred while retrieving inventory actions by type.",
                metadata={"action_type": action_type},
            ) from e
