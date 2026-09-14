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
from backend.models.sync_mapping import SyncMapping
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
from backend.repo.sync_mapping import SyncMappingRepo
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

    This is the one failure that is the user's problem rather than a single
    mapping's: the grant and the credential are shared by all of them.
    """
    if isinstance(exc, caldav_error.AuthorizationError):
        return True
    return isinstance(exc, APIResponseError) and exc.status in (401, 403)


def reconcile(
    db: Session,
    notion: NotionPageRepo,
    calendar: CalDavEventRepo,
    *,
    mapping: SyncMapping,
) -> tuple[int, int, int]:
    """Push one mapping's Notion pages into its calendar, returning the counts.

    Every query and every row here is scoped to mapping.id. Another mapping's
    links, another user's links, and any event Calnio never created are
    invisible to this loop. Scoping by user instead would make one mapping's
    delete pass wipe another mapping's events.
    """
    due_property = mapping.due_date_property
    calendar_url = mapping.calendar_url
    if due_property is None or calendar_url is None:
        raise RuntimeError(f"mapping {mapping.id} is not configured")

    pages = notion.query_database(mapping.data_source_id)
    created = updated = deleted = 0

    events: list[CalDavEvent] = []
    for page in pages:
        if page.archived:
            continue
        event = page_to_event(page, calendar_url, due_property)
        if event is not None:
            events.append(event)
    current_ids = {event.uid for event in events}

    rows = db.scalars(
        select(SyncedEvent).where(SyncedEvent.mapping_id == mapping.id)
    ).all()
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
                        mapping_id=mapping.id,
                        user_id=mapping.user_id,
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


def sync_mapping(
    db: Session,
    mapping: SyncMapping,
    notion: NotionPageRepo,
    credential: CaldavCredential,
) -> str:
    """Run one mapping and return the status it recorded.

    A rejected credential propagates out untouched: it kills every mapping this
    user has, so only sync_user can answer it. Anything else, a database that is
    no longer shared included, stays this mapping's problem and the caller moves
    on to the next one.
    """
    mapping_repo = SyncMappingRepo(db)

    try:
        # calendar_url was resolved and stored when the mapping was set up,
        # which skips iCloud's calendar-home discovery, the slowest call in the
        # flow. One repo per mapping, so one iCloud session per mapping.
        calendar = CalDavEventRepo(
            caldav_url=settings.caldav_url,
            username=credential.icloud_email,
            password=decrypt(credential.password_encrypted),
            calendar_url=mapping.calendar_url or "",
        )
        created, updated, deleted = reconcile(db, notion, calendar, mapping=mapping)
    except Exception as exc:
        db.rollback()
        if is_auth_failure(exc):
            mapping_repo.record_run(mapping, STATUS_AUTH_ERROR)
            raise
        mapping_repo.record_run(mapping, STATUS_ERROR)
        logger.error(
            "sync failed for mapping {} of user {}: {}",
            mapping.id,
            mapping.user_id,
            exc,
        )
        return STATUS_ERROR

    mapping_repo.record_run(mapping, STATUS_OK)
    logger.info(
        "sync done for mapping {}: {} created, {} updated, {} deleted",
        mapping.id,
        created,
        updated,
        deleted,
    )
    return STATUS_OK


def sync_user(user_id: int) -> None:
    """Run every one of a user's eligible mappings. Never raises.

    Opens its own session because it runs on the scheduler thread, both from
    the interval loop and as a one-off job when the user flips a switch on.
    """
    with SessionLocal() as db:
        settings_repo = SyncSettingsRepo(db)
        row = settings_repo.get(user_id)
        connection = NotionConnectionRepo(db).get(user_id)
        credential = CaldavCredentialRepo(db).get(user_id)

        # Re-checked here rather than trusted from the caller: a one-off job
        # fires against a user whose setup could have changed since.
        if row is None or connection is None or credential is None or not row.enabled:
            logger.warning("sync skipped for user {}: setup incomplete", user_id)
            return

        mappings = SyncMappingRepo(db).eligible(user_id)
        if not mappings:
            logger.warning("sync skipped for user {}: no configured syncs", user_id)
            return

        # One Notion repo for the whole user: the grant is theirs, not a
        # mapping's, and every mapping queries through the same token.
        notion = NotionPageRepo(decrypt(connection.access_token_encrypted))

        failed = False
        for mapping in mappings:
            try:
                status = sync_mapping(db, mapping, notion, credential)
            except Exception as exc:
                db.rollback()
                if is_auth_failure(exc):
                    settings_repo.disable(row)
                    settings_repo.record_run(row, STATUS_AUTH_ERROR)
                    SyncMappingRepo(db).record_run(mapping, STATUS_AUTH_ERROR)
                    db.commit()
                    logger.error(
                        "sync disabled for user {}: credentials rejected ({})",
                        user_id,
                        exc,
                    )
                    return
                failed = True
                logger.error(
                    "sync crashed for mapping {} of user {}: {}", mapping.id, user_id, exc
                )
                continue

            if status != STATUS_OK:
                failed = True

        # The user's own status summarises the tick, so the dashboard can say
        # "something failed" without the reader opening every mapping.
        if failed:
            settings_repo.record_run(row, STATUS_ERROR)
        else:
            settings_repo.record_run(row, STATUS_OK)
        db.commit()


def eligible_user_ids(db: Session) -> list[int]:
    """Users the scheduler may sync: switched on, set up, with a live mapping.

    Rooted in sync_mappings and distinct, so a user with five mappings is one
    unit of work. Everything is joined in rather than checked per user, so a
    tick costs one query and never opens an iCloud connection for a user who
    has nothing to sync into.
    """
    stmt = (
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


def reset_all() -> int:
    """Delete every CalDAV event and every synced_events row. Destructive.

    Dev only, and on the .env credentials rather than any user's stored ones.
    """
    calendar_url = CalDavAccountRepo(
        settings.caldav_url,
        settings.icloud_email,
        settings.app_specific_password,
    ).get_calendar_url(name="Calnio")
    calendar = CalDavEventRepo(
        caldav_url=settings.caldav_url,
        username=settings.icloud_email,
        password=settings.app_specific_password,
        calendar_url=calendar_url,
    )
    count = calendar.delete_all()
    with SessionLocal() as db:
        db.execute(delete(SyncedEvent))
        db.commit()
    logger.info("reset complete: {} caldav events and all link rows deleted", count)
    return count
