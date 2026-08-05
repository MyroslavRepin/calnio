from datetime import datetime

from pydantic import BaseModel, Field


class SyncStatus(BaseModel):
    """The switch, its setting, and how the last run went."""

    enabled: bool
    # False while a connection is unfinished or no date column is picked, which
    # the client renders as a disabled toggle.
    eligible: bool
    due_date_property: str | None
    last_run_at: datetime | None
    last_status: str | None


class UpdateSyncRequest(BaseModel):
    """Both fields optional: the toggle and the picker PUT independently."""

    enabled: bool | None = None
    due_date_property: str | None = Field(default=None, min_length=1)
