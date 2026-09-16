from datetime import datetime, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.schemas.notion_database import NotionDatabase
from backend.schemas.notion_page import NotionDate, NotionPage, NotionPageWrite


class NotionParser:
    """Raw Notion payloads into domain schemas."""

    def parse_page(self, obj: dict[str, Any]) -> NotionPage:
        """Parse a raw Notion page object."""
        properties = obj.get("properties", {})
        parent = obj.get("parent", {})
        parent_type = parent.get("type", "")
        return NotionPage(
            id=obj["id"],
            title=self.parse_title(properties),
            parent_id=self.parse_parent_id(parent, parent_type),
            parent_type=parent_type,
            properties=properties,
            url=obj.get("url"),
            archived=obj.get("in_trash", False) or obj.get("archived", False),
            created_at=self.parse_timestamp(obj.get("created_time")),
            updated_at=self.parse_timestamp(obj.get("last_edited_time")),
        )

    def parse_database(self, obj: dict[str, Any]) -> NotionDatabase:
        """Parse a raw Notion data source object."""
        return NotionDatabase(
            id=obj["id"],
            title=self.join_rich_text(obj.get("title", [])),
            properties=obj.get("properties", {}),
            url=obj.get("url"),
            created_at=self.parse_timestamp(obj.get("created_time")),
            updated_at=self.parse_timestamp(obj.get("last_edited_time")),
        )

    def parse_date(self, properties: dict[str, Any], name: str) -> NotionDate | None:
        """Read one date column off a page's properties, None when it is empty."""
        value = properties.get(name, {}).get("date")
        if not value or not value.get("start"):
            return None

        # "YYYY-MM-DD" is Notion's all day shape, and it carries no zone.
        all_day = len(value["start"]) == 10
        zone_name = None
        if not all_day:
            zone_name = value.get("time_zone")

        end = None
        if value.get("end"):
            end = self.parse_date_value(value["end"], zone_name)

        return NotionDate(
            start=self.parse_date_value(value["start"], zone_name),
            end=end,
            all_day=all_day,
            time_zone=zone_name,
        )

    def parse_date_value(self, value: str, zone_name: str | None) -> datetime:
        """One end of a Notion date, as an aware datetime."""
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed

        zone = self.load_zone(zone_name)
        if zone is not None:
            return parsed.replace(tzinfo=zone)
        return parsed.replace(tzinfo=timezone.utc)

    def render_date(self, date: NotionDate) -> dict[str, Any]:
        """Render a date property value, in the shape Notion sent it in."""
        zone = self.load_zone(date.time_zone)

        value: dict[str, Any] = {
            "start": self.render_date_value(date.start, date.all_day, zone),
            "end": None,
        }
        if date.end is not None:
            value["end"] = self.render_date_value(date.end, date.all_day, zone)
        if zone is not None:
            value["time_zone"] = date.time_zone

        return {"date": value}

    def render_date_value(
        self, value: datetime, all_day: bool, zone: tzinfo | None
    ) -> str:
        """One end of a date, as the string Notion stores."""
        if all_day:
            return value.date().isoformat()
        if zone is not None:
            # Notion refuses an offset on a date that names a zone: it stores
            # the wall clock reading in that zone instead.
            return value.astimezone(zone).replace(tzinfo=None).isoformat()
        return value.isoformat()

    def render_title(self, text: str) -> dict[str, Any]:
        """Render a title property value."""
        return {"title": [{"text": {"content": text}}]}

    def render_properties(self, write: NotionPageWrite) -> dict[str, Any]:
        """Render the properties body of a page create or update."""
        return {
            write.title_property: self.render_title(write.title),
            write.date_property: self.render_date(write.date),
        }

    def load_zone(self, name: str | None) -> ZoneInfo | None:
        """The named IANA zone, or None when there is none to load.

        A host without a zone database answers nothing, and the caller then
        writes a UTC offset instead, which says the same instant in a shape
        Notion also accepts.
        """
        if name is None:
            return None
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            return None

    def find_title_property(self, properties: dict[str, Any]) -> str | None:
        """The name of the column holding titles, which every database has one of."""
        for name, prop in properties.items():
            if prop.get("type") == "title":
                return name
        return None

    def parse_title(self, properties: dict[str, Any]) -> str:
        """Join plain_text of whichever property has type 'title'."""
        for prop in properties.values():
            if prop.get("type") == "title":
                return self.join_rich_text(prop.get("title", []))
        return ""

    def parse_parent_id(self, parent: dict[str, Any], parent_type: str) -> str | None:
        """Read parent[parent_type]. Workspace parents hold True, not an id."""
        value = parent.get(parent_type)
        if isinstance(value, str):
            return value
        return None

    def parse_timestamp(self, value: str | None) -> datetime | None:
        """Parse an ISO 8601 'Z' timestamp into an aware UTC datetime."""
        if not value:
            return None
        return datetime.fromisoformat(value)

    def join_rich_text(self, parts: list[dict[str, Any]]) -> str:
        """Concatenate plain_text of a Notion rich-text array."""
        return "".join(part.get("plain_text", "") for part in parts)
