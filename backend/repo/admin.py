from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.caldav_credential import CaldavCredential
from backend.models.notion_connection import NotionConnection
from backend.models.sync_mapping import SyncMapping
from backend.models.sync_settings import STATUS_AUTH_ERROR, STATUS_ERROR, STATUS_OK, SyncSettings
from backend.models.synced_event import SyncedEvent
from backend.models.user import User
from backend.schemas.admin import (
    AdminEventTotals,
    AdminFunnelStep,
    AdminSignups,
    AdminStats,
    AdminSyncTotals,
    AdminTotals,
    AdminUserRow,
)

# How far back the signup chart reaches.
SIGNUP_DAYS = 14


class AdminRepo:
    """Read-only aggregates across every account.

    Counts only. No token, no password and no page title is ever read here,
    because an admin looking at adoption has no business reading somebody's
    tasks.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def stats(self) -> AdminStats:
        """Every number the admin dashboard shows."""
        totals = self.totals()
        return AdminStats(
            totals=totals,
            syncs=self.sync_totals(),
            events=self.event_totals(),
            funnel=self.funnel(totals),
            signups=self.signups(),
            users=self.users(),
        )

    def count(self, statement) -> int:
        """Run a count statement, answering 0 rather than None."""
        return self.db.scalar(statement) or 0

    def user_ids_with_notion(self) -> set[int]:
        return set(self.db.scalars(select(NotionConnection.user_id)).all())

    def user_ids_with_icloud(self) -> set[int]:
        return set(self.db.scalars(select(CaldavCredential.user_id)).all())

    def user_ids_syncing(self) -> set[int]:
        """Users whose next tick would actually do something.

        The same conditions the scheduler filters on, so this number is the one
        that matters: switched on, both targets chosen, both grants stored.
        """
        statement = (
            select(SyncMapping.user_id)
            .join(SyncSettings, SyncSettings.user_id == SyncMapping.user_id)
            .join(NotionConnection, NotionConnection.user_id == SyncMapping.user_id)
            .join(CaldavCredential, CaldavCredential.user_id == SyncMapping.user_id)
            .where(
                SyncSettings.enabled.is_(True),
                SyncMapping.enabled.is_(True),
                SyncMapping.due_date_property.is_not(None),
                SyncMapping.calendar_url.is_not(None),
            )
            .distinct()
        )
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
            with_sync=self.count(
                select(func.count(func.distinct(SyncMapping.user_id)))
            ),
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

        answer: list[AdminFunnelStep] = []
        for name, count in steps:
            share = 0
            if totals.users > 0:
                share = round(count * 100 / totals.users)
            answer.append(AdminFunnelStep(name=name, count=count, share=share))
        return answer

    def signups(self) -> list[AdminSignups]:
        """Accounts per day, with the empty days filled in.

        A gap in a chart reads as missing data, so a day nobody joined is
        written down as a zero.
        """
        first_day = (datetime.now(timezone.utc) - timedelta(days=SIGNUP_DAYS - 1)).date()
        statement = (
            select(
                func.date(User.row_created_at).label("day"),
                func.count().label("count"),
            )
            .where(func.date(User.row_created_at) >= first_day)
            .group_by(func.date(User.row_created_at))
        )
        counted = {row.day: row.count for row in self.db.execute(statement)}

        return [
            AdminSignups(
                day=first_day + timedelta(days=offset),
                count=counted.get(first_day + timedelta(days=offset), 0),
            )
            for offset in range(SIGNUP_DAYS)
        ]

    def users(self) -> list[AdminUserRow]:
        """One row per account, oldest first.

        Each fact is counted once for everybody and then matched up in Python,
        which keeps this readable and costs a handful of queries rather than a
        handful per user.
        """
        notion = self.user_ids_with_notion()
        icloud = self.user_ids_with_icloud()
        syncing = self.user_ids_syncing()

        mappings: dict[int, list[SyncMapping]] = {}
        for mapping in self.db.scalars(select(SyncMapping)).all():
            mappings.setdefault(mapping.user_id, []).append(mapping)

        events = {
            row.user_id: row.count
            for row in self.db.execute(
                select(SyncedEvent.user_id, func.count().label("count")).group_by(
                    SyncedEvent.user_id
                )
            )
        }

        settings = {
            row.user_id: row
            for row in self.db.scalars(select(SyncSettings)).all()
        }

        answer: list[AdminUserRow] = []
        for user in self.db.scalars(select(User).order_by(User.id)).all():
            owned = mappings.get(user.id, [])
            row = settings.get(user.id)
            answer.append(
                AdminUserRow(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    joined=user.row_created_at,
                    is_admin=user.is_admin,
                    notion=user.id in notion,
                    icloud=user.id in icloud,
                    syncing=user.id in syncing,
                    mappings=len(owned),
                    enabled_mappings=len([m for m in owned if m.enabled]),
                    two_way_mappings=len([m for m in owned if m.write_back]),
                    events=events.get(user.id, 0),
                    last_run_at=row.last_run_at if row else None,
                    last_status=row.last_status if row else None,
                )
            )
        return answer
