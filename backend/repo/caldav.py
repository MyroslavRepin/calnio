from datetime import datetime
from urllib.parse import urlparse

import caldav
import caldav.lib.error as caldav_error

from backend.core.logging import logger
from backend.parsers.caldav import ICalParser
from backend.schemas.caldav_calendar import CalDavCalendar
from backend.schemas.caldav_event import CalDavChanges, CalDavEvent


def href_path(href: str) -> str:
    """The path part of an href, the part two spellings of it agree on.

    The same event can be named in full or as a path alone, depending on which
    response it came out of, so nothing compares hrefs whole.
    """
    return urlparse(href).path


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

    def changes(self, sync_token: str | None, known_hrefs: set[str]) -> CalDavChanges:
        """What the calendar did since the token: events changed, hrefs gone.

        iCloud answers a sync-collection report (RFC 6578) with only what moved
        since the token, and names the resources that no longer exist, which is
        the one way a deletion is ever heard about: a deleted event leaves
        nothing behind, not even a time of death.

        Without a token, or with one the server has forgotten, the library
        lists the whole calendar instead. A deletion is then whatever href the
        caller knows and the server did not mention, which is why the caller
        hands its hrefs in.
        """
        collection = self.calendar.get_objects_by_sync_token(
            sync_token=sync_token, load_objects=False
        )
        # The library answers with a "fake-" token when it listed the whole
        # calendar instead of asking the server for a diff.
        listed_everything = str(collection.sync_token).startswith("fake-")
        known_by_path = {href_path(href): href for href in known_hrefs}

        events: list[CalDavEvent] = []
        deleted: list[str] = []
        seen: set[str] = set()

        for obj in collection:
            path = href_path(str(obj.url))
            seen.add(path)
            try:
                obj.load(only_if_unloaded=True)
            except caldav_error.NotFoundError:
                # Named by the diff, and already gone from the server.
                known = known_by_path.get(path)
                if known is not None:
                    deleted.append(known)
                continue
            event = self.parser.parse_event(obj, self.calendar_url)
            # Answered in the caller's own spelling of the href, so it can find
            # the event's row without normalising anything itself.
            event.href = known_by_path.get(path, event.href)
            events.append(event)

        if listed_everything:
            deleted = [href for path, href in known_by_path.items() if path not in seen]

        logger.info(
            "{} events changed and {} gone in {}",
            len(events),
            len(deleted),
            self.calendar_url,
        )
        return CalDavChanges(
            events=events, deleted_hrefs=deleted, sync_token=collection.sync_token
        )

    def create(self, event: CalDavEvent) -> CalDavEvent:
        """Create the event and return it with href filled in."""
        created = self.calendar.add_event(self.parser.render_event(event))
        event.href = str(created.url)
        return event

    def update(self, event: CalDavEvent) -> CalDavEvent:
        """Write the event's fields onto the one at event.href and return it.

        Edited in place rather than replaced, because the event may be one the
        user made in Apple Calendar, carrying an alarm, a location and notes
        that Calnio has nowhere to keep and must not drop.
        """
        assert event.href, "event.href is required to update"
        remote = self.calendar.event_by_url(event.href)
        remote.load()
        with remote.edit_icalendar_instance() as calendar:
            self.parser.apply_event(calendar.walk("vevent")[0], event)
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
