from datetime import datetime

import caldav

from backend.core.logging import logger
from backend.parsers.caldav import ICalParser
from backend.schemas.caldav_calendar import CalDavCalendar
from backend.schemas.caldav_event import CalDavEvent


class CalDavAccountRepo:
    """Calendars on one CalDAV account.

    Constructing it authenticates, so bad credentials raise
    caldav.lib.error.AuthorizationError here. That is how a credential gets
    verified.
    """

    def __init__(self, caldav_url: str, username: str, password: str) -> None:
        client = caldav.DAVClient(  # pyright: ignore[reportCallIssue]
            url=caldav_url,
            username=username,
            password=password,
        )
        self.principal = client.principal()

    def list_calendars(self) -> list[CalDavCalendar]:
        """Every calendar on the account. Doubles as the credential check."""
        calendars = self.principal.calendars()
        logger.info("found {} icloud calendars", len(calendars))
        return [
            CalDavCalendar(
                name=calendar.get_display_name() or "(unnamed)", url=str(calendar.url)
            )
            for calendar in calendars
        ]

    def create_calendar(self, name: str) -> CalDavCalendar:
        """Create a calendar in the account and return it."""
        calendar = self.principal.make_calendar(name=name)
        return CalDavCalendar(name=name, url=str(calendar.url))

    def get_calendar_url(self, name: str | None = None) -> str:
        """Find a calendar URL by display name, else take the first one."""
        calendars = self.principal.calendars()
        if not calendars:
            raise RuntimeError("no calendars found on icloud account")
        if name is not None:
            for calendar in calendars:
                if calendar.get_display_name() == name:
                    logger.info("using calendar {} ({})", name, calendar.url)
                    return str(calendar.url)
            raise RuntimeError(f"calendar {name!r} not found on icloud account")
        logger.info("using calendar {}", calendars[0].url)
        return str(calendars[0].url)


class CalDavEventRepo:
    """Events inside one calendar."""

    def __init__(
        self,
        caldav_url: str,
        username: str,
        password: str,
        calendar_url: str,
    ) -> None:
        client = caldav.DAVClient(  # pyright: ignore[reportCallIssue]
            url=caldav_url,
            username=username,
            password=password,
        )
        self.calendar_url = calendar_url
        self.calendar = client.calendar(url=calendar_url)
        self.parser = ICalParser()

    def get_range(self, start: datetime, end: datetime) -> list[CalDavEvent]:
        """Fetch events overlapping [start, end] with a server-side filter."""
        results = self.calendar.search(start=start, end=end, event=True, expand=True)
        return [self.parser.parse_event(r, self.calendar_url) for r in results]

    def create(self, event: CalDavEvent) -> CalDavEvent:
        """Create the event and return it with href filled in."""
        created = self.calendar.add_event(self.parser.render_event(event))
        event.href = str(created.url)
        return event

    def update(self, event: CalDavEvent) -> CalDavEvent:
        """Overwrite the event at event.href and return it."""
        assert event.href, "event.href is required to update"
        remote = self.calendar.event_by_url(event.href)
        remote.data = self.parser.render_event(event)
        remote.save()
        return event

    def delete(self, event: CalDavEvent) -> None:
        """Delete the event at event.href."""
        assert event.href, "event.href is required to delete"
        self.calendar.event_by_url(event.href).delete()

    def delete_by_href(self, href: str) -> None:
        """Delete the event at href, without needing a CalDavEvent."""
        self.calendar.event_by_url(href).delete()

    def delete_all(self) -> int:
        """Delete every event in the calendar and return how many went."""
        events = self.calendar.events()
        logger.warning("deleting all {} events from {}", len(events), self.calendar_url)
        for event in events:
            event.delete()
        return len(events)
