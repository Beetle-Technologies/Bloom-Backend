import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28

DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

engine = create_async_engine(
    url=DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=0,
    json_serializer=lambda obj: json.dumps(obj),
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        try:
            await session.close()
        except Exception as e:
            logger.warning("Session unexpectedly closed", exc_info=e)


db_context_manager = asynccontextmanager(get_db_session)
