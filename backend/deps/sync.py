from fastapi import Depends
from sqlalchemy.orm import Session

from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.sync_settings import SyncSettings
from backend.models.user import User
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.sync_settings import SyncSettingsRepo
from backend.schemas.sync import SyncStatus


def get_sync_settings(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
) -> SyncSettings:
    """The current user's sync row, created disabled on first look."""
    row = SyncSettingsRepo(db).get_or_create(user.id)
    db.commit()
    return row


def is_eligible(db: Session, user_id: int, due_date_property: str | None) -> bool:
    """Whether a run for this user could do anything.

    The same four conditions the scheduler's query filters on. The date column
    is passed in so a caller can ask about a value it is in the middle of
    setting.
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


def sync_status(db: Session, row: SyncSettings) -> SyncStatus:
    """The sync row plus the eligibility the client needs to render the toggle."""
    return SyncStatus(
        enabled=row.enabled,
        eligible=is_eligible(db, row.user_id, row.due_date_property),
        due_date_property=row.due_date_property,
        last_run_at=row.last_run_at,
        last_status=row.last_status,
    )
