from datetime import date, datetime

import caldav
from icalendar import Calendar as ICalendar
from icalendar import Event as IEvent
from loguru import logger

from backend.repo.models import CalDavEvent


def _to_ical(event: CalDavEvent) -> str:
    """Render a CalDavEvent as an iCalendar string."""
    cal = ICalendar()
    cal.add("prodid", "-//calnio//caldav//EN")
    cal.add("version", "2.0")

    vevent = IEvent()
    vevent.add("uid", event.uid)
    vevent.add("summary", event.title)
    if event.all_day:
        vevent.add("dtstart", event.start.date())
        vevent.add("dtend", event.end.date())
    else:
        vevent.add("dtstart", event.start)
        vevent.add("dtend", event.end)
    vevent.add("dtstamp", event.updated_at or datetime.now())
    if event.created_at:
        vevent.add("created", event.created_at)

    cal.add_component(vevent)
    return cal.to_ical().decode("utf-8")


def _as_datetime(value: date | datetime) -> tuple[datetime, bool]:
    """Coerce an icalendar date/datetime to (datetime, all_day)."""
    if isinstance(value, datetime):
        return value, False
    return datetime(value.year, value.month, value.day), True


def _from_caldav(obj: caldav.Event, calendar: str) -> CalDavEvent:
    """Parse a caldav Event into a CalDavEvent."""
    vevent = obj.icalendar_component
    start, all_day = _as_datetime(vevent["dtstart"].dt)
    end, _ = _as_datetime(vevent["dtend"].dt)
    created = vevent.get("created")
    updated = vevent.get("last-modified")
    return CalDavEvent(
        uid=str(vevent["uid"]),
        title=str(vevent.get("summary", "")),
        start=start,
        end=end,
        all_day=all_day,
        calendar=calendar,
        href=str(obj.url),
        created_at=created.dt if created else None,
        updated_at=updated.dt if updated else None,
    )


class CalDavEventRepo:
    """CRUD repository for calendar events over CalDAV."""

    def __init__(
        self,
        caldav_url: str,
        username: str,
        password: str,
        calendar_url: str,
    ) -> None:
        self.caldav_url = caldav_url
        self.username = username
        self.password = password
        self.calendar_url = calendar_url
        self._calendar: caldav.Calendar | None = None  # pyright: ignore[reportGeneralTypeIssues]

    def connect(self) -> None:
        """Authenticate with iCloud and load the calendar."""
        logger.info("Connecting to CalDAV at {}", self.caldav_url)
        client = caldav.DAVClient(  # pyright: ignore[reportCallIssue]
            url=self.caldav_url,
            username=self.username,
            password=self.password,
        )
        self._calendar = client.calendar(url=self.calendar_url)
        logger.info("Loaded calendar {}", self.calendar_url)

    def get_range(self, start: datetime, end: datetime) -> list[CalDavEvent]:
        """Fetch events overlapping [start, end] via server-side time-range filter."""
        assert self._calendar is not None, "call connect() first"
        logger.info("Fetching events {} -> {}", start, end)
        results = self._calendar.search(
            start=start,
            end=end,
            event=True,
            expand=True,
        )
        logger.info("Found {} events", len(results))
        return [_from_caldav(r, self.calendar_url) for r in results]

    def create(self, event: CalDavEvent) -> CalDavEvent:
        """Create the event and return it with href filled in."""
        assert self._calendar is not None, "call connect() first"
        logger.info("Creating event {} ({})", event.uid, event.title)
        created = self._calendar.add_event(_to_ical(event))
        event.href = str(created.url)
        logger.info("Created event at {}", event.href)
        return event

    def update(self, event: CalDavEvent) -> CalDavEvent:
        """Overwrite the event at event.href and return it."""
        assert self._calendar is not None, "call connect() first"
        assert event.href, "event.href is required to update"
        logger.info("Updating event at {}", event.href)
        remote = self._calendar.event_by_url(event.href)
        remote.data = _to_ical(event)
        remote.save()
        logger.info("Updated event {}", event.uid)
        return event

    def delete(self, event: CalDavEvent) -> None:
        """Delete the event at event.href."""
        assert self._calendar is not None, "call connect() first"
        assert event.href, "event.href is required to delete"
        logger.info("Deleting event at {}", event.href)
        remote = self._calendar.event_by_url(event.href)
        remote.delete()
        logger.info("Deleted event {}", event.uid)
