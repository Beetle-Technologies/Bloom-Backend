from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel import DDL, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import db_context_manager
from src.core.database.triggers import (
    ACCOUNT_AUDIT_LOG_TRIGGER,
    ACCOUNT_SEARCH_TRIGGER,
    ACCOUNT_SEARCH_TRIGGER_FUNCTION,
    AUDIT_LOG_TRIGGER_FUNCTION,
    CATEGORY_SEARCH_TRIGGER,
    CATEGORY_SEARCH_TRIGGER_FUNCTION,
    COUNTRY_SEARCH_TRIGGER,
    COUNTRY_SEARCH_TRIGGER_FUNCTION,
    CURRENCY_SEARCH_TRIGGER,
    CURRENCY_SEARCH_TRIGGER_FUNCTION,
    PRODUCT_AUDIT_LOG_TRIGGER,
    PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_FUNCTION,
    PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_TRIGGER,
    PRODUCT_ITEM_SEARCH_TRIGGER,
    PRODUCT_ITEM_SEARCH_TRIGGER_FUNCTION,
    PRODUCT_ITEM_TRIGGER,
    PRODUCT_ITEM_TRIGGER_FUNCTION,
    PRODUCT_SEARCH_TRIGGER,
    PRODUCT_SEARCH_TRIGGER_FUNCTION,
    TOKEN_CLEANUP_SCHEDULED_TRIGGER,
    TOKEN_CLEANUP_TRIGGER,
    TOKEN_CLEANUP_TRIGGER_FUNCTION,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


async def init_db(db_engine: AsyncEngine) -> None:
    """Initialize database connection"""
    async with AsyncSession(db_engine) as session:
        try:
            (await session.exec(select(1))).all()
        except Exception as e:
            raise e


async def check_db_health(db_engine: AsyncEngine) -> dict[str, str]:
    """Check database health"""
    try:
        async with AsyncSession(db_engine) as session:
            await session.exec(select(1))
            return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}


async def _setup_product_item_triggers(session: AsyncSession) -> None:
    """
    Set up database triggers for ProductItem model.

    Args:
        engine: SQLAlchemy engine instance
    """
    await session.exec(PRODUCT_ITEM_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_FUNCTION)  # type: ignore

    await session.exec(PRODUCT_ITEM_TRIGGER)  # type: ignore
    await session.exec(PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_TRIGGER)  # type: ignore


async def _drop_product_item_triggers(session: AsyncSession) -> None:
    """
    Drop database triggers for ProductItem model.
    """
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_item_populate_fields ON product_items;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_price_update_items ON products;"))  # type: ignore

    await session.exec(DDL("DROP FUNCTION IF EXISTS populate_product_item_fields();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_product_items_on_product_price_change();"))  # type: ignore


async def _setup_audit_log_triggers(session: AsyncSession) -> None:
    """
    Set up database triggers for AuditLog model.
    """

    await session.exec(AUDIT_LOG_TRIGGER_FUNCTION)  # type: ignore

    await session.exec(ACCOUNT_AUDIT_LOG_TRIGGER)  # type: ignore
    await session.exec(PRODUCT_AUDIT_LOG_TRIGGER)  # type: ignore


async def _drop_audit_log_triggers(session: AsyncSession) -> None:
    """
    Drop database triggers for AuditLog model.
    """
    await session.exec(DDL("DROP TRIGGER IF EXISTS account_audit_log ON account;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_audit_log ON products;"))  # type: ignore


async def _setup_token_cleanup_triggers(session: AsyncSession) -> None:
    """
    Set up database triggers for Token cleanup.
    """
    await session.exec(TOKEN_CLEANUP_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(TOKEN_CLEANUP_SCHEDULED_TRIGGER)  # type: ignore

    await session.exec(TOKEN_CLEANUP_TRIGGER)  # type: ignore


async def _drop_token_cleanup_triggers(session: AsyncSession) -> None:
    """
    Drop database triggers for Token cleanup.
    """
    await session.exec(DDL("DROP TRIGGER IF EXISTS token_cleanup_trigger ON tokens;"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS cleanup_expired_tokens();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS scheduled_token_cleanup();"))  # type: ignore


async def _setup_search_triggers(session: AsyncSession) -> None:
    """
    Set up database triggers for search vectors.
    """
    await session.exec(ACCOUNT_SEARCH_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(ACCOUNT_SEARCH_TRIGGER)  # type: ignore

    await session.exec(PRODUCT_SEARCH_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(PRODUCT_SEARCH_TRIGGER)  # type: ignore

    await session.exec(PRODUCT_ITEM_SEARCH_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(PRODUCT_ITEM_SEARCH_TRIGGER)  # type: ignore

    await session.exec(CATEGORY_SEARCH_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(CATEGORY_SEARCH_TRIGGER)  # type: ignore

    await session.exec(COUNTRY_SEARCH_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(COUNTRY_SEARCH_TRIGGER)  # type: ignore

    await session.exec(CURRENCY_SEARCH_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(CURRENCY_SEARCH_TRIGGER)  # type: ignore


async def _drop_search_triggers(session: AsyncSession) -> None:
    """
    Drop database triggers for search vectors.
    """

    await session.exec(DDL("DROP TRIGGER IF EXISTS account_search_update ON accounts;"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_account_search_vector();"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_search_update ON products;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_item_search_update ON product_items;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS category_search_update ON category;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS country_search_update ON country;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS currency_search_update ON currency;"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_product_search_vector();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_product_item_search_vector();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_category_search_vector();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_country_search_vector();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_currency_search_vector();"))  # type: ignore


async def register_triggers() -> None:
    """
    Register all database triggers.
    """
    async with db_context_manager() as session:
        await _setup_product_item_triggers(session)
        # await _setup_audit_log_triggers(session)
        await _setup_token_cleanup_triggers(session)
        await _setup_search_triggers(session)

        await session.commit()


async def drop_triggers() -> None:
    """
    Drop all database triggers.
    """
    async with db_context_manager() as session:
        await _drop_product_item_triggers(session)
        await _drop_audit_log_triggers(session)
        await _drop_token_cleanup_triggers(session)
        await _drop_search_triggers(session)

        await session.commit()
