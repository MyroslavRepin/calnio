from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from fastapi import Depends, HTTPException, status
from notion_client.errors import (
    APIResponseError,
    HTTPResponseError,
    RequestTimeoutError,
)
from sqlalchemy.orm import Session

from backend.core.crypto import decrypt
from backend.core.logging import logger
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.notion_connection import NotionConnection
from backend.models.user import User
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.notion import NotionPageRepo


@contextmanager
def notion_errors() -> Iterator[None]:
    """Map Notion API failures onto HTTP status codes, never onto a 401."""
    try:
        yield
    except APIResponseError as exc:
        # Subclass of HTTPResponseError, so it has to be caught first.
        if exc.status in (401, 403):
            logger.warning("notion rejected the grant: {}", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="notion rejected this connection, reconnect calnio",
            )
        if exc.status == 404:
            logger.warning("notion object missing or unshared: {}", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="that database is no longer shared with calnio",
            )
        logger.error("notion api error: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="could not reach notion, try again",
        )
    except (HTTPResponseError, RequestTimeoutError, httpx.HTTPError) as exc:
        logger.error("notion unreachable: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="could not reach notion, try again",
        )


def get_connection(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
) -> NotionConnection:
    """The current user's stored grant, or 404."""
    row = NotionConnectionRepo(db).get(user.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no notion connection"
        )
    return row


def get_notion_repo(
    row: NotionConnection = Depends(get_connection),
) -> NotionPageRepo:
    """An authenticated Notion repo for this user's grant."""
    return NotionPageRepo(decrypt(row.access_token_encrypted))


def date_property_names(row: NotionConnection) -> list[str]:
    """Date column names on the selected data source, in schema order."""
    if row.data_source_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pick a notion database first",
        )
    with notion_errors():
        database = get_notion_repo(row).get_database(row.data_source_id)
    return [
        name for name, prop in database.properties.items() if prop.get("type") == "date"
    ]
