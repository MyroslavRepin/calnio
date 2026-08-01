from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.sync_settings import SyncSettings


class SyncSettingsRepo:
    """Sync switch + settings persistence. Caller owns the session and commit."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> SyncSettings | None:
        return self.db.scalar(
            select(SyncSettings).where(SyncSettings.user_id == user_id)
        )

    def get_or_create(self, user_id: int) -> SyncSettings:
        """The user's row, created disabled if this is the first time.

        Every read path goes through here, so the dashboard can render a
        sensible "off, nothing picked" state without a special case for
        "no row yet".
        """
        row = self.get(user_id)
        if row is not None:
            return row
        row = SyncSettings(user_id=user_id)
        self.db.add(row)
        self.db.flush()  # assign id before the caller serializes the row
        return row

    def record_run(self, row: SyncSettings, status: str) -> None:
        row.last_run_at = datetime.now(timezone.utc)
        row.last_status = status

    def disable(self, row: SyncSettings) -> None:
        row.enabled = False
