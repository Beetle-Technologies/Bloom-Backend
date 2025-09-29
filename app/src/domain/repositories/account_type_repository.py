from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.domain.models.account_type import AccountType
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import AccountTypeCreate, AccountTypeUpdate

logger = get_logger(__name__)


class AccountTypeRepository(BaseRepository[AccountType, AccountTypeCreate, AccountTypeUpdate]):
    """
    Repository for managing account type in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AccountType, session)

    async def create_if_not_exists(self, schema: AccountTypeCreate) -> AccountType:
        """
        Create an account type if it doesn't already exist.

        Args:
            schema (AccountTypeCreate): The account type data

        Returns:
            AccountType: The existing or newly created account type
        """
        existing = await self.find_one_by_and_none(key=schema.key)

        if existing:
            return existing

        return await self.create(schema)

    async def bulk_create_if_not_exists(self, schemas: list[AccountTypeCreate]) -> list[AccountType]:
        """
        Bulk create account types if they don't already exist.

        Args:
            schemas (list[AccountTypeCreate]): List of account type data to create

        Returns:
            list[AccountType]: List of existing or newly created account types
        """
        results = []
        for schema in schemas:
            result = await self.create_if_not_exists(schema)
            results.append(result)
        return results
