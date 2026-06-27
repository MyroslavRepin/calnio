from datetime import datetime
from typing import Any, Callable

from loguru import logger
from notion_client import Client

from backend.repo.models import NotionDatabase, NotionPage


def _join_rich_text(parts: list[dict[str, Any]]) -> str:
    """Concatenate plain_text of a Notion rich-text array."""
    return "".join(p.get("plain_text", "") for p in parts)


def _extract_title(properties: dict[str, Any]) -> str:
    """Join plain_text of whichever property has type == 'title'."""
    for prop in properties.values():
        if prop.get("type") == "title":
            return _join_rich_text(prop.get("title", []))
    return ""


def _extract_parent_id(parent: dict[str, Any], parent_type: str) -> str | None:
    """Read parent[parent_type]; workspace parents hold `True`, not an id."""
    value = parent.get(parent_type)
    if isinstance(value, str):
        return value
    return None


def _parse_ts(value: str | None) -> datetime | None:
    """Parse an ISO 8601 'Z' timestamp into an aware UTC datetime."""
    if not value:
        return None
    return datetime.fromisoformat(value)


def _from_notion(obj: dict[str, Any]) -> NotionPage:
    """Parse a raw Notion page object into a NotionPage."""
    properties = obj.get("properties", {})
    parent = obj.get("parent", {})
    parent_type = parent.get("type", "")
    return NotionPage(
        id=obj["id"],
        title=_extract_title(properties),
        parent_id=_extract_parent_id(parent, parent_type),
        parent_type=parent_type,
        properties=properties,
        url=obj.get("url"),
        archived=obj.get("archived", False),
        created_at=_parse_ts(obj.get("created_time")),
        updated_at=_parse_ts(obj.get("last_edited_time")),
    )


def _from_notion_database(obj: dict[str, Any]) -> NotionDatabase:
    """Parse a raw Notion database object into a NotionDatabase."""
    return NotionDatabase(
        id=obj["id"],
        title=_join_rich_text(obj.get("title", [])),
        properties=obj.get("properties", {}),
        url=obj.get("url"),
        created_at=_parse_ts(obj.get("created_time")),
        updated_at=_parse_ts(obj.get("last_edited_time")),
    )


def _paginate(fetch: Callable[[str | None], dict[str, Any]]) -> list[dict[str, Any]]:
    """Drain a Notion cursor-paginated endpoint into one list of raw results."""
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        data = fetch(cursor)
        results.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results


class NotionPageRepo:
    """Read-only repository for Notion databases and their pages."""

    def __init__(self, token: str) -> None:
        self.token: str = token
        self._client: Client | None = None

    def connect(self) -> None:
        """Build the Notion SDK client with auth."""
        logger.info("Connecting to Notion")
        self._client = Client(auth=self.token)
        logger.info("Notion client ready")

    @property
    def client(self) -> Client:
        assert self._client is not None, "call connect() first"
        return self._client

    def get_page(self, page_id: str) -> NotionPage:
        """Fetch a single page by id."""
        logger.info("Fetching page {}", page_id)
        obj = self.client.pages.retrieve(page_id=page_id)
        return _from_notion(obj)

    def get_database(self, data_source_id: str) -> NotionDatabase:
        """Fetch a data source (schema + metadata) by id.

        Notion API 2025-09-03: pages + schema live on the data source, not the
        database container. Pass a data_source_id (from `list_databases`).
        """
        logger.info("Fetching data source {}", data_source_id)
        obj = self.client.data_sources.retrieve(data_source_id=data_source_id)
        return _from_notion_database(obj)

    def query_database(
        self,
        data_source_id: str,
        *,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> list[NotionPage]:
        """Fetch pages in a data source, paginating fully; optional Notion filter/sorts."""
        logger.info("Querying data source {}", data_source_id)

        def fetch(cursor: str | None) -> dict[str, Any]:
            body: dict[str, Any] = {
                "data_source_id": data_source_id,
                "start_cursor": cursor,
            }
            if filter is not None:
                body["filter"] = filter
            if sorts is not None:
                body["sorts"] = sorts
            return self.client.data_sources.query(**body)

        pages = [_from_notion(p) for p in _paginate(fetch)]
        logger.info("Found {} pages in data source {}", len(pages), data_source_id)
        return pages

    def list_databases(self) -> list[NotionDatabase]:
        """Discover every database shared with the integration."""
        logger.info("Listing databases shared with integration")

        def fetch(cursor: str | None) -> dict[str, Any]:
            return self.client.search(
                start_cursor=cursor,
                filter={"property": "object", "value": "data_source"},
            )

        dbs = [_from_notion_database(d) for d in _paginate(fetch)]
        logger.info("Found {} databases", len(dbs))
        return dbs
