from datetime import datetime
from typing import Any

from backend.schemas.notion_database import NotionDatabase
from backend.schemas.notion_page import NotionPage


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
            archived=obj.get("archived", False),
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
