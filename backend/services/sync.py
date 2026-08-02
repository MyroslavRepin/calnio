from datetime import datetime, timedelta

import caldav.lib.error as caldav_error
from notion_client.errors import APIResponseError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt
from backend.core.logging import logger
from backend.deps.db import SessionLocal
from backend.models.caldav_credential import CaldavCredential
from backend.models.notion_connection import NotionConnection
from backend.models.sync_settings import (
    STATUS_AUTH_ERROR,
    STATUS_ERROR,
    STATUS_OK,
    SyncSettings,
)
from backend.models.synced_event import SyncedEvent
from backend.repo.caldav import CalDavAccountRepo, CalDavEventRepo
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.notion import NotionPageRepo
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.sync_settings import SyncSettingsRepo
from backend.schemas.caldav_event import CalDavEvent
from backend.schemas.notion_page import NotionPage


def page_to_event(
    page: NotionPage, calendar: str, due_property: str
) -> CalDavEvent | None:
    """Map a Notion task page to an event, or None if it has no date."""
    # due_property is the user's chosen column name: Notion property keys are
    # the column names, and no two workspaces have to agree on them.
    due = page.properties.get(due_property, {}).get("date")
    if not due or not due.get("start"):
        return None

    start = datetime.fromisoformat(due["start"])
    all_day = len(due["start"]) == 10  # "YYYY-MM-DD" has no time component
    if due.get("end"):
        end = datetime.fromisoformat(due["end"])
    elif all_day:
        end = start + timedelta(days=1)  # iCal dtend is exclusive
    else:
        end = start + timedelta(hours=1)

    return CalDavEvent(
        uid=page.id,
        title=page.title or "(untitled)",
        start=start,
        end=end,
        all_day=all_day,
        calendar=calendar,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


def changed(event: CalDavEvent, row: SyncedEvent) -> bool:
    """True if the event differs from what was last synced."""
    # Title is compared directly because Notion's last_edited_time is
    # minute-rounded, so a same-minute edit slips past a timestamp check.
    if event.title != row.title:
        return True
    if event.updated_at is None or row.notion_last_edited is None:
        return True  # missing timestamp, re-push is safer than skipping
    return event.updated_at > row.notion_last_edited


def is_auth_failure(exc: BaseException) -> bool:
    """True when the remote rejected our credentials, not our luck.

    A network blip clears on its own and is worth retrying every interval. A
    revoked grant or a wrong app-specific password never does, and re-sending
    that password to Apple every interval is how an Apple ID gets locked.
    """
    if isinstance(exc, caldav_error.AuthorizationError):
        return True
    return isinstance(exc, APIResponseError) and exc.status in (401, 403)


def reconcile(
    db: Session,
    notion: NotionPageRepo,
    calendar: CalDavEventRepo,
    *,
    user_id: int,
    data_source_id: str,
    due_property: str,
    calendar_url: str,
) -> tuple[int, int, int]:
    """Push one user's Notion pages into their calendar, returning the counts.

    Every query and every row here is scoped to user_id. Another user's links,
    and any event Calnio never created, are invisible to this loop.
    """
    pages = notion.query_database(data_source_id)
    created = updated = deleted = 0

    events: list[CalDavEvent] = []
    for page in pages:
        if page.archived:
            continue
        event = page_to_event(page, calendar_url, due_property)
        if event is not None:
            events.append(event)
    current_ids = {event.uid for event in events}

    rows = db.scalars(select(SyncedEvent).where(SyncedEvent.user_id == user_id)).all()
    by_id = {row.notion_page_id: row for row in rows}

    # Commit per event so a failure mid-batch never orphans CalDAV events:
    # an uncommitted row means the next run re-creates it and iCloud 412s.
    for event in events:
        row = by_id.get(event.uid)

        if row is not None and not changed(event, row):
            continue

        try:
            if row is None:
                new_event = calendar.create(event)
                db.add(
                    SyncedEvent(
                        user_id=user_id,
                        notion_page_id=event.uid,
                        caldav_href=new_event.href,
                        caldav_uid=event.uid,
                        etag=None,
                        notion_last_edited=event.updated_at,
                        title=event.title,
                    )
                )
                created += 1
            else:
                event.href = row.caldav_href
                new_event = calendar.update(event)
                row.caldav_href = new_event.href
                row.notion_last_edited = event.updated_at
                row.title = event.title
                updated += 1
            db.commit()
        except Exception as exc:
            db.rollback()
            if is_auth_failure(exc):
                raise  # not this event's problem, the whole run is dead
            logger.error("sync failed for {} ({}): {}", event.uid, event.title, exc)

    # Rows whose Notion page is gone, archived, or lost its date.
    for row in rows:
        if row.notion_page_id in current_ids:
            continue
        try:
            calendar.delete_by_href(row.caldav_href)
            db.delete(row)
            db.commit()
            deleted += 1
        except Exception as exc:
            db.rollback()
            if is_auth_failure(exc):
                raise
            logger.error("delete failed for {}: {}", row.notion_page_id, exc)

    return created, updated, deleted


def sync_user(user_id: int) -> None:
    """Run one user's sync and record how it went. Never raises.

    Opens its own session because it runs on the scheduler thread, both from
    the interval loop and as a one-off job when the user flips the switch on.
    """
    with SessionLocal() as db:
        settings_repo = SyncSettingsRepo(db)
        row = settings_repo.get(user_id)
        connection = NotionConnectionRepo(db).get(user_id)
        credential = CaldavCredentialRepo(db).get(user_id)

        # Re-checked here rather than trusted from the caller: a one-off job
        # fires against a user whose setup could have changed since.
        if (
            row is None
            or connection is None
            or credential is None
            or not row.due_date_property
            or not connection.data_source_id
            or not credential.calendar_url
        ):
            logger.warning("sync skipped for user {}: setup incomplete", user_id)
            return

        try:
            notion = NotionPageRepo(decrypt(connection.access_token_encrypted))
            # calendar_url was resolved and stored during setup, which skips
            # iCloud's calendar-home discovery, the slowest call in the flow.
            calendar = CalDavEventRepo(
                caldav_url=settings.caldav_url,
                username=credential.icloud_email,
                password=decrypt(credential.password_encrypted),
                calendar_url=credential.calendar_url,
            )
            created, updated, deleted = reconcile(
                db,
                notion,
                calendar,
                user_id=user_id,
                data_source_id=connection.data_source_id,
                due_property=row.due_date_property,
                calendar_url=credential.calendar_url,
            )
        except Exception as exc:
            db.rollback()
            if is_auth_failure(exc):
                settings_repo.disable(row)
                settings_repo.record_run(row, STATUS_AUTH_ERROR)
                logger.error(
                    "sync disabled for user {}: credentials rejected ({})",
                    user_id,
                    exc,
                )
            else:
                settings_repo.record_run(row, STATUS_ERROR)
                logger.error("sync failed for user {}: {}", user_id, exc)
            db.commit()
            return

        settings_repo.record_run(row, STATUS_OK)
        db.commit()
        logger.info(
            "sync done for user {}: {} created, {} updated, {} deleted",
            user_id,
            created,
            updated,
            deleted,
        )


def eligible_user_ids(db: Session) -> list[int]:
    """Users the scheduler may sync: switched on and fully set up.

    Both halves of the setup are joined in rather than checked per user, so a
    tick costs one query and never opens an iCloud connection for a user who
    has nothing to sync into.
    """
    stmt = (
        select(SyncSettings.user_id)
        .join(NotionConnection, NotionConnection.user_id == SyncSettings.user_id)
        .join(CaldavCredential, CaldavCredential.user_id == SyncSettings.user_id)
        .where(
            SyncSettings.enabled.is_(True),
            SyncSettings.due_date_property.is_not(None),
            NotionConnection.data_source_id.is_not(None),
            CaldavCredential.calendar_url.is_not(None),
        )
    )
    return list(db.scalars(stmt).all())


def run_all_users() -> None:
    """The scheduled job: sync every eligible user, one after another.

    Sequential on purpose, since the work is blocking IO and the beta has few
    users. sync_user swallows its own failures and the guard here covers
    anything that escapes, so one broken account cannot stop the tick.
    """
    with SessionLocal() as db:
        user_ids = eligible_user_ids(db)

    logger.info("sync tick: {} eligible users", len(user_ids))
    for user_id in user_ids:
        try:
            sync_user(user_id)
        except Exception as exc:
            logger.error("sync crashed for user {}: {}", user_id, exc)


# Single-user dev path, from before per-user sync. Kept, never scheduled.
# Runs on the .env credentials rather than a user's stored ones.


def build_repos() -> tuple[NotionPageRepo, CalDavEventRepo, str]:
    """Build Notion and CalDAV repos on the .env credentials."""
    calendar_url = CalDavAccountRepo(
        settings.caldav_url,
        settings.icloud_email,
        settings.app_specific_password,
    ).get_calendar_url(name="Calnio")
    notion = NotionPageRepo(settings.notion_token)
    calendar = CalDavEventRepo(
        caldav_url=settings.caldav_url,
        username=settings.icloud_email,
        password=settings.app_specific_password,
        calendar_url=calendar_url,
    )
    return notion, calendar, calendar_url


def sync_notion_to_caldav() -> None:
    """The pre-per-user sync loop, on .env credentials. Kept for reference.

    Do not run it: synced_events.user_id is now required and this path has no
    user to attribute rows to, so every create fails on insert. sync_user
    replaced it. Delete this once nothing refers back to it.
    """
    notion, calendar, calendar_url = build_repos()

    pages = notion.query_database(settings.tasks_data_source)
    created = updated = deleted = 0

    events: list[CalDavEvent] = []
    for page in pages:
        if page.archived:
            continue
        event = page_to_event(page, calendar_url, settings.event_due_date_field_name)
        if event is not None:
            events.append(event)
    current_ids = {event.uid for event in events}

    with SessionLocal() as db:
        rows = db.scalars(select(SyncedEvent)).all()
        by_id = {row.notion_page_id: row for row in rows}

        for event in events:
            row = by_id.get(event.uid)
            if row is not None and not changed(event, row):
                continue
            try:
                if row is None:
                    new_event = calendar.create(event)
                    db.add(
                        SyncedEvent(
                            notion_page_id=event.uid,
                            caldav_href=new_event.href,
                            caldav_uid=event.uid,
                            etag=None,
                            notion_last_edited=event.updated_at,
                            title=event.title,
                        )
                    )
                    created += 1
                else:
                    event.href = row.caldav_href
                    new_event = calendar.update(event)
                    row.caldav_href = new_event.href
                    row.notion_last_edited = event.updated_at
                    row.title = event.title
                    updated += 1
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("sync failed for {} ({}): {}", event.uid, event.title, exc)

        for row in rows:
            if row.notion_page_id in current_ids:
                continue
            try:
                calendar.delete_by_href(row.caldav_href)
                db.delete(row)
                db.commit()
                deleted += 1
            except Exception as exc:
                db.rollback()
                logger.error("delete failed for {}: {}", row.notion_page_id, exc)

    logger.info(
        "sync done: {} created, {} updated, {} deleted", created, updated, deleted
    )


def reset_all() -> int:
    """Delete every CalDAV event and every synced_events row. Destructive."""
    _, calendar, _ = build_repos()
    count = calendar.delete_all()
    with SessionLocal() as db:
        db.execute(delete(SyncedEvent))
        db.commit()
    logger.info("reset complete: {} caldav events and all link rows deleted", count)
    return count
