from __future__ import annotations

from typing import Any, Dict

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import AccountTypeEnum
from src.domain.models import AccountTypeInfo
from src.domain.repositories import AccountTypeInfoRepository, AccountTypeRepository
from src.domain.schemas import AccountTypeInfoCreate, AccountTypeInfoUpdate

logger = get_logger(__name__)


class AccountTypeInfoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_type_info_repository = AccountTypeInfoRepository(session=self.session)
        self.account_type_repository = AccountTypeRepository(session=self.session)

    async def create_account_type_info(
        self,
        *,
        account_id: GUID,
        account_type: AccountTypeEnum,
        attributes: Dict[str, Any] | None = None,
    ) -> AccountTypeInfo:
        """
        Create account type info for an account.

        Args:
            account_id (GUID): The account ID
            account_type (AccountTypeEnum): The account type
            attributes (Dict[str, Any] | None): Optional attributes for the account type

        Returns:
            AccountTypeInfo: The created account type info

        Raises:
            ServiceError: If there is an error creating the account type info
        """
        try:
            account_type_obj = await self.account_type_repository.find_one_by_and_none(key=account_type.value)

            if not account_type_obj:
                raise errors.ServiceError(detail=f"Account type '{account_type.value}' not found", status=404)

            schema = AccountTypeInfoCreate(
                account_id=account_id,
                account_type_id=account_type_obj.id,
                attributes=attributes or {},
            )

            return await self.account_type_info_repository.create_if_not_exists(schema)

        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError creating account type info for account {account_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to create account type info", status=500) from de
        except errors.ServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error creating account type info for account {account_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to create account type info", status=500) from e

    async def get_account_type_info(
        self,
        *,
        account_id: GUID,
        account_type: AccountTypeEnum,
    ) -> AccountTypeInfo | None:
        """
        Get account type info for an account and type.

        Args:
            account_id (GUID): The account ID
            account_type (AccountTypeEnum): The account type

        Returns:
            AccountTypeInfo | None: The account type info if found, otherwise None
        """
        try:
            # Get the account type by key
            account_type_obj = await self.account_type_repository.find_one_by_and_none(key=account_type.value)

            if not account_type_obj:
                return None

            return await self.account_type_info_repository.find_by_account_and_type(
                account_id=account_id, account_type_id=account_type_obj.id
            )

        except Exception as e:
            logger.error(
                f"Error getting account type info for account {account_id}: {str(e)}",
                exc_info=True,
            )
            return None

    async def update_account_type_info(
        self,
        *,
        id: GUID,
        attributes: Dict[str, Any],
    ) -> AccountTypeInfo | None:
        """
        Update account type info attributes.

        Args:
            id (GUID): The account type info ID
            attributes (Dict[str, Any]): The new attributes

        Returns:
            AccountTypeInfo | None: The updated account type info

        Raises:
            ServiceError: If there is an error updating the account type info
        """
        try:
            schema = AccountTypeInfoUpdate(attributes=attributes)
            return await self.account_type_info_repository.update(id, schema)

        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError updating account type info {id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to update account type info", status=500) from de
        except Exception as e:
            logger.error(
                f"Unexpected error updating account type info {id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to update account type info", status=500) from e
