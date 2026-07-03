from datetime import datetime

from pydantic import BaseModel


class SyncedEvent(BaseModel):
    """Link between a Notion page and its CalDAV event (sync state)."""

    notion_page_id: str
    caldav_href: str
    caldav_uid: str
    etag: str | None = None
    notion_last_edited: datetime | None = None
