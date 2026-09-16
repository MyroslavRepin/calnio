from datetime import date, datetime, timedelta, timezone

import caldav
from icalendar import Calendar as ICalendar
from icalendar import Event as IEvent

from backend.schemas.caldav_event import CalDavEvent


class ICalParser:
    """iCalendar payloads into events, and events back into iCalendar."""

    def parse_event(self, obj: caldav.Event, calendar: str) -> CalDavEvent:
        """Parse a caldav Event into a CalDavEvent."""
        vevent = obj.icalendar_component
        start, all_day = self.parse_datetime(vevent["dtstart"].dt)
        created = vevent.get("created")
        updated = vevent.get("last-modified")
        return CalDavEvent(
            uid=str(vevent["uid"]),
            title=str(vevent.get("summary", "")),
            start=start,
            end=self.parse_end(vevent, start, all_day),
            all_day=all_day,
            calendar=calendar,
            href=str(obj.url),
            created_at=created.dt if created else None,
            updated_at=updated.dt if updated else None,
            recurring=any(
                vevent.get(key) is not None
                for key in ("rrule", "rdate", "recurrence-id")
            ),
            has_attendees=vevent.get("attendee") is not None,
        )

    def render_event(self, event: CalDavEvent) -> str:
        """Render a CalDavEvent as an iCalendar string."""
        cal = ICalendar()
        cal.add("prodid", "-//calnio//caldav//EN")
        cal.add("version", "2.0")

        vevent = IEvent()
        vevent.add("uid", event.uid)
        self.apply_event(vevent, event)
        if event.created_at:
            vevent.add("created", event.created_at)

        cal.add_component(vevent)
        return cal.to_ical().decode("utf-8")

    def apply_event(self, vevent: IEvent, event: CalDavEvent) -> None:
        """Write an event's fields onto a VEVENT, leaving the rest of it alone.

        Updating in place rather than rendering a fresh VEVENT, because an
        event the user made in Apple Calendar carries alarms, notes and a
        location that Calnio has no column for and must not destroy.
        """
        for key in ("summary", "dtstart", "dtend", "dtstamp", "last-modified"):
            vevent.pop(key, None)

        vevent.add("summary", event.title)
        if event.all_day:
            vevent.add("dtstart", event.start.date())
            vevent.add("dtend", event.end.date())
        else:
            vevent.add("dtstart", event.start)
            vevent.add("dtend", event.end)

        now = datetime.now(timezone.utc)
        vevent.add("dtstamp", now)
        vevent.add("last-modified", now)

        # Apple clients ignore a changed event whose sequence went backwards,
        # and a fresh VEVENT has no sequence at all.
        sequence = vevent.pop("sequence", None)
        if sequence is not None:
            vevent.add("sequence", int(sequence) + 1)

    def parse_end(
        self, vevent: IEvent, start: datetime, all_day: bool
    ) -> datetime:
        """The event's end, worked out from whichever field it carries.

        DTEND is optional in iCalendar: an event may state a DURATION instead,
        or neither, which means a day for an all day event and an instant for
        any other.
        """
        dtend = vevent.get("dtend")
        if dtend is not None:
            end, _ = self.parse_datetime(dtend.dt)
            return end

        duration = vevent.get("duration")
        if duration is not None:
            return start + duration.dt

        if all_day:
            return start + timedelta(days=1)
        return start

    def parse_datetime(self, value: date | datetime) -> tuple[datetime, bool]:
        """Coerce an icalendar date or datetime to (datetime, all_day).

        An all day date becomes midnight UTC, the one form the rest of the app
        compares and stores. A floating datetime, one the server sent without a
        zone, is read as UTC, since nothing else about it says otherwise.
        """
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc), False
            return value, False
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc), True
