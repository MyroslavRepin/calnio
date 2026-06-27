from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class CalDavEventORM(Base):
    """Persisted mirror of a CalDAV calendar event."""

    __tablename__ = "caldav_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    # iCal natural key — unique, indexed for upserts/lookups.
    uid: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Event data (mirrors pydantic CalDavEvent).
    title: Mapped[str] = mapped_column(String)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    all_day: Mapped[bool] = mapped_column(default=False)
    calendar: Mapped[str] = mapped_column(String)
    href: Mapped[str | None] = mapped_column(String, nullable=True)

    # Source timestamps from the iCal component (may be absent).
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # DB-managed row write times.
    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
