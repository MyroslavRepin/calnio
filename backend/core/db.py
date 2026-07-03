from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings

async_engine: Engine = create_engine(settings.db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
