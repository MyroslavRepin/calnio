"""Fetch this week's events from iCloud over CalDAV."""

from datetime import datetime, timedelta, timezone

import caldav
from loguru import logger

from backend.core.config import settings
from backend.repo.caldav_repo import CalDavEventRepo

CALDAV_URL = "https://caldav.icloud.com/"


def discover_calendar_url() -> str:
    """Find the first iCloud calendar URL."""
    client = caldav.DAVClient(  # pyright: ignore[reportCallIssue]
        url=CALDAV_URL,
        username=settings.icloud_email,
        password=settings.app_specific_password,
    )
    calendars = client.principal().calendars()
    if not calendars:
        raise RuntimeError("no calendars found on iCloud account")
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


if __name__ == "__main__":
    main()
