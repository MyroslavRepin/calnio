from datetime import datetime

from pydantic import BaseModel


class SyncStatus(BaseModel):
    """The master switch and how the last tick went across every sync."""

    enabled: bool
    # False while there is no sync ready to run, which the client renders as a
    # disabled toggle.
    eligible: bool
    # How many syncs the user has, so the client can say "nothing set up yet"
    # without fetching the list.
    mapping_count: int
    last_run_at: datetime | None
    last_status: str | None


class SyncCounts(BaseModel):
    """What one mapping's run did, in both directions, for its log line."""

    created: int = 0
    updated: int = 0
    deleted: int = 0
    # The other direction: pages Calnio wrote, made, or threw away.
    pulled: int = 0
    imported: int = 0
    trashed: int = 0
    # Events that failed on their own while the run went on, and the last reason.
    failed: int = 0
    failure: str | None = None
    # True when the run stopped at its write limit and left the rest for the next.
    deferred: bool = False


class UpdateSyncRequest(BaseModel):
    """Only the master switch. Each sync's own settings live on the mapping."""

    enabled: bool | None = None
