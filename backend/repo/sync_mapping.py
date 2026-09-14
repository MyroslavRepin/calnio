from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.sync_mapping import SyncMapping


class SyncMappingRepo:
    """Sync mapping persistence. Caller owns the session and the commit.

    Every read is scoped by user_id, so a mapping id belonging to somebody else
    reads as missing rather than as forbidden.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, user_id: int) -> list[SyncMapping]:
        rows = self.db.scalars(
            select(SyncMapping)
            .where(SyncMapping.user_id == user_id)
            .order_by(SyncMapping.id)
        ).all()
        return list(rows)

    def get(self, user_id: int, mapping_id: int) -> SyncMapping | None:
        return self.db.scalar(
            select(SyncMapping).where(
                SyncMapping.user_id == user_id, SyncMapping.id == mapping_id
            )
        )

    def get_by_source(self, user_id: int, data_source_id: str) -> SyncMapping | None:
        return self.db.scalar(
            select(SyncMapping).where(
                SyncMapping.user_id == user_id,
                SyncMapping.data_source_id == data_source_id,
            )
        )

    def eligible(self, user_id: int) -> list[SyncMapping]:
        """The user's mappings that have everything they need and are switched on."""
        rows = self.db.scalars(
            select(SyncMapping)
            .where(
                SyncMapping.user_id == user_id,
                SyncMapping.enabled.is_(True),
                SyncMapping.due_date_property.is_not(None),
                SyncMapping.calendar_url.is_not(None),
            )
            .order_by(SyncMapping.id)
        ).all()
        return list(rows)

    def create(
        self, user_id: int, data_source_id: str, data_source_name: str
    ) -> SyncMapping:
        """A new mapping with its database set and its targets still unpicked."""
        row = SyncMapping(
            user_id=user_id,
            data_source_id=data_source_id,
            data_source_name=data_source_name,
        )
        self.db.add(row)
        self.db.flush()  # assign id before the caller serializes the row
        return row

    def set_date_property(self, row: SyncMapping, name: str) -> None:
        row.due_date_property = name

    def set_calendar(
        self, row: SyncMapping, calendar_url: str, calendar_name: str
    ) -> None:
        row.calendar_url = calendar_url
        row.calendar_name = calendar_name

    def record_run(self, row: SyncMapping, status: str) -> None:
        row.last_run_at = datetime.now(timezone.utc)
        row.last_status = status

    def disable(self, row: SyncMapping) -> None:
        row.enabled = False

    def delete(self, row: SyncMapping) -> None:
        self.db.delete(row)
