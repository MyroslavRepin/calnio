from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SyncedEvent(Base):
    """Link between a Notion page and its CalDAV event, plus what both agreed on.

    The content columns are the baseline of a three way merge: they hold the
    event as it stood the last time the two sides matched. Notion differing
    from the baseline means somebody edited Notion, the calendar differing from
    it means somebody edited the calendar, and both differing is the only real
    conflict. Comparing content rather than timestamps is also what keeps the
    two directions from echoing: Calnio writes the baseline with every push, so
    its own write is never read back as somebody's edit.

    Scoped to a mapping, not to a user. A user with several mappings has
    several independent sets of links, and the reconcile loop's delete pass
    treats "every row for this mapping" as "everything this data source
    accounts for". Scoping it by user instead would make one mapping's run
    delete another mapping's events.
    """

    __tablename__: str = "synced_events"
    __table_args__ = (
        UniqueConstraint(
            "mapping_id", "notion_page_id", name="uq_synced_events_mapping_page"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # The mapping that created this link. Deleting the mapping drops it.
    mapping_id: Mapped[int] = mapped_column(
        ForeignKey("sync_mappings.id", ondelete="CASCADE"), index=True
    )

    # Owner, carried alongside the mapping so per-user cleanup stays one query.
    # Deleting the user drops their links; the CalDAV events themselves stay in
    # their calendar, same as a disconnect does.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Mapping key: Notion page id, also the iCal uid.
    notion_page_id: Mapped[str] = mapped_column(String, index=True)

    # The agreed baseline. NULL start_at means this link predates two-way and
    # has no baseline yet, so the next run rebuilds it from Notion rather than
    # guessing that a calendar event was edited.
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    all_day: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # CalDAV locators. caldav_uid is the Notion page id for an event Calnio
    # created, and Apple's own uid for an event the user made in the calendar,
    # which is why the two are separate columns.
    caldav_href: Mapped[str] = mapped_column(String)
    caldav_uid: Mapped[str] = mapped_column(String)

    # DB-managed row write times.
    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
