"""List pages from a Notion database. Usage: uv run python notion_demo.py <database_id>"""

import sys

from loguru import logger

from backend.core.config import settings
from backend.repo.notion_repo import NotionPageRepo


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: uv run python notion_demo.py <database_id>")
    database_id = sys.argv[1]

    repo = NotionPageRepo(token=settings.notion_token)
    repo.connect()

    pages = repo.query_database(database_id)
    for page in pages:
        logger.info("{} | {} | {}", page.title, page.updated_at, page.url)


if __name__ == "__main__":
    main()
