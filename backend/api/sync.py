from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.core.scheduler import scheduler
from backend.deps.db import get_session
from backend.deps.notion import date_property_names
from backend.deps.sync import get_sync_settings, is_eligible, sync_status
from backend.models.sync_settings import SyncSettings
from backend.repo.notion_connection import NotionConnectionRepo
from backend.schemas.sync import SyncStatus, UpdateSyncRequest
from backend.services.sync import sync_user

router = APIRouter(tags=["sync"])


def queue_run(user_id: int) -> None:
    """Sync this user once, now, on the scheduler thread.

    The request never waits: a run talks to Notion and iCloud and takes
    seconds. The job id keeps the queue idempotent, and APScheduler drops a
    one-off job once it has fired, so the guard only covers a run that has not
    started yet.
    """
    if not settings.scheduler_enabled:
        logger.warning(
            "sync not queued for user {}: SCHEDULER_ENABLED is false", user_id
        )
        return
    job_id = f"sync-user-{user_id}"
    if scheduler.get_job(job_id) is not None:
        return
    scheduler.add_job(
        sync_user,
        args=[user_id],
        id=job_id,
        next_run_time=datetime.now(),
    )


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
    """Set the switch, the due-date column, or both. Turning it on runs a sync."""
    if body.due_date_property is not None:
        connection = NotionConnectionRepo(db).get(row.user_id)
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="connect notion first",
            )
        # Checked against the live schema: a name that is not a date column
        # would sync cleanly and produce nothing at all.
        if body.due_date_property not in date_property_names(connection):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="that is not a date property on your database",
            )
        row.due_date_property = body.due_date_property

    turned_on = False
    if body.enabled is not None:
        if body.enabled and not is_eligible(db, row.user_id, row.due_date_property):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="finish your setup before turning syncing on",
            )
        turned_on = body.enabled and not row.enabled
        row.enabled = body.enabled

    db.commit()

    # After the commit: a queued job opens its own session and would otherwise
    # race the transaction that enabled the user.
    if turned_on:
        queue_run(row.user_id)

    return sync_status(db, row)
