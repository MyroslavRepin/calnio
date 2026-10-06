from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.models.sync_mapping import SyncMapping
from backend.models.sync_run import SyncRun
from backend.schemas.sync import SyncCounts

# How long a run is kept: long enough for the admin charts, short enough that
# a tick every few minutes does not grow the table forever.
RUN_HISTORY_DAYS = 90


class SyncRunRepo:
    """Sync run history. Caller owns the session and the commit."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        mapping: SyncMapping,
        status: str,
        *,
        run_id: str,
        started_at: datetime,
        counts: SyncCounts | None = None,
        error: str | None = None,
    ) -> SyncRun:
        """Write one finished run down, timed from started_at to now."""
        if counts is None:
            counts = SyncCounts()
        elapsed = datetime.now(timezone.utc) - started_at
        row = SyncRun(
            run_id=run_id,
            user_id=mapping.user_id,
            mapping_id=mapping.id,
            status=status,
            error=error,
            started_at=started_at,
            duration_ms=round(elapsed.total_seconds() * 1000),
            created=counts.created,
            updated=counts.updated,
            deleted=counts.deleted,
            pulled=counts.pulled,
            imported=counts.imported,
            trashed=counts.trashed,
        )
        self.db.add(row)
        return row

    def prune(self) -> None:
        """Delete runs older than RUN_HISTORY_DAYS."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=RUN_HISTORY_DAYS)
        self.db.execute(delete(SyncRun).where(SyncRun.started_at < cutoff))
