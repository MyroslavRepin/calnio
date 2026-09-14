from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.core.scheduler import scheduler
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.sync_settings import SyncSettings
from backend.models.user import User
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.sync_mapping import SyncMappingRepo
from backend.repo.sync_settings import SyncSettingsRepo
from backend.schemas.sync import SyncStatus
from backend.services.sync import sync_user


def get_sync_settings(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
) -> SyncSettings:
    """The current user's sync row, created disabled on first look."""
    row = SyncSettingsRepo(db).get_or_create(user.id)
    db.commit()
    return row


def has_eligible_mapping(db: Session, user_id: int) -> bool:
    """Whether a run for this user could do anything.

    The same conditions the scheduler's query filters on: both grants stored,
    and at least one sync switched on with a date column and a calendar.
    """
    connection = NotionConnectionRepo(db).get(user_id)
    credential = CaldavCredentialRepo(db).get(user_id)
    if connection is None or credential is None:
        return False
    return len(SyncMappingRepo(db).eligible(user_id)) > 0


def sync_status(db: Session, row: SyncSettings) -> SyncStatus:
    """The sync row plus what the client needs to render the master toggle."""
    return SyncStatus(
        enabled=row.enabled,
        eligible=has_eligible_mapping(db, row.user_id),
        mapping_count=len(SyncMappingRepo(db).list(row.user_id)),
        last_run_at=row.last_run_at,
        last_status=row.last_status,
    )


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
