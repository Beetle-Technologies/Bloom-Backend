import logging

from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import engine
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

max_tries = 60 * 5
wait_seconds = 1

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init_db_with_retry(db_engine: AsyncEngine) -> None:
    async with AsyncSession(db_engine) as session:
        try:
            (await session.exec(select(1))).all()
        except Exception as e:
            raise e


async def main() -> None:
    await init_db_with_retry(engine)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
