from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

import httpx
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from notion_client.errors import (
    APIResponseError,
    HTTPResponseError,
    RequestTimeoutError,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt, encrypt
from backend.core.logging import logger
from backend.core.oauth import NOTION_REVOKE_URL, oauth
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.notion_connection import NotionConnection
from backend.models.user import User
from backend.repo.notion_connection_repo import NotionConnectionRepo
from backend.repo.notion_repo import NotionPageRepo

# Two path families in one router on purpose. The OAuth dance sits under
# /auth/oauth/* next to Google's, because that is what a reader looking for an
# OAuth callback expects; the resource routes take /api/v1 like every other new
# router. One feature stays in one file, so the paths are spelled out in full
# rather than set as a router prefix.
router = APIRouter(tags=["notion"])

OAUTH_BASE = "/auth/oauth/notion"
BASE = "/api/v1/me/notion"

# Where the OAuth dance lands the browser, success or failure.
LANDING = "/dashboard/connections"


class AuthorizeUrlResponse(BaseModel):
    authorize_url: str


class SelectDatabaseRequest(BaseModel):
    data_source_id: str = Field(min_length=1)


class ConnectionStatus(BaseModel):
    """What the dashboard is allowed to see. Never carries the access token."""

    connected: bool
    workspace_name: str | None
    workspace_icon: str | None
    data_source_id: str | None
    data_source_name: str | None
    last_verified_at: datetime | None


class NotionDatabaseOption(BaseModel):
    """One row in the database picker.

    A projection of NotionDatabase without `properties` — the picker needs a
    name, not the workspace's column schema.
    """

    id: str
    title: str
    url: str | None


def _status(row: NotionConnection) -> ConnectionStatus:
    return ConnectionStatus(
        connected=True,
        workspace_name=row.workspace_name,
        workspace_icon=row.workspace_icon,
        data_source_id=row.data_source_id,
        data_source_name=row.data_source_name,
        last_verified_at=row.last_verified_at,
    )


@contextmanager
def _notion_errors() -> Iterator[None]:
    """Map Notion API failures onto HTTP status codes.

    Never 401 — the frontend's apiFetch auto-refreshes and retries on 401, and
    a revoked Notion token will never start working on a retry. Notion
    rejecting us is a 400 telling the user to reconnect; Notion being
    unreachable is a 502.

    Raw exception text is logged, never returned: it can carry request URLs and
    the bearer token.
    """
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


def _repo(row: NotionConnection) -> NotionPageRepo:
    """An authenticated Notion repo for this user's grant.

    The only place a stored Notion token is decrypted. Lift this into
    services/notion.py when the per-user sync loop needs the same path.
    """
    repo = NotionPageRepo(decrypt(row.access_token_encrypted))
    repo.connect()
    return repo


def _bounce(flag: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_url}{LANDING}?notion_error={flag}")


@router.get(f"{OAUTH_BASE}/login", response_model=AuthorizeUrlResponse)
async def notion_login(request: Request, user: User = Depends(get_current_user)):
    """Hand the frontend an authorize URL instead of redirecting to it.

    Unlike Google's login, this route needs to know who is asking — and the
    access cookie lives 5 minutes. A plain link would 401 whenever the
    dashboard had been open a while, with no apiFetch in the loop to refresh
    silently. Returning JSON lets the frontend fetch it through apiFetch (which
    does refresh), then navigate, so the callback seconds later still has a
    valid cookie.
    """
    redirect_uri = settings.notion_oauth_redirect_uri
    rv = await oauth.notion.create_authorization_url(redirect_uri)
    # Stores the CSRF `state` in the session cookie. authorize_redirect would
    # do this for us, but it also returns the 302 we are avoiding here.
    await oauth.notion.save_authorize_data(request, redirect_uri=redirect_uri, **rv)
    logger.info("notion authorize url issued for user {}", user.id)
    return AuthorizeUrlResponse(authorize_url=rv["url"])


@router.get(f"{OAUTH_BASE}/callback")
async def notion_callback(request: Request, db: Session = Depends(get_session)):
    """Exchange the code, store the grant, send the browser back to the app.

    The successful exchange is the verification — a token Notion just minted
    works — so there is no probe call here. The frontend fetches the database
    list itself once it lands.
    """
    # get_current_user is called by hand rather than as a dependency: its 401 is
    # a JSON body, and this route is a browser navigation that has to end on a
    # page. Expiry here means the user sat on Notion's consent screen for over
    # five minutes; they land back on the dashboard and click connect again.
    try:
        user = get_current_user(request, db)
    except HTTPException:
        logger.warning("notion callback arrived without a valid session")
        return _bounce("session")

    try:
        token = await oauth.notion.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning("notion oauth failed: {}", exc.error)
        return _bounce("oauth")

    # access_token + workspace_id are the two fields everything downstream
    # depends on; anything else Notion sends is optional.
    if not token.get("access_token") or not token.get("workspace_id"):
        logger.warning("notion oauth: unexpected token response shape")
        return _bounce("token")

    NotionConnectionRepo(db).upsert(
        user.id,
        encrypt(token["access_token"]),
        bot_id=token.get("bot_id", ""),
        workspace_id=token["workspace_id"],
        workspace_name=token.get("workspace_name"),
        workspace_icon=token.get("workspace_icon"),
    )
    db.commit()

    logger.info("notion connected for user {}", user.id)
    return RedirectResponse(f"{settings.frontend_url}{LANDING}")


@router.get(BASE, response_model=ConnectionStatus)
async def get_notion(row: NotionConnection = Depends(get_connection)):
    return _status(row)


def _revoke(access_token: str) -> None:
    """Ask Notion to drop the grant. Best effort — never blocks a disconnect.

    The iCloud disconnect deliberately leaves the user's events alone because
    they are the user's data. This is the opposite case: the grant is ours, and
    leaving it live would keep Calnio listed in the user's Notion connections
    after they asked us to go away.
    """
    try:
        httpx.post(
            NOTION_REVOKE_URL,
            auth=(
                settings.notion_oauth_client_id,
                settings.notion_oauth_client_secret,
            ),
            json={"token": access_token},
            timeout=10,
        ).raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("notion revoke failed, forgetting the grant anyway: {}", exc)


@router.delete(BASE, status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_notion(
    row: NotionConnection = Depends(get_connection),
    db: Session = Depends(get_session),
):
    user_id = row.user_id
    _revoke(decrypt(row.access_token_encrypted))
    NotionConnectionRepo(db).delete(row)
    db.commit()
    logger.info("notion disconnected for user {}", user_id)


@router.get(f"{BASE}/databases", response_model=list[NotionDatabaseOption])
async def list_notion_databases(row: NotionConnection = Depends(get_connection)):
    """The data sources the user ticked in Notion's consent picker.

    Legitimately empty when they authorized the workspace without sharing a
    database — an easy thing to do in Notion's dialog — so the client renders
    an empty state rather than treating it as an error.
    """
    with _notion_errors():
        databases = _repo(row).list_databases()
    return [
        NotionDatabaseOption(id=d.id, title=d.title, url=d.url) for d in databases
    ]


@router.put(f"{BASE}/database", response_model=ConnectionStatus)
async def select_notion_database(
    body: SelectDatabaseRequest,
    row: NotionConnection = Depends(get_connection),
    db: Session = Depends(get_session),
):
    """Point syncing at one of the workspace's data sources.

    Verified with a single retrieve rather than by scanning the whole list: it
    proves the data source is still shared with us, costs one call instead of a
    paginated search, and hands back the authoritative title to store. An id we
    cannot see comes back as a Notion 404, which _notion_errors turns into 400.
    """
    with _notion_errors():
        database = _repo(row).get_database(body.data_source_id)

    NotionConnectionRepo(db).set_data_source(row, database.id, database.title)
    db.commit()
    logger.info("notion data source selected for user {}", row.user_id)
    return _status(row)
