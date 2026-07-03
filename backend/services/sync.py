from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select

from backend.core.config import settings
from backend.deps.db import SessionLocal
from backend.models.synced_event import SyncedEvent
from backend.repo.caldav_repo import CalDavEventRepo, get_calendar_url
from backend.repo.notion_repo import NotionPageRepo
from backend.schemas.caldav_event import CalDavEvent as CalDavEventScheme
from backend.schemas.notion_page import NotionPage

# TODO(phase3): move to .env / Settings
tasks_data_source_id = "e17a5558-72b4-8367-8c69-87a36a845e37"


def _page_to_event(page: NotionPage, calendar: str) -> CalDavEventScheme | None:
    """Map a Notion task page to a CalDavEvent; None if it has no Due Date."""
    due = page.properties.get("Due Date", {}).get("date")
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
    """True if the Notion page is newer than what we last synced (LWW)."""
    if event.updated_at is None or row.notion_last_edited is None:
        return True  # missing timestamp -> re-push, safer than skipping
    return event.updated_at > row.notion_last_edited


def _build_repos() -> tuple[NotionPageRepo, CalDavEventRepo, str]:
    """Connect Notion + CalDAV repos and resolve the target calendar URL."""
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
    """One-way push Notion -> CalDAV; synced_events links page id -> caldav href."""
    notion, caldav, calendar_url = _build_repos()

    pages = notion.query_database(tasks_data_source_id)
    events: list[CalDavEventScheme] = []
    for page in pages:
        if page.archived:
            continue
        event = _page_to_event(page, calendar_url)
        if event is not None:
            events.append(event)
    current_ids = {e.uid for e in events}

    with SessionLocal() as db:
        rows = db.scalars(select(SyncedEvent)).all()
        by_id = {row.notion_page_id: row for row in rows}

        # Commit per event so a failure mid-batch never orphans CalDAV events
        # (uncommitted rows -> next run re-creates -> iCloud 412 duplicate).
        for event in events:
            row = by_id.get(event.uid)
            if row is not None and not _changed(event, row):
                continue
            try:
                if row is None:
                    created = caldav.create(event)
                    db.add(
                        SyncedEvent(
                            notion_page_id=event.uid,
                            caldav_href=created.href,
                            caldav_uid=event.uid,
                            etag=None,
                            notion_last_edited=event.updated_at,
                        )
                    )
                    logger.info("Created {} ({})", event.uid, event.title)
                else:
                    event.href = row.caldav_href
                    updated = caldav.update(event)
                    row.caldav_href = updated.href
                    row.notion_last_edited = event.updated_at
                    logger.info("Updated {} ({})", event.uid, event.title)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Sync failed for {} ({}): {}", event.uid, event.title, exc)

        # Reconcile deletes: rows whose Notion page is gone / archived / lost its date.
        for row in rows:
            if row.notion_page_id in current_ids:
                continue
            try:
                caldav.delete_by_href(row.caldav_href)
                db.delete(row)
                db.commit()
                logger.info("Deleted {}", row.notion_page_id)
            except Exception as exc:
                db.rollback()
                logger.error("Delete failed for {}: {}", row.notion_page_id, exc)


def delete_all() -> int:
    _, caldav, _ = _build_repos()
    return caldav.delete_all()
