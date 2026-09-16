from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthorizeUrlResponse(BaseModel):
    authorize_url: str


class ConnectionStatus(BaseModel):
    """What the dashboard is allowed to see. Never carries the access token."""

    model_config = ConfigDict(from_attributes=True)

    connected: bool = True
    # False for a grant minted before Calnio asked Notion for write access. The
    # dashboard offers a reconnect instead of a two-way switch that cannot work.
    can_write: bool
    workspace_name: str | None
    workspace_icon: str | None
    last_verified_at: datetime | None


class NotionDatabaseOption(BaseModel):
    """One row in the database picker, without the column schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    url: str | None
