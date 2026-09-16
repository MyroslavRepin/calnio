from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotionDate(BaseModel):
    """A Notion date property value.

    all_day is Notion's "YYYY-MM-DD" shape, where the end date is the last day
    of the range and is included in it. iCalendar spells the same range with an
    exclusive DTEND, so the two conversions are not symmetric and live in one
    place, the parser.
    """

    start: datetime
    end: datetime | None = None
    all_day: bool = False
    # Set when the user picked a zone in Notion, in which case Notion sends the
    # timestamps without an offset. Writing the value back has to return it the
    # same way, or the page changes zone on every sync.
    time_zone: str | None = None


class NotionPageWrite(BaseModel):
    """The two columns Calnio ever writes: the title, and the sync's date column.

    Everything else on the page is left exactly as the user has it, including
    every column Calnio never asked about.
    """

    title_property: str
    title: str
    date_property: str
    date: NotionDate


class NotionPage(BaseModel):
    """Read-only projection of a Notion page."""

    id: str
    title: str
    parent_id: str | None = None
    parent_type: str
    properties: dict[str, Any]
    url: str | None = None
    archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
