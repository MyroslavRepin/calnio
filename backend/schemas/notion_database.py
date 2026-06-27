from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotionDatabase(BaseModel):
    """Read-only projection of a Notion database (data source)."""

    id: str
    title: str
    properties: dict[str, Any]
    url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
