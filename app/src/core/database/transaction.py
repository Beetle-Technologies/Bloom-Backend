import logging
from contextvars import ContextVar
from typing import Self

from sqlalchemy.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

_transaction_level = ContextVar("transaction_level", default=0)


class Transaction:
    """
    Transaction context manager for database operations.

    This class is used to manage database transactions in a context manager style,
    ensuring that transactions are committed or rolled back automatically based on
    the success or failure of the operations performed within the context.

    Supports nested transactions - only the outermost transaction will actually commit.
    Inner transactions just manage their scope and participate in the outer transaction.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.token = None
        self.is_outermost = False

    async def __aenter__(self) -> Self:
        level = _transaction_level.get()
        self.is_outermost = level == 0
        self.token = _transaction_level.set(level + 1)

        if self.is_outermost:
            logger.debug("Starting outermost transaction")
        else:
            logger.debug(f"Starting nested transaction at level {level + 1}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        try:
            if exc_type is not None:
                logger.error(
                    f"Transaction failed: {exc_val}",
                    exc_info=(exc_type, exc_val, exc_tb),
                )
                if self.is_outermost:
                    logger.debug("Rolling back outermost transaction")
                    await self.session.rollback()
                return False

            if self.is_outermost:
                logger.debug("Committing outermost transaction")
                await self.session.commit()
        finally:
            if self.token is not None:
                _transaction_level.reset(self.token)

        return True


def in_transaction() -> bool:
    """Check if code is currently executing within a transaction context."""
    return _transaction_level.get() > 0
