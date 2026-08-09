from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.caldav_calendar import CalDavCalendar


class ConnectRequest(BaseModel):
    icloud_email: str
    app_specific_password: str = Field(min_length=1)


class CreateCalendarRequest(BaseModel):
    name: str = Field(default="Calnio", min_length=1, max_length=64)


class SelectCalendarRequest(BaseModel):
    calendar_url: str


class ConnectionStatus(BaseModel):
    """What the dashboard is allowed to see. Never carries the password."""

    model_config = ConfigDict(from_attributes=True)

    connected: bool = True
    icloud_email: str
    calendar_url: str | None
    calendar_name: str | None
    last_verified_at: datetime | None


class ConnectResponse(ConnectionStatus):
    """Status plus the account's calendars, so setup skips a slow round trip."""

    calendars: list[CalDavCalendar]
