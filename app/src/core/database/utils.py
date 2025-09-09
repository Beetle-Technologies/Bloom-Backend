import logging

from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel import DDL, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import db_context_manager
from src.core.database.triggers import (
    ACCOUNT_AUDIT_LOG_TRIGGER,
    AUDIT_LOG_TRIGGER_FUNCTION,
    PRODUCT_AUDIT_LOG_TRIGGER,
    PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_FUNCTION,
    PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_TRIGGER,
    PRODUCT_ITEM_TRIGGER,
    PRODUCT_ITEM_TRIGGER_FUNCTION,
)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

logger = logging.getLogger(__name__)


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
    # Create the trigger functions
    await session.exec(PRODUCT_ITEM_TRIGGER_FUNCTION)  # type: ignore
    await session.exec(PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_FUNCTION)  # type: ignore

    # Create the triggers
    await session.exec(PRODUCT_ITEM_TRIGGER)  # type: ignore
    await session.exec(PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_TRIGGER)  # type: ignore


async def _drop_product_item_triggers(session: AsyncSession) -> None:
    """
    Drop database triggers for ProductItem model.
    """
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_item_populate_fields ON product_items;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_price_update_items ON products;"))  # type: ignore

    # Drop functions
    await session.exec(DDL("DROP FUNCTION IF EXISTS populate_product_item_fields();"))  # type: ignore
    await session.exec(DDL("DROP FUNCTION IF EXISTS update_product_items_on_product_price_change();"))  # type: ignore


async def _setup_audit_log_triggers(session: AsyncSession) -> None:
    """
    Set up database triggers for AuditLog model.
    """

    # Create the trigger functions
    await session.exec(AUDIT_LOG_TRIGGER_FUNCTION)  # type: ignore

    # Create the triggers
    await session.exec(ACCOUNT_AUDIT_LOG_TRIGGER)  # type: ignore
    await session.exec(PRODUCT_AUDIT_LOG_TRIGGER)  # type: ignore


async def _drop_audit_log_triggers(session: AsyncSession) -> None:
    """
    Drop database triggers for AuditLog model.
    """
    await session.exec(DDL("DROP TRIGGER IF EXISTS account_audit_log ON account;"))  # type: ignore
    await session.exec(DDL("DROP TRIGGER IF EXISTS product_audit_log ON products;"))  # type: ignore


async def register_triggers() -> None:
    """
    Register all database triggers.
    """
    async with db_context_manager() as session:
        await _setup_product_item_triggers(session)
        await _setup_audit_log_triggers(session)

        await session.commit()


async def drop_triggers() -> None:
    """
    Drop all database triggers.
    """
    async with db_context_manager() as session:
        await _drop_product_item_triggers(session)
        await _drop_audit_log_triggers(session)

        await session.commit()
