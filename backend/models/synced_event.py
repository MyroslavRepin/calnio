from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SyncedEvent(Base):
    """Link between a Notion page and its CalDAV event (sync state).

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

    # Last-synced title, compared to detect Notion title edits.
    title: Mapped[str | None] = mapped_column(String, nullable=True)

    # CalDAV locators.
    caldav_href: Mapped[str] = mapped_column(String)
    caldav_uid: Mapped[str] = mapped_column(String)
    etag: Mapped[str | None] = mapped_column(String, nullable=True)

    # LWW change detection against Notion.
    notion_last_edited: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # DB-managed row write times.
    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
