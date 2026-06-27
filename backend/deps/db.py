from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield an async session, always close it."""
    async with SessionLocal() as db:
        yield db
