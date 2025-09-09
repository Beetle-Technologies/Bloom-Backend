from __future__ import annotations

import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from src.domain.models.account_type import AccountType
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import AccountTypeCreate, AccountTypeUpdate

logger = logging.getLogger(__name__)


class AccountTypeRepository(
    BaseRepository[AccountType, AccountTypeCreate, AccountTypeUpdate]
):
    """
    Repository for managing account type in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AccountType, session)
        pass
