from datetime import date, datetime

from pydantic import BaseModel


class AdminTotals(BaseModel):
    """How many people are here, and how far each of them got."""

    users: int
    signed_up_7d: int
    signed_up_30d: int
    notion_connected: int
    icloud_connected: int
    both_connected: int
    with_sync: int
    syncing: int
    two_way: int


class AdminSyncTotals(BaseModel):
    """The syncs themselves, and how their last run went."""

    mappings: int
    enabled: int
    eligible: int
    two_way: int
    ok: int
    error: int
    auth_error: int
    never_run: int


class AdminEventTotals(BaseModel):
    """What the syncs have actually produced."""

    linked_events: int
    databases: int
    calendars: int


class AdminFunnelStep(BaseModel):
    """One step of setup, and how many people are standing on it.

    The drop between two steps is the question worth answering: it says which
    step is losing people, which no single total can.
    """

    name: str
    count: int
    share: int


class AdminSignups(BaseModel):
    """Accounts created on one day."""

    day: date
    count: int


class AdminUserRow(BaseModel):
    """One account, and everything the dashboard says about it.

    Aggregates only. Nothing here reads a token, a password or a page title.
    """

    id: int
    email: str
    name: str | None
    joined: datetime
    is_admin: bool
    notion: bool
    icloud: bool
    syncing: bool
    mappings: int
    enabled_mappings: int
    two_way_mappings: int
    events: int
    last_run_at: datetime | None
    last_status: str | None


class AdminFailure(BaseModel):
    """A sync that is currently failing, and everything needed to chase it.

    run_id is the point of this: `grep "run=<id>"` over the log file gives that
    run's lines and its traceback.
    """

    mapping_id: int
    user_id: int
    email: str
    database: str | None
    status: str
    error: str | None
    run_id: str | None
    last_run_at: datetime | None


class AdminStats(BaseModel):
    """Everything the admin dashboard draws, in one answer."""

    totals: AdminTotals
    syncs: AdminSyncTotals
    events: AdminEventTotals
    funnel: list[AdminFunnelStep]
    signups: list[AdminSignups]
    failures: list[AdminFailure]
    users: list[AdminUserRow]
