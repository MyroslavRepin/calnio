from typing import Any, Callable

from notion_client import Client

from backend.core.logging import logger
from backend.parsers.notion import NotionParser
from backend.schemas.notion_database import NotionDatabase
from backend.schemas.notion_page import NotionPage


def paginate(fetch: Callable[[str | None], dict[str, Any]]) -> list[dict[str, Any]]:
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
        self.client = Client(auth=token)
        self.parser = NotionParser()

    def get_page(self, page_id: str) -> NotionPage:
        """Fetch a single page by id."""
        return self.parser.parse_page(self.client.pages.retrieve(page_id=page_id))

    def get_database(self, data_source_id: str) -> NotionDatabase:
        """Fetch a data source, its schema and metadata, by id."""
        # Notion API 2025-09-03: pages and schema live on the data source, not
        # on the database container.
        return self.parser.parse_database(
            self.client.data_sources.retrieve(data_source_id=data_source_id)
        )

    def query_database(
        self,
        data_source_id: str,
        *,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> list[NotionPage]:
        """Fetch every page in a data source, paginating fully."""

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

        pages = [self.parser.parse_page(page) for page in paginate(fetch)]
        logger.info("found {} notion pages in {}", len(pages), data_source_id)
        return pages

    def list_databases(self) -> list[NotionDatabase]:
        """Discover every data source shared with the integration."""

        def fetch(cursor: str | None) -> dict[str, Any]:
            return self.client.search(
                start_cursor=cursor,
                filter={"property": "object", "value": "data_source"},
            )

        databases = [self.parser.parse_database(db) for db in paginate(fetch)]
        logger.info("found {} notion databases", len(databases))
        return databases
