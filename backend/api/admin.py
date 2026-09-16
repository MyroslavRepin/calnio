from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.deps.auth import get_admin_user
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.admin import AdminRepo
from backend.schemas.admin import AdminStats

router = APIRouter(tags=["admin"])


@router.get("/api/v1/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    user: User = Depends(get_admin_user), db: Session = Depends(get_session)
):
    """Every number the admin dashboard draws, in one answer.

    One endpoint rather than five, because the page shows all of it at once and
    the whole thing is a handful of counts.
    """
    return AdminRepo(db).stats()
