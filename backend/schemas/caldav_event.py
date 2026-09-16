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

    # A repeating event and an invite have no shape a Notion page can hold, so
    # neither is ever imported. Facts about the event, not a decision: the
    # service decides what to do with them.
    recurring: bool = False
    has_attendees: bool = False


class CalDavChanges(BaseModel):
    """What a calendar did since a sync token.

    Events that were added or edited, hrefs that no longer resolve, and the
    token to send next time. A deleted event can be reported no other way: the
    resource is simply gone, and nothing about it carries a time of death.
    """

    events: list[CalDavEvent]
    deleted_hrefs: list[str]
    sync_token: str | None = None
