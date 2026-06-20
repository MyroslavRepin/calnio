from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    uid: str
    summary: str
    start: datetime
    end: datetime | None = None
    all_day: bool = False
    description: str | None = None
    created_at: datetime | None = None
    last_updated: datetime | None = None
