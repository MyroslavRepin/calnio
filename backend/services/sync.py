from datetime import datetime, timedelta

import caldav.lib.error as caldav_error
from loguru import logger
from notion_client.errors import APIResponseError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt
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
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.caldav import CalDavEventRepo, get_calendar_url
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.notion import NotionPageRepo
from backend.repo.sync_settings import SyncSettingsRepo
from backend.schemas.caldav_event import CalDavEvent as CalDavEventScheme
from backend.schemas.notion_page import NotionPage

tasks_data_source_id = settings.tasks_data_source


def _page_to_event(
    page: NotionPage, calendar: str, due_property: str
) -> CalDavEventScheme | None:
    """Map a Notion task page to a CalDavEvent; None if it has no date.

    `due_property` is the user's chosen column name — Notion property keys are
    the column names, and no two workspaces have to agree on them.
    """
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

    return CalDavEventScheme(
        uid=page.id,
        title=page.title or "(untitled)",
        start=start,
        end=end,
        all_day=all_day,
        calendar=calendar,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


def _changed(event: CalDavEventScheme, row: SyncedEvent) -> bool:
    """True if the event differs from what we last synced.

    Compare title directly (Notion's last_edited_time is minute-rounded, so
    same-minute edits slip past a timestamp check); fall back to LWW for the
    rest (dates).
    """
    if event.title != row.title:
        return True
    if event.updated_at is None or row.notion_last_edited is None:
        return True  # missing timestamp -> re-push, safer than skipping
    return event.updated_at > row.notion_last_edited


def _is_auth_failure(exc: BaseException) -> bool:
    """True when the remote rejected our credentials, not our luck.

    The distinction decides whether the user keeps syncing. A network blip
    clears on its own and is worth retrying every interval; a revoked Notion
    grant or a wrong app-specific password never does, and re-sending that
    password to Apple every interval is how an Apple ID gets locked.
    """
    if isinstance(exc, caldav_error.AuthorizationError):
        return True
    return isinstance(exc, APIResponseError) and exc.status in (401, 403)


def _reconcile(
    db: Session,
    notion: NotionPageRepo,
    caldav: CalDavEventRepo,
    *,
    user_id: int,
    data_source_id: str,
    due_property: str,
    calendar_url: str,
) -> tuple[int, int, int]:
    """Push one user's Notion pages into their calendar. Returns the counts.

    Every query and every row here is scoped to `user_id`: rows Calnio owns
    for *this* user. Another user's links, and any event Calnio never
    created, are invisible to this loop and stay untouched.
    """
    pages = notion.query_database(data_source_id)
    logger.info("Sync started for user {}: {} Notion pages", user_id, len(pages))
    created = updated = deleted = 0

    events: list[CalDavEventScheme] = []
    for page in pages:
        if page.archived:
            continue
        event = _page_to_event(page, calendar_url, due_property)
        if event is not None:
            events.append(event)
    current_ids = {e.uid for e in events}

    stmt = select(SyncedEvent).where(SyncedEvent.user_id == user_id)
    rows = db.scalars(stmt).all()
    by_id = {row.notion_page_id: row for row in rows}

    # Commit per event so a failure mid-batch never orphans CalDAV events
    # (uncommitted rows -> next run re-creates -> iCloud 412 duplicate).
    for event in events:
        row = by_id.get(event.uid)

        if row is not None and not _changed(event, row):
            continue

        try:
            if row is None:
                new_event = caldav.create(event)
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
                logger.debug("Created {} ({})", event.uid, event.title)
            else:
                event.href = row.caldav_href
                new_event = caldav.update(event)
                row.caldav_href = new_event.href
                row.notion_last_edited = event.updated_at
                row.title = event.title
                updated += 1
                logger.debug("Updated {} ({})", event.uid, event.title)
            db.commit()
        except Exception as exc:
            db.rollback()
            if _is_auth_failure(exc):
                raise  # not this event's problem — the whole run is dead
            logger.error("Sync failed for {} ({}): {}", event.uid, event.title, exc)

    # Reconcile deletes: rows whose Notion page is gone / archived / lost its date.
    for row in rows:
        if row.notion_page_id in current_ids:
            continue
        try:
            caldav.delete_by_href(row.caldav_href)
            db.delete(row)
            db.commit()
            deleted += 1
            logger.debug("Deleted {}", row.notion_page_id)
        except Exception as exc:
            db.rollback()
            if _is_auth_failure(exc):
                raise
            logger.error("Delete failed for {}: {}", row.notion_page_id, exc)

    return created, updated, deleted


def sync_user(user_id: int) -> None:
    """Run one user's sync and record how it went. Never raises.

    Opens its own session because it runs on the scheduler thread, both from
    the interval loop and as a one-off job when the user flips the switch on.
    """
    with SessionLocal() as db:
        repo = SyncSettingsRepo(db)
        row = repo.get(user_id)
        connection = NotionConnectionRepo(db).get(user_id)
        credential = CaldavCredentialRepo(db).get(user_id)

        # Re-checked here rather than trusted from the caller: the one-off job
        # fires against a user whose setup could have changed since.
        if (
            row is None
            or connection is None
            or credential is None
            or not row.due_date_property
            or not connection.data_source_id
            or not credential.calendar_url
        ):
            logger.warning("Sync skipped for user {}: setup incomplete", user_id)
            return

        notion = NotionPageRepo(token=decrypt(connection.access_token_encrypted))
        # calendar_url was resolved and stored during setup, so this skips
        # get_calendar_url — iCloud's calendar-home discovery is the slowest
        # call in the whole flow.
        caldav = CalDavEventRepo(
            caldav_url=settings.caldav_url,
            username=credential.icloud_email,
            password=decrypt(credential.password_encrypted),
            calendar_url=credential.calendar_url,
        )

        try:
            notion.connect()
            caldav.connect()
            created, updated, deleted = _reconcile(
                db,
                notion,
                caldav,
                user_id=user_id,
                data_source_id=connection.data_source_id,
                due_property=row.due_date_property,
                calendar_url=credential.calendar_url,
            )
        except Exception as exc:
            db.rollback()
            if _is_auth_failure(exc):
                repo.disable(row)
                repo.record_run(row, STATUS_AUTH_ERROR)
                logger.error(
                    "Sync disabled for user {}: credentials rejected ({})",
                    user_id,
                    exc,
                )
            else:
                repo.record_run(row, STATUS_ERROR)
                logger.error("Sync failed for user {}: {}", user_id, exc)
            db.commit()
            return

        repo.record_run(row, STATUS_OK)
        db.commit()
        logger.info(
            "Sync done for user {}: {} created, {} updated, {} deleted",
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

    Sequential on purpose — the work is blocking CalDAV/Notion IO and the beta
    has few users. Each user is isolated: sync_user swallows its own failures,
    and the guard here covers anything that escapes it, so one broken account
    can never stop the tick.
    """
    with SessionLocal() as db:
        user_ids = eligible_user_ids(db)

    logger.info("Sync tick: {} eligible users", len(user_ids))
    for user_id in user_ids:
        try:
            sync_user(user_id)
        except Exception as exc:
            logger.error("Sync crashed for user {}: {}", user_id, exc)


# --- Single-user dev path (pre per-user sync) --------------------------------
# Kept, never scheduled. Runs on the .env credentials rather than a user's
# stored ones.


def _build_repos() -> tuple[NotionPageRepo, CalDavEventRepo, str]:
    """Connect Notion + CalDAV repos on the .env credentials."""
    calendar_url = get_calendar_url(
        settings.caldav_url,
        settings.icloud_email,
        settings.app_specific_password,
        name="Calnio",
    )
    notion = NotionPageRepo(token=settings.notion_token)
    caldav = CalDavEventRepo(
        caldav_url=settings.caldav_url,
        username=settings.icloud_email,
        password=settings.app_specific_password,
        calendar_url=calendar_url,
    )
    notion.connect()
    caldav.connect()
    return notion, caldav, calendar_url


def sync_notion_to_caldav() -> None:
    """The pre-per-user sync loop, on .env credentials. Kept for reference.

    Do not run it: `synced_events.user_id` is now required and this path has
    no user to attribute rows to, so every create fails on insert. `sync_user`
    replaced it. Left in the file as the single-user shape this grew out of —
    delete it once nothing refers back to it.
    """
    notion, caldav, calendar_url = _build_repos()

    pages = notion.query_database(tasks_data_source_id)
    logger.info("Sync started: {} Notion pages", len(pages))
    created = updated = deleted = 0

    events: list[CalDavEventScheme] = []
    for page in pages:
        if page.archived:
            continue
        event = _page_to_event(page, calendar_url, settings.event_due_date_field_name)
        if event is not None:
            events.append(event)
    current_ids = {e.uid for e in events}

    with SessionLocal() as db:
        rows = db.scalars(select(SyncedEvent)).all()
        by_id = {row.notion_page_id: row for row in rows}

        for event in events:
            row = by_id.get(event.uid)
            if row is not None and not _changed(event, row):
                continue
            try:
                if row is None:
                    new_event = caldav.create(event)
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
                    new_event = caldav.update(event)
                    row.caldav_href = new_event.href
                    row.notion_last_edited = event.updated_at
                    row.title = event.title
                    updated += 1
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Sync failed for {} ({}): {}", event.uid, event.title, exc)

        for row in rows:
            if row.notion_page_id in current_ids:
                continue
            try:
                caldav.delete_by_href(row.caldav_href)
                db.delete(row)
                db.commit()
                deleted += 1
            except Exception as exc:
                db.rollback()
                logger.error("Delete failed for {}: {}", row.notion_page_id, exc)

    logger.info(
        "Sync done: {} created, {} updated, {} deleted", created, updated, deleted
    )


def reset_all() -> int:
    """Wipe all sync state: delete every CalDAV event and every synced_events row.
    Returns the number of CalDAV events deleted.

    Still the .env path: it clears the calendar those credentials point at and
    the whole link table, for every user. Destructive — never call casually.
    """
    _, caldav, _ = _build_repos()
    count = caldav.delete_all()
    with SessionLocal() as db:
        db.execute(delete(SyncedEvent))
        db.commit()
    logger.info(
        "Reset complete: {} CalDAV events + all synced_events rows deleted", count
    )
    return count
