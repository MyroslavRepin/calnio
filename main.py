from datetime import datetime, timedelta, timezone

import caldav
from loguru import logger

from backend.core.config import settings
from backend.repo.caldav_repo import CalDavEventRepo
from backend.repo.notion_repo import NotionPageRepo
from backend.schemas.caldav_event import CalDavEvent
from backend.schemas.notion_page import NotionPage

CALDAV_URL = "https://caldav.icloud.com/"


def discover_calendar_url(name: str | None = None) -> str:
    """Find an iCloud calendar URL — by display name, else the first one."""
    client = caldav.DAVClient(  # pyright: ignore[reportCallIssue]
        url=CALDAV_URL,
        username=settings.icloud_email,
        password=settings.app_specific_password,
    )
    calendars = client.principal().calendars()
    if not calendars:
        raise RuntimeError("no calendars found on iCloud account")
    if name is not None:
        for cal in calendars:
            if cal.get_display_name() == name:
                url = str(cal.url)
                logger.info("Using calendar {} ({})", name, url)
                return url
        raise RuntimeError(f"calendar {name!r} not found on iCloud account")
    url = str(calendars[0].url)
    logger.info("Using calendar {}", url)
    return url


def week_range() -> tuple[datetime, datetime]:
    """Return [Monday 00:00, next Monday 00:00) of the current week in UTC."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start, start + timedelta(days=7)


def main() -> None:
    from backend.repo.caldav_repo import CalDavEventRepo

    calendar_url = discover_calendar_url()
    repo = CalDavEventRepo(
        caldav_url=CALDAV_URL,
        username=settings.icloud_email,
        password=settings.app_specific_password,
        calendar_url=calendar_url,
    )
    repo.connect()

    start, end = week_range()
    events = repo.get_range(start, end)

    logger.info("This week ({} -> {}):", start.date(), end.date())
    for event in sorted(events, key=lambda e: e.start.replace(tzinfo=None)):
        logger.info("{} | {} -> {}", event.title, event.start, event.end)


def list_notion_databases() -> None:
    """Print every Notion database shared with the integration, with its id."""
    from backend.repo.notion_repo import NotionPageRepo

    repo = NotionPageRepo(token=settings.notion_token)
    repo.connect()

    dbs = repo.list_databases()
    if not dbs:
        logger.warning("No databases found — did you share one with the integration?")
        return
    for db in dbs:
        logger.info("{} | {}", db.id, db.title or "(untitled)")


def _page_to_event(page: "NotionPage", calendar: str) -> "CalDavEvent | None":
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


def sync_notion_to_caldav() -> None:
    calendar_url = discover_calendar_url(name="Tasks")
    notion = NotionPageRepo(token=settings.notion_token)
    caldav_orm = CalDavEventRepo(
        caldav_url=CALDAV_URL,
        username=settings.icloud_email,
        password=settings.app_specific_password,
        calendar_url=calendar_url,
    )
    notion.connect()
    caldav_orm.connect()

    # data_source_id — the id printed by list_notion_databases().
    tasks_data_source_id = "e17a5558-72b4-8367-8c69-87a36a845e37"
    pages = notion.query_database(tasks_data_source_id)

    logger.info("Fetched {} pages from Notion", len(pages))
    for page in pages:
        event = _page_to_event(page, "Personal")
        if event is None:
            logger.info("Skipping (no Due Date): {}", page.title)
            continue
        logger.info("Syncing event: {}", page.title)
        caldav_orm.create(event)


if __name__ == "__main__":
    # list_notion_databases()
    # get_pages()
    sync_notion_to_caldav()
