from pydantic import BaseModel


class CalDavCalendar(BaseModel):
    """A calendar in the user's iCloud account (read-only projection)."""

    name: str
    url: str
