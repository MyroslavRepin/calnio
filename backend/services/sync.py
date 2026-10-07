from datetime import datetime, timedelta, timezone
from uuid import uuid4

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
from backend.repo.caldav import CalDavAccountRepo, CalDavEventRepo, href_path
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.notion import NotionPageRepo, is_notion_outage
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.sync_mapping import SyncMappingRepo
from backend.repo.sync_run import SyncRunRepo
from backend.repo.telegram import notify
from backend.repo.sync_settings import SyncSettingsRepo
from backend.schemas.caldav_event import CalDavChanges, CalDavEvent
from backend.schemas.notion_page import NotionDate, NotionPage, NotionPageWrite
from backend.schemas.sync import SyncCounts


class NotionReadOnly(Exception):
    """The user's Notion grant may only read, so nothing can be written back.

    Notion fixes an integration's capabilities when the user consents, so this
    never clears by itself and retrying is pointless. The grant is marked and
    the user is asked to connect Calnio again.
    """


class RateLimited(Exception):
    """iCloud or Notion asked Calnio to slow down for this user."""


def event_from_page(
    page: NotionPage, date: NotionDate, *, uid: str, calendar: str
) -> CalDavEvent:
    """The calendar event a page's date column asks for."""
    if date.end is not None:
        end = date.end
        # Notion's last day is part of the range and iCalendar's is the day
        # after it, so an all day range gains a day on the way out and loses it
        # again on the way back.
        if date.all_day:
            end = end + timedelta(days=1)
    elif date.all_day:
        end = date.start + timedelta(days=1)
    else:
        end = date.start + timedelta(hours=1)

    return CalDavEvent(
        uid=uid,
        title=page.title or "(untitled)",
        start=date.start,
        end=end,
        all_day=date.all_day,
        calendar=calendar,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


def date_from_event(event: CalDavEvent, previous: NotionDate | None) -> NotionDate:
    """The Notion date an event's start and end ask for.

    Shaped like the value already on the page wherever the two agree, so a
    calendar edit changes the day and nothing else: a page that carried a
    single timestamp does not grow an end, and the zone it named is kept.
    """
    if event.all_day:
        last_day = event.end - timedelta(days=1)
        end = None
        if last_day.date() > event.start.date():
            end = last_day
        return NotionDate(start=event.start, end=end, all_day=True)

    end = event.end
    if end == event.start:
        end = None
    # An hour is what Calnio gives an event whose page holds a plain timestamp,
    # so an hour long event over such a page stays a plain timestamp.
    if (
        previous is not None
        and previous.end is None
        and end == event.start + timedelta(hours=1)
    ):
        end = None

    time_zone = None
    if previous is not None:
        time_zone = previous.time_zone
    return NotionDate(start=event.start, end=end, all_day=False, time_zone=time_zone)


def same_event(event: CalDavEvent, row: SyncedEvent) -> bool:
    """Whether an event is exactly the state this link last agreed on.

    A row with no baseline predates two-way sync and matches nothing, so the
    next run rewrites it from Notion rather than inventing a calendar edit.
    """
    if row.start_at is None or row.end_at is None:
        return False
    if event.title != (row.title or ""):
        return False
    if event.all_day != row.all_day:
        return False
    if event.all_day:
        # Both sides are read as UTC first. Postgres hands a timestamptz back in
        # the server's own zone, and a midnight UTC date read as 20:00 the day
        # before compares as a different day.
        return (
            event.start.astimezone(timezone.utc).date(),
            event.end.astimezone(timezone.utc).date(),
        ) == (
            row.start_at.astimezone(timezone.utc).date(),
            row.end_at.astimezone(timezone.utc).date(),
        )
    return (event.start, event.end) == (row.start_at, row.end_at)


def remember(row: SyncedEvent, event: CalDavEvent) -> None:
    """Record an event as the state both sides now agree on."""
    row.title = event.title
    row.start_at = event.start
    row.end_at = event.end
    row.all_day = event.all_day
    if event.href is not None:
        row.caldav_href = event.href


def create_event(calendar: CalDavEventRepo, event: CalDavEvent) -> CalDavEvent:
    """Create the event, taking a fresh uid if the server refuses the old one.

    iCloud remembers a uid long after its event is gone, the whole calendar
    included, and answers 404 to any PUT that reuses it. The link row keeps the
    uid apart from the page id for exactly this: the page stays, the uid moves.
    """
    event.href = None
    try:
        return calendar.create(event)
    except caldav_error.PutError:
        logger.warning("icloud refused uid {}, creating it under a new one", event.uid)
        event.uid = str(uuid4())
        return calendar.create(event)


def link_row(mapping: SyncMapping, page_id: str, event: CalDavEvent) -> SyncedEvent:
    """A fresh link between a page and an event, holding their agreed state."""
    row = SyncedEvent(
        mapping_id=mapping.id,
        user_id=mapping.user_id,
        notion_page_id=page_id,
        caldav_href=event.href or "",
        caldav_uid=event.uid,
    )
    remember(row, event)
    return row


def notion_wins(page: NotionPage, event: CalDavEvent) -> bool:
    """Which side keeps its edit when both changed since the last run.

    Last write wins, and every tie goes to Notion. Notion rounds
    last_edited_time down to the minute, so two edits inside one minute cannot
    be ordered at all, and Notion is the side that holds the task.
    """
    if page.updated_at is None or event.updated_at is None:
        return True
    return page.updated_at >= event.updated_at.replace(second=0, microsecond=0)


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
    if not isinstance(exc, APIResponseError):
        return False
    # A grant that may only read is a different problem with the same status:
    # reading still works, so the user keeps their one-way sync.
    if is_read_only_grant(exc):
        return False
    return exc.status in (401, 403)


def is_read_only_grant(exc: BaseException) -> bool:
    """True when Notion refused a write because the grant may only read."""
    return isinstance(exc, APIResponseError) and exc.code == "restricted_resource"


def is_rate_limited(exc: BaseException) -> bool:
    """True when iCloud or Notion asked Calnio to slow down."""
    if isinstance(exc, caldav_error.RateLimitError):
        return True
    return isinstance(exc, APIResponseError) and exc.code == "rate_limited"


def reached_write_limit(counts: SyncCounts) -> bool:
    """Whether this run has made the 100 calendar writes one run may make."""
    return counts.created + counts.updated + counts.deleted >= 100


def reason(exc: BaseException) -> str:
    """One line a person can act on, short enough for a card.

    The class name carries as much as the text half the time (NotFoundError,
    AuthorizationError), so both go in, and the whole thing is cut to something
    a card can hold. A failure that clears by itself says so in plain words
    instead, since the person has nothing to act on.
    """
    if isinstance(exc, caldav_error.RateLimitError):
        return "iCloud is limiting requests from Calnio. It tries again on the next run."
    if is_rate_limited(exc):
        return "Notion is limiting requests from Calnio. It tries again on the next run."
    if is_notion_outage(exc):
        return "Notion did not answer in time. Calnio tries again on the next run."
    text = f"{type(exc).__name__}: {exc}".strip()
    text = " ".join(text.split())
    if len(text) > 300:
        return text[:297] + "..."
    return text


def rows_for(db: Session, mapping_id: int) -> list[SyncedEvent]:
    """This mapping's link rows, the only events a run may touch."""
    rows = db.scalars(
        select(SyncedEvent).where(SyncedEvent.mapping_id == mapping_id)
    ).all()
    return list(rows)


def may_import(db: Session, mapping: SyncMapping) -> bool:
    """Whether an unknown event in this calendar may become a Notion page.

    Only when the calendar belongs to this sync alone. Two syncs sharing one
    calendar cannot tell which database a hand made event belongs in, and
    guessing would file half of them in the wrong one.
    """
    if mapping.write_back_since is None or mapping.calendar_url is None:
        return False
    return (
        SyncMappingRepo(db).count_on_calendar(mapping.user_id, mapping.calendar_url) == 1
    )


def merge_pages(
    db: Session,
    notion: NotionPageRepo,
    calendar: CalDavEventRepo,
    *,
    mapping: SyncMapping,
    live: dict[str, tuple[NotionPage, NotionDate]],
    changes: CalDavChanges,
    title_property: str | None,
) -> SyncCounts:
    """Bring every live page and its event back together, whichever side moved.

    The link row holds what the two last agreed on, so a page differing from it
    means Notion was edited and an event differing from it means the calendar
    was. Only both at once is a conflict, and that is the one place a timestamp
    decides anything.

    Commits per event on purpose: a failure mid-batch must never leave a
    CalDAV event without its row, because the next run would create it again
    and iCloud answers 412 to a duplicate.
    """
    counts = SyncCounts()
    # Keyed by path, never by the whole href: the same event is named one way in
    # a stored row and another in the server's own listing.
    events_by_path = {
        href_path(event.href): event
        for event in changes.events
        if event.href is not None
    }
    gone = {href_path(href) for href in changes.deleted_hrefs}
    rows_by_page = {row.notion_page_id: row for row in rows_for(db, mapping.id)}

    for page, date in live.values():
        # A first sync of a big database would otherwise send hundreds of
        # events in one burst, which is how iCloud gets talked into a limit.
        if reached_write_limit(counts):
            counts.deferred = True
            break
        row = rows_by_page.get(page.id)

        # An event the user made in Apple Calendar keeps the uid Apple gave it.
        uid = page.id
        if row is not None:
            uid = row.caldav_uid
        wanted = event_from_page(page, date, uid=uid, calendar=mapping.calendar_url or "")

        try:
            if row is None:
                db.add(link_row(mapping, page.id, create_event(calendar, wanted)))
                counts.created += 1
                db.commit()
                continue

            event = events_by_path.get(href_path(row.caldav_href))
            # The server's own href when it just named one, since a stored href
            # can be stale. remember() writes the working one back to the row.
            if event is not None and event.href is not None:
                wanted.href = event.href
            else:
                wanted.href = row.caldav_href
            notion_edited = not same_event(wanted, row)
            # A row with no baseline cannot say the calendar moved, only that
            # nothing is known yet, so Notion rebuilds it instead.
            calendar_edited = (
                event is not None
                and row.start_at is not None
                and not same_event(event, row)
            )

            if href_path(row.caldav_href) in gone:
                # A delete carries no time of death, so it cannot be weighed
                # against a Notion edit. A page that was edited is a page
                # somebody still wants, and its event comes back.
                if notion_edited:
                    remember(row, create_event(calendar, wanted))
                    counts.created += 1
                else:
                    notion.trash_page(page.id)
                    db.delete(row)
                    counts.trashed += 1
                db.commit()
                continue

            if (
                calendar_edited
                and event is not None
                and title_property is not None
                and not (notion_edited and notion_wins(page, event))
            ):
                notion.update_page(
                    page.id,
                    NotionPageWrite(
                        title_property=title_property,
                        title=event.title,
                        date_property=mapping.due_date_property or "",
                        date=date_from_event(event, date),
                    ),
                )
                remember(row, event)
                counts.pulled += 1
                db.commit()
                continue

            if notion_edited:
                try:
                    remember(row, calendar.update(wanted))
                    counts.updated += 1
                except caldav_error.NotFoundError:
                    # The event is no longer where the row says it is, and the
                    # page is still live, so it goes back into the calendar.
                    remember(row, create_event(calendar, wanted))
                    counts.created += 1
                db.commit()

        except Exception as exc:
            db.rollback()
            if is_auth_failure(exc) or is_rate_limited(exc):
                raise  # not this event's problem, the whole run is dead
            if is_read_only_grant(exc):
                raise NotionReadOnly(str(exc)) from exc
            logger.opt(exception=exc).error(
                "sync failed for page {} ({}) at {}: {}",
                page.id,
                page.title,
                row.caldav_href if row is not None else "no event yet",
                exc,
            )
            counts.failed += 1
            counts.failure = reason(exc)

    return counts


def drop_pages(
    db: Session,
    calendar: CalDavEventRepo,
    *,
    mapping: SyncMapping,
    live: dict[str, tuple[NotionPage, NotionDate]],
    counts: SyncCounts,
) -> None:
    """Delete the events of pages that are gone, archived, or lost their date."""
    for row in rows_for(db, mapping.id):
        if reached_write_limit(counts):
            counts.deferred = True
            break
        if row.notion_page_id in live:
            continue
        try:
            try:
                calendar.delete_by_href(row.caldav_href)
            except caldav_error.NotFoundError:
                # Deleted in the calendar too, so the row is the only leftover.
                pass
            db.delete(row)
            db.commit()
            counts.deleted += 1
        except Exception as exc:
            db.rollback()
            if is_auth_failure(exc) or is_rate_limited(exc):
                raise
            logger.opt(exception=exc).error(
                "delete failed for page {} at {}: {}",
                row.notion_page_id,
                row.caldav_href,
                exc,
            )
            counts.failed += 1
            counts.failure = reason(exc)


def import_events(
    db: Session,
    notion: NotionPageRepo,
    *,
    mapping: SyncMapping,
    changes: CalDavChanges,
    title_property: str,
) -> int:
    """Make a Notion page out of every event the user added to the calendar."""
    imported = 0
    known = {href_path(row.caldav_href) for row in rows_for(db, mapping.id)}

    for event in changes.events:
        if event.href is None or href_path(event.href) in known:
            continue
        # A repeating event has no single date and an invite belongs to whoever
        # sent it, so neither has a shape a Notion page could hold.
        if event.recurring or event.has_attendees:
            continue
        # Older than the switch, so it is part of whatever the calendar already
        # held rather than something written for Calnio to pick up.
        if (
            event.created_at is None
            or mapping.write_back_since is None
            or event.created_at < mapping.write_back_since
        ):
            continue

        try:
            page = notion.create_page(
                mapping.data_source_id,
                NotionPageWrite(
                    title_property=title_property,
                    title=event.title,
                    date_property=mapping.due_date_property or "",
                    date=date_from_event(event, None),
                ),
            )
            db.add(link_row(mapping, page.id, event))
            db.commit()
            imported += 1
        except Exception as exc:
            db.rollback()
            if is_auth_failure(exc) or is_rate_limited(exc):
                raise
            if is_read_only_grant(exc):
                raise NotionReadOnly(str(exc)) from exc
            logger.opt(exception=exc).error(
                "import failed for event {} ({}) at {}: {}",
                event.uid,
                event.title,
                event.href,
                exc,
            )

    return imported


def reconcile(
    db: Session,
    notion: NotionPageRepo,
    calendar: CalDavEventRepo,
    *,
    mapping: SyncMapping,
    write_back: bool,
) -> SyncCounts:
    """Run one mapping, one way or both ways, and report what it did.

    Every query and every row here is scoped to mapping.id. Another mapping's
    links, another user's links, and any event Calnio never created are
    invisible to this loop. Scoping by user instead would make one mapping's
    delete pass wipe another mapping's events.
    """
    due_property = mapping.due_date_property
    if due_property is None or mapping.calendar_url is None:
        raise RuntimeError(f"mapping {mapping.id} is not configured")

    parser = notion.parser
    # Read per run: a renamed or retyped date column would otherwise read as
    # every page losing its date, and the drop pass would delete every event.
    database = notion.get_database(mapping.data_source_id)
    date_column = database.properties.get(due_property)
    if date_column is None or date_column.get("type") != "date":
        raise RuntimeError(
            f"The date column {due_property!r} is no longer in this database"
        )

    live: dict[str, tuple[NotionPage, NotionDate]] = {}
    for page in notion.query_database(
        mapping.data_source_id,
        # Pages without a date never reach the calendar, so Notion keeps them.
        filter={"property": due_property, "date": {"is_not_empty": True}},
        # Every title column has the id "title". The fewer columns, the faster
        # Notion answers, rollups and formulas above all.
        property_ids=["title", date_column["id"]],
    ):
        if page.archived:
            continue
        # A page short of either column would read as untitled or dateless and
        # rename or delete its event, so a short answer stops the run instead.
        if due_property not in page.properties or parser.find_title_property(
            page.properties
        ) is None:
            raise RuntimeError("Notion answered without the title or the date column")
        date = parser.parse_date(page.properties, due_property)
        if date is not None:
            live[page.id] = (page, date)

    changes = CalDavChanges(events=[], deleted_hrefs=[])
    title_property = None
    if write_back:
        # A renamed title column would otherwise be written to under its old
        # name and answer 400 on every page.
        title_property = parser.find_title_property(database.properties)
        changes = calendar.changes(
            mapping.caldav_sync_token,
            {row.caldav_href for row in rows_for(db, mapping.id)},
        )

    counts = merge_pages(
        db,
        notion,
        calendar,
        mapping=mapping,
        live=live,
        changes=changes,
        title_property=title_property,
    )
    drop_pages(db, calendar, mapping=mapping, live=live, counts=counts)
    if counts.deferred:
        logger.info("write limit reached, the rest goes on the next run")

    if title_property is not None and may_import(db, mapping):
        counts.imported = import_events(
            db,
            notion,
            mapping=mapping,
            changes=changes,
            title_property=title_property,
        )

    if write_back and not counts.deferred:
        # Deliberately the token from before this run's own writes. The next
        # run sees them again, finds them equal to the baseline and does
        # nothing, which costs a read. Missing a change would cost correctness.
        # A run cut short by the write limit keeps the old token, so the
        # calendar changes it never reached come round again.
        mapping.caldav_sync_token = changes.sync_token
        db.commit()

    return counts


def record(
    db: Session,
    mapping: SyncMapping,
    status: str,
    *,
    run_id: str,
    started_at: datetime,
    counts: SyncCounts | None = None,
    error: str | None = None,
) -> None:
    """Stamp a run on its mapping and add it to the run history."""
    SyncMappingRepo(db).record_run(mapping, status, error=error, run_id=run_id)
    SyncRunRepo(db).add(
        mapping,
        status,
        run_id=run_id,
        started_at=started_at,
        counts=counts,
        error=error,
    )


def sync_mapping(
    db: Session,
    mapping: SyncMapping,
    notion: NotionPageRepo,
    credential: CaldavCredential,
    *,
    can_write: bool,
    run_id: str,
    started_at: datetime,
) -> str:
    """Run one mapping and return the status it recorded.

    A rejected credential propagates out untouched: it kills every mapping this
    user has, so only sync_user can answer it. So does a grant that may only
    read, since it stops two-way for all of them. Anything else, a database
    that is no longer shared included, stays this mapping's problem and the
    caller moves on to the next one.
    """
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
        counts = reconcile(
            db,
            notion,
            calendar,
            mapping=mapping,
            write_back=mapping.write_back and can_write,
        )
    except Exception as exc:
        db.rollback()
        if is_auth_failure(exc):
            record(
                db,
                mapping,
                STATUS_AUTH_ERROR,
                run_id=run_id,
                started_at=started_at,
                error=reason(exc),
            )
            raise
        if isinstance(exc, NotionReadOnly):
            record(
                db,
                mapping,
                STATUS_ERROR,
                run_id=run_id,
                started_at=started_at,
                error="Notion refused the write, reconnect Calnio to allow it",
            )
            raise
        record(
            db,
            mapping,
            STATUS_ERROR,
            run_id=run_id,
            started_at=started_at,
            error=reason(exc),
        )
        # Committed here, or the next mapping's rollback would take this
        # failure with it.
        db.commit()
        if is_rate_limited(exc):
            logger.opt(exception=exc).warning("sync stopped, asked to slow down: {}", exc)
            raise RateLimited(str(exc)) from exc
        if is_notion_outage(exc):
            logger.opt(exception=exc).warning("sync failed, notion was down: {}", exc)
            return STATUS_ERROR
        logger.opt(exception=exc).error("sync failed for this mapping: {}", exc)
        return STATUS_ERROR

    logger.info(
        "sync done: {} created, {} updated, {} deleted, "
        "{} written back, {} imported, {} trashed, {} failed",
        counts.created,
        counts.updated,
        counts.deleted,
        counts.pulled,
        counts.imported,
        counts.trashed,
        counts.failed,
    )
    if counts.failed:
        # The rest of the run went through, but a stuck event must still reach
        # the sync card and the admin page instead of hiding behind "ok".
        record(
            db,
            mapping,
            STATUS_ERROR,
            run_id=run_id,
            started_at=started_at,
            counts=counts,
            error=f"{counts.failed} events could not be synced. {counts.failure}",
        )
        db.commit()
        return STATUS_ERROR

    record(
        db, mapping, STATUS_OK, run_id=run_id, started_at=started_at, counts=counts
    )
    db.commit()
    return STATUS_OK


def sync_user(user_id: int) -> None:
    """Run every one of a user's eligible mappings. Never raises.

    Opens its own session because it runs on the scheduler thread, both from
    the interval loop and as a one-off job when the user flips a switch on.
    """
    # run= ties every line of this pass together, user= every line about this
    # person. Both sit in a fixed column on every log line, grep does the rest.
    run_id = uuid4().hex[:8]
    with (
        SessionLocal() as db,
        logger.contextualize(run=run_id, user=user_id),
    ):
        settings_repo = SyncSettingsRepo(db)
        row = settings_repo.get(user_id)
        connection_repo = NotionConnectionRepo(db)
        connection = connection_repo.get(user_id)
        credential = CaldavCredentialRepo(db).get(user_id)

        # Re-checked here rather than trusted from the caller: a one-off job
        # fires against a user whose setup could have changed since.
        if row is None or connection is None or credential is None or not row.enabled:
            logger.warning("sync skipped: setup incomplete")
            return

        mappings = SyncMappingRepo(db).eligible(user_id)
        if not mappings:
            logger.warning("sync skipped: no configured syncs")
            return

        # One Notion repo for the whole user: the grant is theirs, not a
        # mapping's, and every mapping queries through the same token.
        notion = NotionPageRepo(decrypt(connection.access_token_encrypted))

        failed = False
        for mapping in mappings:
            # Every line written from here down carries this sync's id, so one
            # grep follows one sync from its first query to its last write.
            with logger.contextualize(sync=mapping.id):
                started_at = datetime.now(timezone.utc)
                try:
                    status = sync_mapping(
                        db,
                        mapping,
                        notion,
                        credential,
                        can_write=connection.can_write,
                        run_id=run_id,
                        started_at=started_at,
                    )
                except RateLimited:
                    # iCloud limits the Apple ID and Notion the grant, and every
                    # sync of this user shares both, so the rest would only be
                    # refused too. Already recorded on the mapping that hit it.
                    failed = True
                    break
                except NotionReadOnly as exc:
                    # The grant is older than two-way sync, or its capabilities
                    # were taken away. Reading still works, so the user keeps a
                    # one-way sync until they connect Calnio again.
                    connection_repo.set_can_write(connection, False)
                    db.commit()
                    failed = True
                    logger.warning(
                        "two-way disabled: notion grant may only read ({})", exc
                    )
                    continue
                except Exception as exc:
                    db.rollback()
                    if is_auth_failure(exc):
                        settings_repo.disable(row)
                        settings_repo.record_run(row, STATUS_AUTH_ERROR)
                        record(
                            db,
                            mapping,
                            STATUS_AUTH_ERROR,
                            run_id=run_id,
                            started_at=started_at,
                            error=reason(exc),
                        )
                        db.commit()
                        logger.opt(exception=exc).error(
                            "syncing disabled for this user: credentials rejected ({})",
                            exc,
                        )
                        # Worth pushing: this switched the user's sync off, so
                        # nothing else will happen until they reconnect. It
                        # cannot repeat for the same reason. A mapping that
                        # merely errors is left to the Failures button, which
                        # would otherwise fire every tick.
                        notify(
                            f"Sync disabled: credentials rejected\n"
                            f"user {user_id}\nrun={run_id}\n{reason(exc)}",
                            buttons=True,
                        )
                        return
                    failed = True
                    record(
                        db,
                        mapping,
                        STATUS_ERROR,
                        run_id=run_id,
                        started_at=started_at,
                        error=reason(exc),
                    )
                    db.commit()
                    logger.opt(exception=exc).error("sync crashed: {}", exc)
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
        SyncRunRepo(db).prune()
        db.commit()

    logger.info("sync tick: {} eligible users", len(user_ids))
    for user_id in user_ids:
        try:
            sync_user(user_id)
        except Exception as exc:
            logger.opt(exception=exc).error("sync crashed for user {}: {}", user_id, exc)


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
