from datetime import datetime

from pydantic import BaseModel


class CalDavEvent(BaseModel):
    """A single calendar event."""

    uid: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False
    calendar: str
    href: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
