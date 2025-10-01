from __future__ import annotations

from typing import ClassVar

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.enums import AccountTypeEnum
from src.domain.models import AccountTypeInfoPermission
from src.domain.repositories import AccountTypeInfoPermissionRepository, PermissionRepository
from src.domain.schemas import AccountTypeInfoPermissionCreate

logger = get_logger(__name__)


class PermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.permission_repository = PermissionRepository(session=self.session)
        self.account_type_info_permission_repository = AccountTypeInfoPermissionRepository(session=self.session)

    ACCOUNT_TYPE_PERMISSION_MAPPING: ClassVar[dict[AccountTypeEnum, list[str]]] = {
        AccountTypeEnum.USER: [
            "accounts:read",
            "accounts:update",
            "attachments:manage",
            "country:read",
            "currency:read",
            "category:read",
            "cart:read",
            "cart:write",
            "cart:update",
            "cart:delete",
            "orders:read",
            "orders:write",
            "reviews:read",
            "reviews:write",
            "reviews:update",
            "reviews:delete",
            "products:read",
            "product_items:read",
            "wishlist:read",
            "wishlist:write",
            "wishlist:update",
            "wishlist:delete",
            "notifications:read",
            "notifications:update",
        ],
        AccountTypeEnum.BUSINESS: [
            "accounts:read",
            "accounts:update",
            "attachments:manage",
            "country:read",
            "currency:read",
            "products:read",
            "product_items:read",
            "product_item_requests:read",
            "product_item_requests:update",
            "category:read",
            "orders:read",
            "orders:write",
            "orders:update",
            "inventory:read",
            "inventory:write",
            "inventory_actions:manage",
            "inventory:update",
            "kyc_attempts:read",
            "kyc_attempts:write",
            "notifications:read",
            "notifications:update",
            "banking_info:read",
            "banking_info:write",
            "banking_info:update",
        ],
        AccountTypeEnum.SUPPLIER: [
            "accounts:read",
            "accounts:update",
            "attachments:manage",
            "country:read",
            "currency:read",
            "products:read",
            "products:write",
            "products:update",
            "products:delete",
            "category:read",
            "category:write",
            "category:update",
            "orders:read",
            "orders:update",
            "inventory:read",
            "inventory:write",
            "inventory:update",
            "inventory:delete",
            "inventory_actions:manage",
            "product_items:read",
            "product_item_requests:manage",
            "product_items:write",
            "product_items:update",
            "product_items:delete",
            "kyc_attempts:read",
            "kyc_attempts:write",
            "notifications:read",
            "notifications:update",
            "banking_info:read",
            "banking_info:write",
            "banking_info:update",
        ],
        AccountTypeEnum.ADMIN: [
            "accounts:manage",
            "account_types:manage",
            "products:manage",
            "country:manage",
            "currency:manage",
            "category:manage",
            "orders:manage",
            "inventory:manage",
            "product_item_requests:manage",
            "permissions:manage",
            "countries:manage",
            "currencies:manage",
            "notifications:manage",
            "banking_info:manage",
            "kyc_documents:manage",
            "kyc_attempts:manage",
            "audit_logs:read",
            "event_outbox:read",
            "reviews:manage",
            "wishlist:manage",
            "cart:manage",
            "product_items:manage",
            "attachments:manage",
        ],
    }

    async def assign_permissions_to_account_type_info(
        self,
        *,
        account_type_info_id: GUID,
        account_type: AccountTypeEnum,
        assigned_by: GUID | None = None,
    ) -> list[AccountTypeInfoPermission]:
        """
        Assign default permissions to an account type info based on the account type.

        Args:
            account_type_info_id (GUID): The account type info ID
            account_type (AccountTypeEnum): The account type
            assigned_by (GUID | None): The ID of who assigned the permissions

        Returns:
            list[AccountTypeInfoPermission]: List of created permissions

        Raises:
            ServiceError: If there is an error assigning permissions
        """
        try:
            permission_scopes = self.ACCOUNT_TYPE_PERMISSION_MAPPING.get(account_type, [])

            if not permission_scopes:
                logger.warning(f"No permission mapping found for account type: {account_type.value}")
                return []

            # Get all permissions that match the scopes
            permission_schemas = []

            for scope in permission_scopes:
                if ":" not in scope:
                    logger.warning(f"Invalid permission scope format: {scope}")
                    continue

                resource, action = scope.split(":", 1)

                # Find the permission by resource and action
                permission = await self.permission_repository.find_one_by_and_none(resource=resource, action=action)

                if not permission:
                    logger.warning(f"Permission not found for scope: {scope}")
                    continue

                permission_schema = AccountTypeInfoPermissionCreate(
                    account_type_info_id=account_type_info_id,
                    permission_id=permission.id,
                    granted=True,
                    assigned_by=assigned_by,
                )

                permission_schemas.append(permission_schema)

            # Bulk create permissions
            if permission_schemas:
                return await self.account_type_info_permission_repository.bulk_create_if_not_exists(permission_schemas)

            return []

        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError assigning permissions to account type info {account_type_info_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to assign permissions") from de
        except Exception as e:
            logger.error(
                f"Unexpected error assigning permissions to account type info {account_type_info_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to assign permissions") from e

    async def get_permissions_for_account_type_info(
        self,
        *,
        account_type_info_id: GUID,
    ) -> list[AccountTypeInfoPermission]:
        """
        Get all permissions for an account type info.

        Args:
            account_type_info_id (GUID): The account type info ID

        Returns:
            list[AccountTypeInfoPermission]: List of permissions
        """
        try:
            return await self.account_type_info_permission_repository.find_by_account_type_info(account_type_info_id)
        except Exception as e:
            logger.error(
                f"Error getting permissions for account type info {account_type_info_id}: {str(e)}",
                exc_info=True,
            )
            return []

    async def revoke_permission(
        self,
        *,
        account_type_info_id: GUID,
        permission_id: int,
        resource_id: str | None = None,
    ) -> bool:
        """
        Revoke a specific permission from an account type info.

        Args:
            account_type_info_id (GUID): The account type info ID
            permission_id (int): The permission ID
            resource_id (str | None): Optional resource ID

        Returns:
            bool: True if permission was revoked, False if not found

        Raises:
            ServiceError: If there is an error revoking the permission
        """
        try:
            permission = await self.account_type_info_permission_repository.find_by_type_info_and_permission(
                account_type_info_id=account_type_info_id,
                permission_id=permission_id,
                resource_id=resource_id,
            )

            if not permission:
                return False

            updated = await self.account_type_info_permission_repository.update(permission.id, {"granted": False})

            return updated is not None

        except errors.DatabaseError as de:
            logger.error(f"DatabaseError revoking permission: {de.detail}", exc_info=True)
            raise errors.ServiceError(detail="Failed to revoke permission") from de
        except Exception as e:
            logger.error(f"Unexpected error revoking permission: {str(e)}", exc_info=True)
            raise errors.ServiceError(detail="Failed to revoke permission") from e
