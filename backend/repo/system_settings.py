from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.system_settings import SystemSettings


class SystemSettingsRepo:
    """The single row of instance-wide state. Caller owns the commit."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def sync_enabled(self) -> bool:
        """The global switch. A missing row means on."""
        # One column, not the row: the tick reads this, and a deploy whose
        # migration has not run yet must not stop every sync over a new column.
        enabled = self.db.scalar(
            select(SystemSettings.sync_enabled).order_by(SystemSettings.id)
        )
        if enabled is None:
            return True
        return enabled

    def get_or_create(self) -> SystemSettings:
        """The row, created with defaults on a fresh database."""
        row = self.db.scalar(select(SystemSettings).order_by(SystemSettings.id))
        if row is None:
            row = SystemSettings()
            self.db.add(row)
            self.db.flush()
        return row

    def mark_started(self) -> bool:
        """Flag this process as running. Returns whether the previous one stopped cleanly."""
        row = self.get_or_create()
        previous = row.stopped_cleanly
        row.stopped_cleanly = False
        return previous

    def mark_stopped(self) -> None:
        self.get_or_create().stopped_cleanly = True
