from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.database.session import db_context_manager
from src.domain.enums import AccountType
from src.domain.repositories import AccountTypeRepository
from src.domain.schemas import AccountTypeCreate

# from src.domain.enums.permission import PermissionAction, PermissionResource
# from src.domain.schemas.permission import PermissionBatchCreate, PermissionCreate
# from src.domain.services.permission_service import PermissionService


# async def _load_permissions(session: AsyncSession) -> None:
#     """
#     Load permissions into the database.
#     """

#     def generate_all_permissions() -> PermissionBatchCreate:
#         """
#         Generate all possible combinations of resource and action permissions.

#         Returns:
#             PermissionBatchCreate: Object containing all permission combinations
#         """
#         permissions: list[PermissionCreate] = []

#         for resource, action in product(PermissionResource, PermissionAction):
#             permission = PermissionCreate(
#                 namespace=resource.value,
#                 action=action.value,
#                 description=f"Permission to {action.value} {resource.value.replace('_', ' ')}",
#             )
#             permissions.append(permission)

#         return PermissionBatchCreate(permissions=permissions)

#     permission_service = PermissionService(session=session)
#     batch_permissions = generate_all_permissions()
#     await permission_service.add_permissions(batch=batch_permissions)


async def _load_default_account_types(session: AsyncSession) -> None:
    """
    Load default account types into the system.
    """
    account_types: list[AccountTypeCreate] = [
        AccountTypeCreate(title=account_type.name, key=account_type.value)
        for account_type in AccountType
    ]
    account_type_repo = AccountTypeRepository(session=session)

    for account_type in account_types:
        await account_type_repo.create(schema=account_type)


async def load() -> None:
    if settings.LOAD_FIXTURES:
        async with db_context_manager() as session:
            await _load_default_account_types(session=session)
            # await _load_permissions(session=session)
            pass


async def main() -> None:
    await load()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
