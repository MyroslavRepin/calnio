from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SyncedEvent(Base):
    """Link between a Notion page and its CalDAV event (sync state)."""

    __tablename__: str = "synced_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Mapping key — Notion page id, also the iCal uid.
    notion_page_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Last-synced title — compared to detect Notion title edits.
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
