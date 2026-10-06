from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.logging import logger
from backend.deps.auth import get_admin_user
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.admin import AdminRepo
from backend.repo.log import LogRepo
from backend.schemas.admin import (
    AdminOverview,
    AdminProblems,
    AdminRun,
    AdminSyncDetail,
    AdminSyncRow,
    AdminUserDetail,
    AdminUserRow,
)

router = APIRouter(tags=["admin"])


@router.get("/api/v1/admin/overview", response_model=AdminOverview)
async def get_admin_overview(
    user: User = Depends(get_admin_user), db: Session = Depends(get_session)
):
    """Every number the admin overview draws, in one answer."""
    return AdminRepo(db).overview(LogRepo().entries())


@router.get("/api/v1/admin/users", response_model=list[AdminUserRow])
async def list_admin_users(
    user: User = Depends(get_admin_user), db: Session = Depends(get_session)
):
    """Every account, oldest first."""
    return AdminRepo(db).users()


@router.get("/api/v1/admin/users/{user_id}", response_model=AdminUserDetail)
async def get_admin_user_detail(
    user_id: int,
    user: User = Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    """One account with its grants, syncs and recent runs."""
    detail = AdminRepo(db).user_detail(user_id)
    if detail is None:
        logger.warning("admin asked for missing user {}", user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such user")
    return detail


@router.get("/api/v1/admin/syncs", response_model=list[AdminSyncRow])
async def list_admin_syncs(
    user: User = Depends(get_admin_user), db: Session = Depends(get_session)
):
    """Every sync of every account, oldest first."""
    return AdminRepo(db).syncs()


@router.get("/api/v1/admin/syncs/{mapping_id}", response_model=AdminSyncDetail)
async def get_admin_sync_detail(
    mapping_id: int,
    user: User = Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    """One sync with its history and failure reasons."""
    detail = AdminRepo(db).sync_detail(mapping_id)
    if detail is None:
        logger.warning("admin asked for missing sync {}", mapping_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such sync")
    return detail


@router.get("/api/v1/admin/runs", response_model=list[AdminRun])
async def list_admin_runs(
    status: str | None = None,
    user_id: int | None = None,
    mapping_id: int | None = None,
    run_id: str | None = None,
    user: User = Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    """The newest sync runs, narrowed by any filter given."""
    return AdminRepo(db).runs(
        status=status, user_id=user_id, mapping_id=mapping_id, run_id=run_id
    )


@router.get("/api/v1/admin/problems", response_model=AdminProblems)
async def get_admin_problems(user: User = Depends(get_admin_user)):
    """The newest warnings and errors loguru wrote, from any part of the app."""
    return LogRepo().problems()
