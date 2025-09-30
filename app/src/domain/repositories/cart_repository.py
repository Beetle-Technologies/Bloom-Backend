from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.cart import Cart
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.cart import CartCreate, CartUpdate
from src.libs.query_engine import BaseQueryEngineParams

logger = get_logger(__name__)


class CartRepository(BaseRepository[Cart, CartCreate, CartUpdate]):
    """
    Repository for managing carts in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Cart, session)

    async def get_by_friendly_id(self, friendly_id: str) -> Cart | None:
        """Get cart by friendly ID."""
        try:
            return await self.find_one_by_or_none(friendly_id=friendly_id)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.cart_repository.get_by_friendly_id:: error while getting cart by friendly_id {friendly_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve cart",
                detail="An error occurred while retrieving cart by friendly ID.",
                metadata={"friendly_id": friendly_id},
            ) from e

    async def get_cart_by_account_type_info(self, account_type_info_id: GUID) -> Cart | None:
        """Get cart by account type info ID."""
        try:
            return await self.query(
                params=BaseQueryEngineParams(
                    filters={"account_type_info_id__eq": str(account_type_info_id)},
                )
            )
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.cart_repository.get_cart_by_account_type_info:: error while getting cart by account_type_info_id {account_type_info_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve cart",
                detail="An error occurred while retrieving cart by account type info ID.",
                metadata={"account_type_info_id": str(account_type_info_id)},
            ) from e
