from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.deps.db import get_session
from backend.deps.sync import (
    get_sync_settings,
    has_eligible_mapping,
    queue_run,
    sync_status,
)
from backend.models.sync_settings import SyncSettings
from backend.schemas.sync import SyncStatus, UpdateSyncRequest

router = APIRouter(tags=["sync"])


@router.get("/api/v1/me/sync", response_model=SyncStatus)
async def get_sync(
    row: SyncSettings = Depends(get_sync_settings),
    db: Session = Depends(get_session),
):
    """Also the poll target: the client watches last_run_at for a queued run."""
    return sync_status(db, row)


@router.put("/api/v1/me/sync", response_model=SyncStatus)
async def update_sync(
    body: UpdateSyncRequest,
    row: SyncSettings = Depends(get_sync_settings),
    db: Session = Depends(get_session),
):
    """Set the master switch. Turning it on runs every eligible sync once."""
    turned_on = False
    if body.enabled is not None:
        if body.enabled and not has_eligible_mapping(db, row.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="set up a sync before turning syncing on",
            )
        turned_on = body.enabled and not row.enabled
        row.enabled = body.enabled

    db.commit()

    # After the commit: a queued job opens its own session and would otherwise
    # race the transaction that enabled the user.
    if turned_on:
        queue_run(row.user_id)

    return sync_status(db, row)
