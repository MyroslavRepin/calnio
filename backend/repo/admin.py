from datetime import date, datetime, timedelta, timezone
from statistics import median

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.caldav_credential import CaldavCredential
from backend.models.notion_connection import NotionConnection
from backend.models.sync_mapping import SyncMapping
from backend.models.sync_run import SyncRun
from backend.models.sync_settings import STATUS_AUTH_ERROR, STATUS_ERROR, STATUS_OK, SyncSettings
from backend.models.synced_event import SyncedEvent
from backend.models.user import User
from backend.schemas.admin import (
    AdminActivation,
    AdminBucket,
    AdminCohort,
    AdminDay,
    AdminEventTotals,
    AdminFailure,
    AdminFunnelStep,
    AdminHealth,
    AdminIcloudGrant,
    AdminLogEntry,
    AdminNotionGrant,
    AdminOverview,
    AdminRun,
    AdminRunErrorGroup,
    AdminSyncDetail,
    AdminSyncRow,
    AdminSyncTotals,
    AdminTotals,
    AdminUserDetail,
    AdminUserRow,
)

# How far back the daily charts reach.
CHART_DAYS = 30

# How many signup weeks the cohort table shows.
COHORT_WEEKS = 8

# How many runs one list carries, and how many failure reasons.
RUN_LIMIT = 200
ERROR_GROUP_LIMIT = 10


def share(part: int, whole: int) -> int | None:
    """part as a whole percentage of whole, None when whole is zero."""
    if whole == 0:
        return None
    return round(part * 100 / whole)


