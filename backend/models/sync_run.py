from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SyncRun(Base):
    """One run of one sync, kept so the admin page can draw history.

    sync_mappings holds only the last run. This holds every run for
    RUN_HISTORY_DAYS, so success rate, run time and the work done can be
    charted per day. A row outlives its sync (mapping_id goes NULL), so
    deleting a sync does not rewrite the past. Deleting the user drops them.
    """

    __tablename__: str = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The pass id from the log, shared by every sync run in one pass over a
    # user, so grep "run=<id>" finds this row's lines.
    run_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    mapping_id: Mapped[int | None] = mapped_column(
        ForeignKey("sync_mappings.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(String)
    error: Mapped[str | None] = mapped_column(String, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_ms: Mapped[int] = mapped_column(Integer)

    # What the run did, the same six numbers as its "sync done" log line.
    created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pulled: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    imported: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    trashed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
