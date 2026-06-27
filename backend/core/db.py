from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.config import settings

async_engine: AsyncEngine = create_async_engine(settings.db_url, pool_pre_ping=True)

SessionLocal = async_sessionmaker(
    bind=async_engine, autoflush=False, expire_on_commit=False
)
