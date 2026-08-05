from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthorizeUrlResponse(BaseModel):
    authorize_url: str


class SelectDatabaseRequest(BaseModel):
    data_source_id: str = Field(min_length=1)


class ConnectionStatus(BaseModel):
    """What the dashboard is allowed to see. Never carries the access token."""

    model_config = ConfigDict(from_attributes=True)

    connected: bool = True
    workspace_name: str | None
    workspace_icon: str | None
    data_source_id: str | None
    data_source_name: str | None
    last_verified_at: datetime | None


class NotionDatabaseOption(BaseModel):
    """One row in the database picker, without the column schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    url: str | None
