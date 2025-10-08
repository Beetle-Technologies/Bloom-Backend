from __future__ import annotations

import inflection
from pycountries import Country as CountryEnum
from pycountries import Currency as CurrencyCode
from pycountries import Language
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
from src.domain.repositories import (
    AccountTypeRepository,
    CategoryRepository,
    CountryRepository,
    CurrencyRepository,
    PermissionRepository,
)
from src.domain.schemas import AccountTypeCreate, CategoryCreate, CountryCreate, CurrencyCreate, PermissionCreate

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
        AccountTypeCreate(title=account_type.name, key=account_type.value) for account_type in AccountTypeEnum
    ]
    account_type_repo = AccountTypeRepository(session=session)

    await account_type_repo.bulk_create_if_not_exists(account_types)


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


async def _load_default_currencies(session: AsyncSession) -> None:
    """
    Load default currencies into the system.
    """
    common_currency_codes = [
        "USD",  # US Dollar (default)
        "EUR",  # Euro
        "GBP",  # British Pound Sterling
        "JPY",  # Japanese Yen
        "CAD",  # Canadian Dollar
        "AUD",  # Australian Dollar
        "CHF",  # Swiss Franc
        "CNY",  # Chinese Yuan Renminbi
        "INR",  # Indian Rupee
        "BRL",  # Brazilian Real
        "NGN",  # Nigerian Naira
        "ZAR",  # South African Rand
        "KES",  # Kenyan Shilling
        "GHS",  # Ghanaian Cedi
        "EGP",  # Egyptian Pound
    ]

    currencies_to_create: list[CurrencyCreate] = []
    currency_repo = CurrencyRepository(session=session)

    for currency_code in common_currency_codes:
        try:
            currency_enum = getattr(CurrencyCode, currency_code)
            currency_create = CurrencyCreate(
                code=currency_enum,
                is_active=True,
                is_default=(currency_code == "USD"),
            )
            currencies_to_create.append(currency_create)
        except AttributeError:
            print(f"Warning: Currency code {currency_code} not found in pycountries")
            continue

    await currency_repo.bulk_create_if_not_exists(currencies_to_create)


async def _load_default_countries(session: AsyncSession) -> None:
    """
    Load default countries into the system.
    """
    countries_data = [
        {"country_code": "US", "currency_code": "USD", "language_code": "ENG"},
        {"country_code": "GB", "currency_code": "GBP", "language_code": "ENG"},
        {"country_code": "CA", "currency_code": "CAD", "language_code": "ENG"},
        {"country_code": "AU", "currency_code": "AUD", "language_code": "ENG"},
        {"country_code": "DE", "currency_code": "EUR", "language_code": "GER"},
        {"country_code": "FR", "currency_code": "EUR", "language_code": "FRE"},
        {"country_code": "JP", "currency_code": "JPY", "language_code": "JPN"},
        {"country_code": "IN", "currency_code": "INR", "language_code": "ENG"},
        {"country_code": "BR", "currency_code": "BRL", "language_code": "POR"},
        {"country_code": "NG", "currency_code": "NGN", "language_code": "ENG"},
        {"country_code": "ZA", "currency_code": "ZAR", "language_code": "ENG"},
        {"country_code": "KE", "currency_code": "KES", "language_code": "ENG"},
        {"country_code": "GH", "currency_code": "GHS", "language_code": "ENG"},
        {"country_code": "EG", "currency_code": "EGP", "language_code": "ARA"},
        {"country_code": "CH", "currency_code": "CHF", "language_code": "GER"},
        {"country_code": "CN", "currency_code": "CNY", "language_code": "CHI"},
    ]

    country_repo = CountryRepository(session=session)
    currency_repo = CurrencyRepository(session=session)
    countries_to_create: list[CountryCreate] = []

    for country_data in countries_data:
        try:
            country_enum = getattr(CountryEnum, country_data["country_code"])
            currency_enum = getattr(CurrencyCode, country_data["currency_code"])
            language_enum = getattr(Language, country_data["language_code"])

            currency = await currency_repo.find_by_code(currency_enum)
            if not currency:
                print(
                    f"Warning: Currency {country_data['currency_code']} not found for country {country_data['country_code']}"
                )
                continue

            country_create = CountryCreate(
                name=country_enum,
                language=language_enum,
                currency_id=currency.id,
                is_active=True,
            )
            countries_to_create.append(country_create)

        except AttributeError as e:
            print(f"Warning: Could not create country {country_data['country_code']}: {e}")
            continue

    await country_repo.bulk_create_if_not_exists(countries_to_create)


async def _load_default_categories(session: AsyncSession) -> None:
    """
    Load default categories into the system.
    """
    category_repo = CategoryRepository(session=session)

    parent_categories = [
        {
            "title": "Jewelry",
            "description": "Jewelry, watches, and precious accessories",
            "parent_id": None,
            "sort_order": 1,
        },
        {
            "title": "Shoes",
            "description": "Footwear for all occasions and styles",
            "sort_order": 2,
            "parent_id": None,
        },
        {
            "title": "Fragrance",
            "description": "Fragrances, colognes, and scented products",
            "sort_order": 3,
            "parent_id": None,
        },
        {
            "title": "Skincare",
            "description": "Skincare products and beauty essentials",
            "sort_order": 4,
            "parent_id": None,
        },
    ]

    parent_categories_to_create: list[CategoryCreate] = []
    for category_data in parent_categories:
        category_create = CategoryCreate(
            title=category_data["title"],
            description=category_data["description"],
            parent_id=category_data["parent_id"],
            is_active=True,
            sort_order=category_data["sort_order"],
        )
        parent_categories_to_create.append(category_create)

    await category_repo.bulk_create_if_not_exists(parent_categories_to_create)

    jewelry_parent = await category_repo.find_by_title("Jewelry")
    fragrance_parent = await category_repo.find_by_title("Fragrance")

    if not jewelry_parent or not fragrance_parent:
        print("Warning: Could not find parent categories for subcategories")
        return

    subcategories = [
        {
            "title": "Necklaces",
            "description": "Necklaces and pendants",
            "parent_id": jewelry_parent.id,
            "sort_order": 1,
        },
        {
            "title": "Earrings",
            "description": "Earrings and ear accessories",
            "parent_id": jewelry_parent.id,
            "sort_order": 2,
        },
        {
            "title": "Bracelets",
            "description": "Bracelets and wrist accessories",
            "parent_id": jewelry_parent.id,
            "sort_order": 3,
        },
        {
            "title": "Perfumes",
            "description": "Premium perfumes and eau de toilette",
            "parent_id": fragrance_parent.id,
            "sort_order": 1,
        },
    ]

    subcategories_to_create: list[CategoryCreate] = []
    for category_data in subcategories:
        category_create = CategoryCreate(
            title=category_data["title"],
            description=category_data["description"],
            parent_id=category_data["parent_id"],
            is_active=True,
            sort_order=category_data["sort_order"],
        )
        subcategories_to_create.append(category_create)

    await category_repo.bulk_create_if_not_exists(subcategories_to_create)


async def load() -> None:
    if settings.LOAD_FIXTURES:
        async with db_context_manager() as session:
            await _load_default_account_types(session=session)
            await _load_default_permissions(session=session)
            await _load_default_currencies(session=session)
            await _load_default_countries(session=session)
            await _load_default_categories(session=session)
    else:
        print("Skipping loading fixtures as per configuration.")


async def main() -> None:
    await load()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
