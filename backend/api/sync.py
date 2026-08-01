from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.notion import date_property_names
from backend.core.config import settings
from backend.core.logging import logger
from backend.core.scheduler import scheduler
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.sync_settings import SyncSettings
from backend.models.user import User
from backend.repo.caldav_credential_repo import CaldavCredentialRepo
from backend.repo.notion_connection_repo import NotionConnectionRepo
from backend.repo.sync_settings_repo import SyncSettingsRepo
from backend.services.sync import sync_user

router = APIRouter(prefix="/api/v1", tags=["sync"])

BASE = "/me/sync"


class SyncStatus(BaseModel):
    """The switch, its setting, and how the last run went."""

    enabled: bool
    # False while either connection is unfinished or no date column is picked.
    # The client renders the toggle disabled rather than letting a user turn on
    # a sync that would immediately be skipped.
    eligible: bool
    due_date_property: str | None
    last_run_at: datetime | None
    last_status: str | None


class UpdateSyncRequest(BaseModel):
    """Both fields optional: the toggle and the picker PUT independently."""

    enabled: bool | None = None
    due_date_property: str | None = Field(default=None, min_length=1)


def get_settings(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
) -> SyncSettings:
    """The current user's sync row, created (disabled) on first look."""
    row = SyncSettingsRepo(db).get_or_create(user.id)
    db.commit()
    return row


def _eligible(db: Session, user_id: int, due_date_property: str | None) -> bool:
    """Whether a run for this user could do anything.

    Same four conditions the scheduler's query filters on, asked one user at a
    time. `due_date_property` is passed in rather than read from the row so the
    caller can ask about a value it is in the middle of setting.
    """
    if not due_date_property:
        return False
    connection = NotionConnectionRepo(db).get(user_id)
    credential = CaldavCredentialRepo(db).get(user_id)
    return (
        connection is not None
        and connection.data_source_id is not None
        and credential is not None
        and credential.calendar_url is not None
    )


def _status(db: Session, row: SyncSettings) -> SyncStatus:
    return SyncStatus(
        enabled=row.enabled,
        eligible=_eligible(db, row.user_id, row.due_date_property),
        due_date_property=row.due_date_property,
        last_run_at=row.last_run_at,
        last_status=row.last_status,
    )


def _queue_run(user_id: int) -> None:
    """Sync this user once, now, on the scheduler thread.

    The request never waits for it: a run talks to Notion and iCloud and takes
    seconds, which is a request that times out behind a proxy. The job id makes
    the queue idempotent — flipping the switch twice in a row does not stack two
    runs. APScheduler drops a one-off job once it has fired, so the guard only
    covers a run that has not started yet.
    """
    if not settings.scheduler_enabled:
        logger.warning(
            "sync not queued for user {}: SCHEDULER_ENABLED is false", user_id
        )
        return
    job_id = f"sync-user-{user_id}"
    if scheduler.get_job(job_id) is not None:
        logger.info("sync already queued for user {}", user_id)
        return
    scheduler.add_job(
        sync_user,
        args=[user_id],
        id=job_id,
        next_run_time=datetime.now(),
    )
    logger.info("sync queued for user {}", user_id)


@router.get(BASE, response_model=SyncStatus)
async def get_sync(
    row: SyncSettings = Depends(get_settings), db: Session = Depends(get_session)
):
    """Also the poll target: the client watches last_run_at for a queued run."""
    return _status(db, row)


@router.put(BASE, response_model=SyncStatus)
async def update_sync(
    body: UpdateSyncRequest,
    row: SyncSettings = Depends(get_settings),
    db: Session = Depends(get_session),
):
    """Set the switch, the due-date column, or both.

    Turning it on runs a sync straight away instead of leaving the user to
    wonder for up to an interval whether anything happened.
    """
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
        if body.enabled and not _eligible(db, row.user_id, row.due_date_property):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="finish your setup before turning syncing on",
            )
        turned_on = body.enabled and not row.enabled
        row.enabled = body.enabled

    db.commit()
    logger.info(
        "sync settings updated for user {} (enabled={})", row.user_id, row.enabled
    )

    # After the commit: a queued job opens its own session and would otherwise
    # race the transaction that enabled the user.
    if turned_on:
        _queue_run(row.user_id)

    return _status(db, row)
