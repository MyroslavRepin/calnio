from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.base import Base

if TYPE_CHECKING:
    from backend.models.user import User


class SyncMapping(Base):
    """One Notion data source pushed into one Apple calendar.

    N rows per user, so a workspace's tasks, habits and reading lists each land
    in their own calendar and Apple's per-calendar colour and visibility
    toggles do the filtering.

    Both targets are nullable because a mapping is built in stages: the
    database is chosen first, then its date column and its calendar. A row with
    either missing is simply not eligible and never runs.

    Two mappings may share a calendar. The iCal uid is the Notion page id,
    which is unique across a workspace, so two data sources writing into one
    calendar cannot collide, and the reconcile loop is scoped by mapping_id so
    neither touches the other's events.
    """

    __tablename__: str = "sync_mappings"
    __table_args__ = (
        UniqueConstraint("user_id", "data_source_id", name="uq_sync_mappings_user_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # API 2025-09-03: pages and schema live on the data source, not the
    # database container, so this is the id data_sources.query takes.
    data_source_id: Mapped[str] = mapped_column(String)
    data_source_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # The Notion date column read for this data source. No default on purpose:
    # guessing "Due Date" would let a user turn syncing on, see a successful
    # run, and get no events.
    due_date_property: Mapped[str | None] = mapped_column(String, nullable=True)

    calendar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    calendar_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # This mapping's own switch, under the user's master switch in
    # sync_settings. Starts False: Calnio writes to a calendar only after
    # somebody asks for it.
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # How this mapping's last run went, separately from the user's tick, so a
    # single unshared database can be pointed at without blaming the others.
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String, nullable=True)

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="sync_mappings")
