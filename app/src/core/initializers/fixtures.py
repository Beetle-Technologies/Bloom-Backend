from __future__ import annotations

import inflection
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.database.session import db_context_manager
from src.domain.enums import AccountTypeEnum
from src.domain.models import (
    Account,
    AccountType,
    AccountTypeGroup,
    AccountTypeInfo,
    AccountTypeInfoPermission,
    Address,
    Attachment,
    AttachmentBlob,
    AttachmentVariant,
    AuditLog,
    BankingInfo,
    Cart,
    CartItem,
    Category,
    Country,
    Currency,
    EventOutbox,
    Inventory,
    InventoryAction,
    KYCAttempt,
    KYCDocument,
    KYCDocumentType,
    KYCDocumentVerificationComment,
    Notification,
    NotificationPreference,
    NotificationTemplate,
    Order,
    OrderInvoice,
    OrderItem,
    Permission,
    Product,
    ProductItem,
    ProductItemRequest,
    Review,
    Wishlist,
    WishlistItem,
)
from src.domain.repositories import AccountTypeRepository, PermissionRepository
from src.domain.schemas import AccountTypeCreate, PermissionCreate

MODEL_CLASSES = [
    Account,
    AccountType,
    AccountTypeGroup,
    AccountTypeInfo,
    AccountTypeInfoPermission,
    Address,
    Attachment,
    AttachmentBlob,
    AttachmentVariant,
    AuditLog,
    BankingInfo,
    Cart,
    CartItem,
    Category,
    Country,
    Currency,
    EventOutbox,
    Inventory,
    InventoryAction,
    KYCAttempt,
    KYCDocument,
    KYCDocumentType,
    KYCDocumentVerificationComment,
    Notification,
    NotificationPreference,
    NotificationTemplate,
    Order,
    OrderInvoice,
    OrderItem,
    Permission,
    Product,
    ProductItem,
    ProductItemRequest,
    Review,
    Wishlist,
    WishlistItem,
]


STANDARD_ACTIONS = ["read", "write", "update", "delete", "manage"]


def get_table_name_from_model(model_class) -> str:
    """
    Get the table name from a model class.

    Args:
        model_class: The SQLModel class

    Returns:
        str: The table name
    """
    if hasattr(model_class, "__tablename__") and model_class.__tablename__:
        return model_class.__tablename__

    return inflection.pluralize(inflection.underscore(model_class.__name__))


async def _load_default_account_types(session: AsyncSession) -> None:
    """
    Load default account types into the system.
    """
    account_types: list[AccountTypeCreate] = [
        AccountTypeCreate(title=account_type.name, key=account_type.value)
        for account_type in AccountTypeEnum
    ]
    account_type_repo = AccountTypeRepository(session=session)

    for account_type in account_types:
        await account_type_repo.create_if_not_exists(schema=account_type)


async def _load_default_permissions(session: AsyncSession) -> None:
    """
    Load default permissions for all model tables into the system.
    """
    permission_repo = PermissionRepository(session=session)
    permissions_to_create: list[PermissionCreate] = []

    for model_class in MODEL_CLASSES:
        table_name = get_table_name_from_model(model_class)

        for action in STANDARD_ACTIONS:
            permission = PermissionCreate(
                resource=table_name,
                action=action,
                description=f"Permission to {action} {table_name}",
            )
            permissions_to_create.append(permission)

    await permission_repo.bulk_create_if_not_exists(permissions_to_create)


async def load() -> None:
    if settings.LOAD_FIXTURES:
        async with db_context_manager() as session:
            await _load_default_account_types(session=session)
            await _load_default_permissions(session=session)
    else:
        print("Skipping loading fixtures as per configuration.")


async def main() -> None:
    await load()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
