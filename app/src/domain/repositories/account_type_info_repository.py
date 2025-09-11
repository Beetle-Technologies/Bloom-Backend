from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.types import GUID
from src.domain.models.account_type_info import AccountTypeInfo
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import AccountTypeInfoCreate, AccountTypeInfoUpdate

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AccountTypeInfoRepository(BaseRepository[AccountTypeInfo, AccountTypeInfoCreate, AccountTypeInfoUpdate]):
    """
    Repository for managing account type information in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AccountTypeInfo, session)

    async def find_by_account_and_type(self, account_id: GUID, account_type_id: GUID) -> AccountTypeInfo | None:
        """
        Find account type info by account ID and account type ID.

        Args:
            account_id (GUID): The account ID
            account_type_id (GUID): The account type ID

        Returns:
            AccountTypeInfo | None: The account type info if found, otherwise None
        """
        return await self.find_one_by_and_none(account_id=account_id, account_type_id=account_type_id)

    async def create_if_not_exists(self, schema: AccountTypeInfoCreate) -> AccountTypeInfo:
        """
        Create account type info if it doesn't already exist.

        Args:
            schema (AccountTypeInfoCreate): The account type info data

        Returns:
            AccountTypeInfo: The existing or newly created account type info
        """
        existing = await self.find_by_account_and_type(
            account_id=schema.account_id, account_type_id=schema.account_type_id
        )

        if existing:
            return existing

        return await self.create(schema)