class AdminRepo:
    """Read-only aggregates across every account.

    No token, no password and no page content is ever read here. Database and
    calendar names are, because a sync cannot be told apart without them.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def overview(self, problems: list[AdminLogEntry]) -> AdminOverview:
        """Every number the admin overview shows."""
        totals = self.totals()
        return AdminOverview(
            totals=totals,
            syncs=self.sync_totals(),
            events=self.event_totals(),
            health=self.health(problems),
            activation=self.activation(),
            funnel=self.funnel(totals),
            days=self.days(),
            cohorts=self.cohorts(),
            syncs_per_user=self.syncs_per_user(),
            run_errors=self.run_errors(),
            failures=self.failures(),
        )

    def count(self, statement) -> int:
        """Run a count statement, answering 0 rather than None."""
        return self.db.scalar(statement) or 0

    def runnable(self, statement: Select) -> Select:
        """Narrow a statement over sync_mappings to the syncs the next tick runs.

        The same conditions the scheduler filters on: switched on, both targets
        chosen, both grants stored.
        """
        return (
            statement.join(SyncSettings, SyncSettings.user_id == SyncMapping.user_id)
            .join(NotionConnection, NotionConnection.user_id == SyncMapping.user_id)
            .join(CaldavCredential, CaldavCredential.user_id == SyncMapping.user_id)
            .where(
                SyncSettings.enabled.is_(True),
                SyncMapping.enabled.is_(True),
                SyncMapping.due_date_property.is_not(None),
                SyncMapping.calendar_url.is_not(None),
            )
        )

    def user_ids_with_notion(self) -> set[int]:
        return set(self.db.scalars(select(NotionConnection.user_id)).all())

    def user_ids_with_icloud(self) -> set[int]:
        return set(self.db.scalars(select(CaldavCredential.user_id)).all())

    def user_ids_with_sync(self) -> set[int]:
        return set(self.db.scalars(select(SyncMapping.user_id).distinct()).all())

    def user_ids_syncing(self) -> set[int]:
        """Users whose next tick would actually do something."""
        statement = self.runnable(select(SyncMapping.user_id)).distinct()
        return set(self.db.scalars(statement).all())

    def totals(self) -> AdminTotals:
        """People, and how far each of them got."""
        now = datetime.now(timezone.utc)
        notion = self.user_ids_with_notion()
        icloud = self.user_ids_with_icloud()

        return AdminTotals(
            users=self.count(select(func.count()).select_from(User)),
            signed_up_7d=self.count(
                select(func.count())
                .select_from(User)
                .where(User.row_created_at >= now - timedelta(days=7))
            ),
            signed_up_30d=self.count(
                select(func.count())
                .select_from(User)
                .where(User.row_created_at >= now - timedelta(days=30))
            ),
            notion_connected=len(notion),
            icloud_connected=len(icloud),
            both_connected=len(notion & icloud),
            with_sync=len(self.user_ids_with_sync()),
            syncing=len(self.user_ids_syncing()),
            two_way=self.count(
                select(func.count(func.distinct(SyncMapping.user_id))).where(
                    SyncMapping.write_back.is_(True)
                )
            ),
        )

    def sync_totals(self) -> AdminSyncTotals:
        """The syncs themselves, and how their last run went."""

        def mappings_where(*conditions) -> int:
            return self.count(
                select(func.count()).select_from(SyncMapping).where(*conditions)
            )

        return AdminSyncTotals(
            mappings=self.count(select(func.count()).select_from(SyncMapping)),
            enabled=mappings_where(SyncMapping.enabled.is_(True)),
            eligible=mappings_where(
                SyncMapping.due_date_property.is_not(None),
                SyncMapping.calendar_url.is_not(None),
            ),
            two_way=mappings_where(SyncMapping.write_back.is_(True)),
            ok=mappings_where(SyncMapping.last_status == STATUS_OK),
            error=mappings_where(SyncMapping.last_status == STATUS_ERROR),
            auth_error=mappings_where(SyncMapping.last_status == STATUS_AUTH_ERROR),
            never_run=mappings_where(SyncMapping.last_run_at.is_(None)),
        )

    def event_totals(self) -> AdminEventTotals:
        """What the syncs have produced, and how many targets they touch."""
        return AdminEventTotals(
            linked_events=self.count(select(func.count()).select_from(SyncedEvent)),
            databases=self.count(
                select(func.count(func.distinct(SyncMapping.data_source_id)))
            ),
            calendars=self.count(
                select(func.count(func.distinct(SyncMapping.calendar_url)))
            ),
        )

    def health(self, problems: list[AdminLogEntry]) -> AdminHealth:
        """Run outcomes and run times lately, stuck syncs, and log problems."""
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)

        day = self.db.execute(
            select(
                func.count().label("runs"),
                func.count().filter(SyncRun.status != STATUS_OK).label("failed"),
                func.percentile_cont(0.5).within_group(SyncRun.duration_ms).label("median"),
                func.percentile_cont(0.95).within_group(SyncRun.duration_ms).label("p95"),
            )
            .select_from(SyncRun)
            .where(SyncRun.started_at >= day_ago)
        ).one()
        week = self.db.execute(
            select(
                func.count().label("runs"),
                func.count().filter(SyncRun.status != STATUS_OK).label("failed"),
            )
            .select_from(SyncRun)
            .where(SyncRun.started_at >= now - timedelta(days=7))
        ).one()

        # A sync the scheduler should run that has not run for three intervals
        # means the tick is stuck or skipping it. A new sync counts from when
        # it was made, so it is not stale before its first chance to run.
        interval = timedelta(minutes=int(settings.syncing_interval_minutes))
        stale = self.count(
            self.runnable(select(func.count()).select_from(SyncMapping)).where(
                func.coalesce(SyncMapping.last_run_at, SyncMapping.row_created_at)
                < now - 3 * interval
            )
        )
        failing = self.count(
            select(func.count())
            .select_from(SyncMapping)
            .where(SyncMapping.last_status.in_([STATUS_ERROR, STATUS_AUTH_ERROR]))
        )

        recent = [entry for entry in problems if entry.time >= day_ago]

        return AdminHealth(
            runs_24h=day.runs,
            failed_24h=day.failed,
            success_rate_24h=share(day.runs - day.failed, day.runs),
            success_rate_7d=share(week.runs - week.failed, week.runs),
            median_ms_24h=None if day.median is None else round(day.median),
            p95_ms_24h=None if day.p95 is None else round(day.p95),
            stale=stale,
            failing=failing,
            errors_24h=len([e for e in recent if e.level in ("ERROR", "CRITICAL")]),
            warnings_24h=len([e for e in recent if e.level == "WARNING"]),
        )

    def activation(self) -> AdminActivation:
        """Time from signing in to the first sync, and which grants can write."""
        joined = {
            row.id: row.row_created_at
            for row in self.db.execute(select(User.id, User.row_created_at))
        }
        first_sync = {
            row.user_id: row.first
            for row in self.db.execute(
                select(
                    SyncMapping.user_id,
                    func.min(SyncMapping.row_created_at).label("first"),
                ).group_by(SyncMapping.user_id)
            )
        }

        hours = [
            max(0.0, (first - joined[user_id]).total_seconds() / 3600)
            for user_id, first in first_sync.items()
            if user_id in joined
        ]

        def grants_where(can_write: bool) -> int:
            return self.count(
                select(func.count())
                .select_from(NotionConnection)
                .where(NotionConnection.can_write.is_(can_write))
            )

        return AdminActivation(
            median_hours_to_sync=round(median(hours), 1) if hours else None,
            within_1d=share(len([h for h in hours if h <= 24]), len(joined)) or 0,
            within_7d=share(len([h for h in hours if h <= 24 * 7]), len(joined)) or 0,
            notion_can_write=grants_where(True),
            notion_read_only=grants_where(False),
        )

    def funnel(self, totals: AdminTotals) -> list[AdminFunnelStep]:
        """Setup as a sequence, so the step that loses people is visible.

        Shares are of everybody who ever signed in, not of the previous step,
        because the question is how much of the top of the funnel survives.
        """
        synced_once = self.count(
            select(func.count()).select_from(SyncSettings).where(
                SyncSettings.last_status == STATUS_OK
            )
        )
        steps = [
            ("Signed in", totals.users),
            ("Connected Notion", totals.notion_connected),
            ("Connected iCloud", totals.icloud_connected),
            ("Created a sync", totals.with_sync),
            ("Syncing now", totals.syncing),
            ("Synced successfully", synced_once),
            ("Turned two-way on", totals.two_way),
        ]

        return [
            AdminFunnelStep(name=name, count=count, share=share(count, totals.users) or 0)
            for name, count in steps
        ]

    def per_day(self, column, start: datetime) -> dict[date, int]:
        """Rows per day of one timestamp column, from start onwards."""
        day = func.date(column)
        statement = (
            select(day.label("day"), func.count().label("total"))
            .where(column >= start)
            .group_by(day)
        )
        return {row.day: row.total for row in self.db.execute(statement)}

    def days(
        self, *, user_id: int | None = None, mapping_id: int | None = None
    ) -> list[AdminDay]:
        """The last CHART_DAYS days, for everybody or for one user or one sync.

        Signups and new syncs are counted only for everybody: one account has
        one signup, and its syncs are listed beside the chart anyway.
        """
        first_day = (datetime.now(timezone.utc) - timedelta(days=CHART_DAYS - 1)).date()
        start = datetime(first_day.year, first_day.month, first_day.day, tzinfo=timezone.utc)
        answer = {
            first_day + timedelta(days=offset): AdminDay(day=first_day + timedelta(days=offset))
            for offset in range(CHART_DAYS)
        }

        run_day = func.date(SyncRun.started_at)
        statement = (
            select(
                run_day.label("day"),
                func.count().filter(SyncRun.status == STATUS_OK).label("ok"),
                func.count().filter(SyncRun.status != STATUS_OK).label("failed"),
                func.sum(SyncRun.created).label("created"),
                func.sum(SyncRun.updated).label("updated"),
                func.sum(SyncRun.deleted).label("deleted"),
                func.sum(SyncRun.pulled).label("pulled"),
                func.sum(SyncRun.imported).label("imported"),
                func.sum(SyncRun.trashed).label("trashed"),
            )
            .where(SyncRun.started_at >= start)
            .group_by(run_day)
        )
        if user_id is not None:
            statement = statement.where(SyncRun.user_id == user_id)
        if mapping_id is not None:
            statement = statement.where(SyncRun.mapping_id == mapping_id)

        for row in self.db.execute(statement):
            day = answer.get(row.day)
            if day is None:
                continue
            day.runs_ok = row.ok
            day.runs_failed = row.failed
            day.created = row.created or 0
            day.updated = row.updated or 0
            day.deleted = row.deleted or 0
            day.pulled = row.pulled or 0
            day.imported = row.imported or 0
            day.trashed = row.trashed or 0

        if user_id is None and mapping_id is None:
            for when, count in self.per_day(User.row_created_at, start).items():
                if when in answer:
                    answer[when].signups = count
            for when, count in self.per_day(SyncMapping.row_created_at, start).items():
                if when in answer:
                    answer[when].syncs_created = count

        return list(answer.values())

    def cohorts(self) -> list[AdminCohort]:
        """Signup weeks, newest first, and how far each week's people got."""
        notion = self.user_ids_with_notion()
        icloud = self.user_ids_with_icloud()
        with_sync = self.user_ids_with_sync()
        syncing = self.user_ids_syncing()

        today = datetime.now(timezone.utc).date()
        this_monday = today - timedelta(days=today.weekday())
        weeks: dict[date, set[int]] = {
            this_monday - timedelta(weeks=offset): set() for offset in range(COHORT_WEEKS)
        }
        for row in self.db.execute(select(User.id, User.row_created_at)):
            joined = row.row_created_at.date()
            monday = joined - timedelta(days=joined.weekday())
            if monday in weeks:
                weeks[monday].add(row.id)

        return [
            AdminCohort(
                week=monday,
                users=len(ids),
                notion=len(ids & notion),
                icloud=len(ids & icloud),
                with_sync=len(ids & with_sync),
                syncing=len(ids & syncing),
            )
            for monday, ids in weeks.items()
        ]

    def syncs_per_user(self) -> list[AdminBucket]:
        """How many accounts have no sync, one, two, or more."""
        per_user = [
            row.total
            for row in self.db.execute(
                select(func.count().label("total"))
                .select_from(SyncMapping)
                .group_by(SyncMapping.user_id)
            )
        ]
        users = self.count(select(func.count()).select_from(User))
        return [
            AdminBucket(name="None", count=users - len(per_user)),
            AdminBucket(name="1", count=len([n for n in per_user if n == 1])),
            AdminBucket(name="2", count=len([n for n in per_user if n == 2])),
            AdminBucket(name="3 or more", count=len([n for n in per_user if n >= 3])),
        ]

    def run_errors(self, *conditions) -> list[AdminRunErrorGroup]:
        """The commonest failure reasons of the last 7 days, most frequent first."""
        reason = func.coalesce(SyncRun.error, "No reason recorded")
        statement = (
            select(
                reason.label("error"),
                func.count().label("runs"),
                func.count(func.distinct(SyncRun.mapping_id)).label("syncs"),
                func.max(SyncRun.started_at).label("last_seen"),
            )
            .where(
                SyncRun.status != STATUS_OK,
                SyncRun.started_at >= datetime.now(timezone.utc) - timedelta(days=7),
                *conditions,
            )
            .group_by(reason)
            .order_by(func.count().desc())
            .limit(ERROR_GROUP_LIMIT)
        )
        return [
            AdminRunErrorGroup(
                error=row.error, runs=row.runs, syncs=row.syncs, last_seen=row.last_seen
            )
            for row in self.db.execute(statement)
        ]

    def failures(self) -> list[AdminFailure]:
        """Every sync whose last run did not work, most recent first."""
        statement = (
            select(SyncMapping, User.email)
            .join(User, User.id == SyncMapping.user_id)
            .where(SyncMapping.last_status.in_([STATUS_ERROR, STATUS_AUTH_ERROR]))
            .order_by(SyncMapping.last_run_at.desc())
        )
        return [
            AdminFailure(
                mapping_id=mapping.id,
                user_id=mapping.user_id,
                email=email,
                database=mapping.data_source_name,
                status=mapping.last_status or STATUS_ERROR,
                error=mapping.last_error,
                run_id=mapping.last_run_id,
                last_run_at=mapping.last_run_at,
            )
            for mapping, email in self.db.execute(statement)
        ]

    def users(self, *conditions) -> list[AdminUserRow]:
        """One row per account, oldest first, narrowed by conditions on User.

        Each fact is counted once for everybody and matched up in Python, which
        costs a handful of queries rather than a handful per user.
        """
        notion = self.user_ids_with_notion()
        can_write = set(
            self.db.scalars(
                select(NotionConnection.user_id).where(NotionConnection.can_write.is_(True))
            ).all()
        )
        icloud = self.user_ids_with_icloud()
        syncing = self.user_ids_syncing()

        mappings: dict[int, list[SyncMapping]] = {}
        for mapping in self.db.scalars(select(SyncMapping)).all():
            mappings.setdefault(mapping.user_id, []).append(mapping)

        events = {
            row.user_id: row.total
            for row in self.db.execute(
                select(SyncedEvent.user_id, func.count().label("total")).group_by(
                    SyncedEvent.user_id
                )
            )
        }

        settings_rows = {
            row.user_id: row for row in self.db.scalars(select(SyncSettings)).all()
        }

        answer: list[AdminUserRow] = []
        for user in self.db.scalars(select(User).where(*conditions).order_by(User.id)).all():
            owned = mappings.get(user.id, [])
            row = settings_rows.get(user.id)
            answer.append(
                AdminUserRow(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    joined=user.row_created_at,
                    is_admin=user.is_admin,
                    notion=user.id in notion,
                    notion_can_write=user.id in can_write,
                    icloud=user.id in icloud,
                    syncing=user.id in syncing,
                    mappings=len(owned),
                    enabled_mappings=len([m for m in owned if m.enabled]),
                    two_way_mappings=len([m for m in owned if m.write_back]),
                    failing_mappings=len(
                        [
                            m
                            for m in owned
                            if m.last_status in (STATUS_ERROR, STATUS_AUTH_ERROR)
                        ]
                    ),
                    events=events.get(user.id, 0),
                    last_run_at=row.last_run_at if row else None,
                    last_status=row.last_status if row else None,
                )
            )
        return answer

    def syncs(self, *conditions) -> list[AdminSyncRow]:
        """One row per sync, oldest first, narrowed by conditions on SyncMapping."""
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        events = {
            row.mapping_id: row.total
            for row in self.db.execute(
                select(SyncedEvent.mapping_id, func.count().label("total")).group_by(
                    SyncedEvent.mapping_id
                )
            )
        }
        runs = {
            row.mapping_id: row
            for row in self.db.execute(
                select(
                    SyncRun.mapping_id,
                    func.count().label("runs"),
                    func.count().filter(SyncRun.status != STATUS_OK).label("failed"),
                )
                .where(SyncRun.started_at >= week_ago)
                .group_by(SyncRun.mapping_id)
            )
        }

        statement = (
            select(SyncMapping, User.email)
            .join(User, User.id == SyncMapping.user_id)
            .where(*conditions)
            .order_by(SyncMapping.id)
        )

        answer: list[AdminSyncRow] = []
        for mapping, email in self.db.execute(statement):
            run = runs.get(mapping.id)
            answer.append(
                AdminSyncRow(
                    id=mapping.id,
                    user_id=mapping.user_id,
                    email=email,
                    database=mapping.data_source_name,
                    data_source_id=mapping.data_source_id,
                    calendar=mapping.calendar_name,
                    date_property=mapping.due_date_property,
                    enabled=mapping.enabled,
                    two_way=mapping.write_back,
                    eligible=mapping.due_date_property is not None
                    and mapping.calendar_url is not None,
                    events=events.get(mapping.id, 0),
                    runs_7d=run.runs if run else 0,
                    failed_7d=run.failed if run else 0,
                    last_run_at=mapping.last_run_at,
                    last_status=mapping.last_status,
                    last_error=mapping.last_error,
                    last_run_id=mapping.last_run_id,
                    created_at=mapping.row_created_at,
                )
            )
        return answer

    def runs(
        self,
        *,
        status: str | None = None,
        user_id: int | None = None,
        mapping_id: int | None = None,
        run_id: str | None = None,
        limit: int = RUN_LIMIT,
    ) -> list[AdminRun]:
        """The newest runs, narrowed by any filter given.

        status "failed" means every status but ok, so both kinds of failure
        show in one list.
        """
        statement = (
            select(SyncRun, User.email, SyncMapping.data_source_name)
            .join(User, User.id == SyncRun.user_id)
            .outerjoin(SyncMapping, SyncMapping.id == SyncRun.mapping_id)
            .order_by(SyncRun.started_at.desc(), SyncRun.id.desc())
            .limit(limit)
        )
        if status == "failed":
            statement = statement.where(SyncRun.status != STATUS_OK)
        elif status:
            statement = statement.where(SyncRun.status == status)
        if user_id is not None:
            statement = statement.where(SyncRun.user_id == user_id)
        if mapping_id is not None:
            statement = statement.where(SyncRun.mapping_id == mapping_id)
        if run_id:
            statement = statement.where(SyncRun.run_id == run_id)

        return [
            AdminRun(
                id=run.id,
                run_id=run.run_id,
                user_id=run.user_id,
                email=email,
                mapping_id=run.mapping_id,
                database=database,
                status=run.status,
                error=run.error,
                started_at=run.started_at,
                duration_ms=run.duration_ms,
                created=run.created,
                updated=run.updated,
                deleted=run.deleted,
                pulled=run.pulled,
                imported=run.imported,
                trashed=run.trashed,
            )
            for run, email, database in self.db.execute(statement)
        ]

    def user_detail(self, user_id: int) -> AdminUserDetail | None:
        """One account with its grants, syncs and history, None when missing."""
        rows = self.users(User.id == user_id)
        if not rows:
            return None

        settings_row = self.db.scalar(
            select(SyncSettings).where(SyncSettings.user_id == user_id)
        )
        connection = self.db.scalar(
            select(NotionConnection).where(NotionConnection.user_id == user_id)
        )
        credential = self.db.scalar(
            select(CaldavCredential).where(CaldavCredential.user_id == user_id)
        )

        notion = None
        if connection is not None:
            notion = AdminNotionGrant(
                workspace_name=connection.workspace_name,
                workspace_id=connection.workspace_id,
                bot_id=connection.bot_id,
                can_write=connection.can_write,
                connected_at=connection.row_created_at,
                last_verified_at=connection.last_verified_at,
            )

        icloud = None
        if credential is not None:
            icloud = AdminIcloudGrant(
                connected_at=credential.row_created_at,
                last_verified_at=credential.last_verified_at,
            )

        return AdminUserDetail(
            user=rows[0],
            master_enabled=settings_row is not None and settings_row.enabled,
            notion=notion,
            icloud=icloud,
            syncs=self.syncs(SyncMapping.user_id == user_id),
            days=self.days(user_id=user_id),
            runs=self.runs(user_id=user_id, limit=50),
        )

    def sync_detail(self, mapping_id: int) -> AdminSyncDetail | None:
        """One sync with its history and failure reasons, None when missing."""
        rows = self.syncs(SyncMapping.id == mapping_id)
        mapping = self.db.get(SyncMapping, mapping_id)
        if not rows or mapping is None:
            return None

        # Other syncs of the same person writing into the same calendar, which
        # is the one setup where imports are switched off.
        shares_calendar = 0
        if mapping.calendar_url is not None:
            shares_calendar = self.count(
                select(func.count())
                .select_from(SyncMapping)
                .where(
                    SyncMapping.user_id == mapping.user_id,
                    SyncMapping.calendar_url == mapping.calendar_url,
                    SyncMapping.id != mapping.id,
                )
            )

        return AdminSyncDetail(
            sync=rows[0],
            write_back_since=mapping.write_back_since,
            has_sync_token=mapping.caldav_sync_token is not None,
            shares_calendar=shares_calendar,
            days=self.days(mapping_id=mapping_id),
            run_errors=self.run_errors(SyncRun.mapping_id == mapping_id),
            runs=self.runs(mapping_id=mapping_id, limit=100),
        )
