from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SyncedEvent(Base):
    """Link between a Notion page and its CalDAV event (sync state).

    Scoped to a user: the same Notion page can only ever be linked once per
    user, but two users syncing the same shared page are two independent
    links into two different calendars. That is why the uniqueness lives on
    (user_id, notion_page_id) rather than on the page id alone.
    """

    __tablename__: str = "synced_events"
    __table_args__ = (
        UniqueConstraint("user_id", "notion_page_id", name="uq_synced_events_user_page"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Owner of this link. Deleting the user drops their links; the CalDAV
    # events themselves stay in their calendar, same as a disconnect does.
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
