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
    """One step of setup, and how many people are standing on it."""

    name: str
    count: int
    share: int


class AdminDay(BaseModel):
    """One day of activity. A quiet day is zeros, never a gap."""

    day: date
    signups: int = 0
    syncs_created: int = 0
    runs_ok: int = 0
    runs_failed: int = 0
    created: int = 0
    updated: int = 0
    deleted: int = 0
    pulled: int = 0
    imported: int = 0
    trashed: int = 0


class AdminHealth(BaseModel):
    """How the scheduler and the app have been doing lately."""

    runs_24h: int
    failed_24h: int
    # Percentages, None when there was no run to rate.
    success_rate_24h: int | None
    success_rate_7d: int | None
    median_ms_24h: int | None
    p95_ms_24h: int | None
    # Syncs that should be running but have not for three intervals.
    stale: int
    failing: int
    errors_24h: int
    warnings_24h: int


class AdminActivation(BaseModel):
    """How fast people get from signing in to a sync."""

    median_hours_to_sync: float | None
    # Percent of every account, not of the ones that made it.
    within_1d: int
    within_7d: int
    notion_can_write: int
    notion_read_only: int


class AdminCohort(BaseModel):
    """Everybody who signed up in one week, and how far they got."""

    week: date
    users: int
    notion: int
    icloud: int
    with_sync: int
    syncing: int


class AdminBucket(BaseModel):
    """One bar of a distribution."""

    name: str
    count: int


class AdminRunErrorGroup(BaseModel):
    """One failure reason, and how often syncs ran into it."""

    error: str
    runs: int
    syncs: int
    last_seen: datetime


class AdminFailure(BaseModel):
    """A sync that is currently failing, and everything needed to chase it."""

    mapping_id: int
    user_id: int
    email: str
    database: str | None
    status: str
    error: str | None
    run_id: str | None
    last_run_at: datetime | None


class AdminOverview(BaseModel):
    """Everything the admin overview draws, in one answer."""

    totals: AdminTotals
    syncs: AdminSyncTotals
    events: AdminEventTotals
    health: AdminHealth
    activation: AdminActivation
    funnel: list[AdminFunnelStep]
    days: list[AdminDay]
    cohorts: list[AdminCohort]
    syncs_per_user: list[AdminBucket]
    run_errors: list[AdminRunErrorGroup]
    failures: list[AdminFailure]


class AdminUserRow(BaseModel):
    """One account, and everything the dashboard says about it."""

    id: int
    email: str
    name: str | None
    joined: datetime
    is_admin: bool
    notion: bool
    notion_can_write: bool
    icloud: bool
    syncing: bool
    mappings: int
    enabled_mappings: int
    two_way_mappings: int
    failing_mappings: int
    events: int
    last_run_at: datetime | None
    last_status: str | None


class AdminSyncRow(BaseModel):
    """One sync, with its owner and how it has been running."""

    id: int
    user_id: int
    email: str
    database: str | None
    data_source_id: str
    calendar: str | None
    date_property: str | None
    enabled: bool
    two_way: bool
    eligible: bool
    events: int
    runs_7d: int
    failed_7d: int
    last_run_at: datetime | None
    last_status: str | None
    last_error: str | None
    last_run_id: str | None
    created_at: datetime


class AdminRun(BaseModel):
    """One run of one sync, from the history table."""

    id: int
    run_id: str | None
    user_id: int
    email: str
    mapping_id: int | None
    database: str | None
    status: str
    error: str | None
    started_at: datetime
    duration_ms: int
    created: int
    updated: int
    deleted: int
    pulled: int
    imported: int
    trashed: int


class AdminNotionGrant(BaseModel):
    """The user's Notion grant, minus the token."""

    workspace_name: str | None
    workspace_id: str
    bot_id: str
    can_write: bool
    connected_at: datetime
    last_verified_at: datetime | None


class AdminIcloudGrant(BaseModel):
    """The user's iCloud credential, minus the account and the password."""

    connected_at: datetime
    last_verified_at: datetime | None


class AdminUserDetail(BaseModel):
    """One account, its grants, its syncs and its recent runs."""

    user: AdminUserRow
    master_enabled: bool
    notion: AdminNotionGrant | None
    icloud: AdminIcloudGrant | None
    syncs: list[AdminSyncRow]
    days: list[AdminDay]
    runs: list[AdminRun]


class AdminSyncDetail(BaseModel):
    """One sync, its history and why it failed when it did."""

    sync: AdminSyncRow
    write_back_since: datetime | None
    has_sync_token: bool
    shares_calendar: int
    days: list[AdminDay]
    run_errors: list[AdminRunErrorGroup]
    runs: list[AdminRun]


class AdminLogEntry(BaseModel):
    """One warning or error from loguru's problems sink."""

    time: datetime
    level: str
    run_id: str | None
    user_id: int | None
    mapping_id: int | None
    location: str
    message: str
    error_type: str | None
    traceback: str | None


class AdminLogGroup(BaseModel):
    """Every entry written from one line of code, newest message kept."""

    level: str
    location: str
    error_type: str | None
    message: str
    count: int
    last_time: datetime


class AdminProblems(BaseModel):
    """The newest warnings and errors, one by one and grouped by origin."""

    entries: list[AdminLogEntry]
    groups: list[AdminLogGroup]
