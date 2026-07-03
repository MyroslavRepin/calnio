from backend.core.db import SessionLocal


def get_session():
    """FastAPI dependency: yield an async session, always close it."""
    with SessionLocal() as db:
        yield db
