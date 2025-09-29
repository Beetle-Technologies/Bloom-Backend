from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.account_type_info_permission import AccountTypeInfoPermission
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import AccountTypeInfoPermissionCreate, AccountTypeInfoPermissionUpdate
from src.libs.query_engine import GeneralPaginationRequest

logger = get_logger(__name__)


class AccountTypeInfoPermissionRepository(
    BaseRepository[
        AccountTypeInfoPermission,
        AccountTypeInfoPermissionCreate,
        AccountTypeInfoPermissionUpdate,
    ]
):
    """
    Repository for managing account type info permissions in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AccountTypeInfoPermission, session)

    async def find_by_type_info_and_permission(
        self,
        account_type_info_id: GUID,
        permission_id: int,
        resource_id: str | None = None,
    ) -> AccountTypeInfoPermission | None:
        """
        Find permission by account type info ID and permission ID.

        Args:
            account_type_info_id (GUID): The account type info ID
            permission_id (int): The permission ID
            resource_id (str | None): Optional resource ID

        Returns:
            AccountTypeInfoPermission | None: The permission if found, otherwise None
        """
        kwargs = {
            "account_type_info_id": account_type_info_id,
            "permission_id": permission_id,
        }

        if resource_id is not None:
            kwargs["resource_id"] = resource_id

        return await self.find_one_by_and_none(**kwargs)

    async def bulk_create_if_not_exists(
        self, schemas: list[AccountTypeInfoPermissionCreate]
    ) -> list[AccountTypeInfoPermission]:
        """
        Bulk create permissions if they don't already exist.

        Args:
            schemas (list[AccountTypeInfoPermissionCreate]): List of permission data to create

        Returns:
            list[AccountTypeInfoPermission]: List of existing or newly created permissions
        """
        results = []
        for schema in schemas:
            existing = await self.find_by_type_info_and_permission(
                account_type_info_id=schema.account_type_info_id,
                permission_id=schema.permission_id,
                resource_id=schema.resource_id,
            )

            if existing:
                results.append(existing)
            else:
                result = await self.create(schema)
                results.append(result)

        return results

    async def find_by_account_type_info(self, account_type_info_id: GUID) -> list[AccountTypeInfoPermission]:
        """
        Find all permissions for a specific account type info.

        Args:
            account_type_info_id (GUID): The account type info ID

        Returns:
            list[AccountTypeInfoPermission]: List of permissions
        """

        pagination = GeneralPaginationRequest(filters={"account_type_info_id__eq": account_type_info_id})

        response = await self.find(pagination=pagination)
        return response.items
