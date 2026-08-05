from datetime import date, datetime

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
        end, _ = self.parse_datetime(vevent["dtend"].dt)
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

    def render_event(self, event: CalDavEvent) -> str:
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

    def parse_datetime(self, value: date | datetime) -> tuple[datetime, bool]:
        """Coerce an icalendar date or datetime to (datetime, all_day)."""
        if isinstance(value, datetime):
            return value, False
        return datetime(value.year, value.month, value.day), True
