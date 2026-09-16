from datetime import datetime

from pydantic import BaseModel, Field


class MappingStatus(BaseModel):
    """One sync: its database, its targets, its switch and its last run.

    Built by hand rather than with model_validate, because `eligible` is not a
    column: it is the same condition the scheduler's query filters on.
    """

    id: int
    data_source_id: str
    data_source_name: str | None
    due_date_property: str | None
    calendar_url: str | None
    calendar_name: str | None
    enabled: bool
    write_back: bool
    eligible: bool
    last_run_at: datetime | None
    last_status: str | None


class CreateMappingRequest(BaseModel):
    """Several at once: ticking three databases is one action, not three."""

    data_source_ids: list[str] = Field(min_length=1)


class UpdateMappingRequest(BaseModel):
    """Every field optional: each picker and the switch PUT independently."""

    due_date_property: str | None = Field(default=None, min_length=1)
    calendar_url: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None
    write_back: bool | None = None
