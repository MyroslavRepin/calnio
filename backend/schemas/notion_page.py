from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotionPage(BaseModel):
    """Read-only projection of a Notion page."""

    id: str
    title: str
    parent_id: str | None = None
    parent_type: str
    properties: dict[str, Any]
    url: str | None = None
    archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
