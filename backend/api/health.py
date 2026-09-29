from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.logging import logger
from backend.deps.db import get_session
from backend.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
async def get_health(response: Response, db: Session = Depends(get_session)):
    """Report whether the app can reach its database.

    Unauthenticated, because an uptime monitor has no cookie, and it answers
    only ok or down: a probe is not a place to describe the failure.
    """
    try:
        db.execute(text("select 1"))
    except Exception as exc:
        logger.opt(exception=exc).error("health check: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="down", database="down")

    return HealthResponse(status="ok", database="ok")
