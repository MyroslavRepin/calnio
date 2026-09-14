from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt, encrypt
from backend.core.logging import logger
from backend.core.oauth import oauth
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.deps.notion import get_connection, get_notion_repo, notion_errors
from backend.models.notion_connection import NotionConnection
from backend.models.user import User
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.notion import NotionPageRepo
from backend.repo.sync_mapping import SyncMappingRepo
from backend.schemas.notion_connection import (
    AuthorizeUrlResponse,
    ConnectionStatus,
    NotionDatabaseOption,
)

router = APIRouter(tags=["notion"])


def redirect_with_error(flag: str) -> RedirectResponse:
    """Send the browser back to the connections page carrying an error flag."""
    return RedirectResponse(
        f"{settings.frontend_url}/dashboard/connections?notion_error={flag}"
    )


@router.get("/auth/oauth/notion/login", response_model=AuthorizeUrlResponse)
async def notion_login(request: Request, user: User = Depends(get_current_user)):
    """Hand the frontend an authorize URL instead of redirecting to it.

    A plain link would 401 once the 5 minute access cookie expired, with no
    apiFetch in the loop to refresh it silently.
    """
    redirect_uri = settings.notion_oauth_redirect_uri
    authorize_data = await oauth.notion.create_authorization_url(redirect_uri)
    # Stores the CSRF state in the session cookie, which authorize_redirect
    # would also do, but it returns the 302 this route is avoiding.
    await oauth.notion.save_authorize_data(
        request, redirect_uri=redirect_uri, **authorize_data
    )
    return AuthorizeUrlResponse(authorize_url=authorize_data["url"])


@router.get("/auth/oauth/notion/callback")
async def notion_callback(request: Request, db: Session = Depends(get_session)):
    """Exchange the code, store the grant, send the browser back to the app."""
    # Called by hand, not as a dependency: a 401 here is a JSON body, and a
    # browser navigation has to end on a page.
    try:
        user = get_current_user(request, db)
    except HTTPException:
        logger.warning("notion callback arrived without a valid session")
        return redirect_with_error("session")

    try:
        token = await oauth.notion.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning("notion oauth failed: {}", exc.error)
        return redirect_with_error("oauth")

    if not token.get("access_token") or not token.get("workspace_id"):
        logger.warning("notion oauth: unexpected token response shape")
        return redirect_with_error("token")

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
    return RedirectResponse(f"{settings.frontend_url}/dashboard/connections")


@router.get("/api/v1/me/notion", response_model=ConnectionStatus)
async def get_notion(row: NotionConnection = Depends(get_connection)):
    """The stored grant as the dashboard sees it."""
    return row


@router.delete("/api/v1/me/notion", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_notion(
    row: NotionConnection = Depends(get_connection),
    db: Session = Depends(get_session),
):
    """Revoke the grant on Notion's side, forget it, and drop the user's syncs.

    Every sync reads through this grant, so leaving them behind would leave
    rows that can never run. The ORM cascade takes their link rows with them;
    events already in iCloud stay, same as an Apple Calendar disconnect.
    """
    user_id = row.user_id
    repo = NotionConnectionRepo(db)
    repo.revoke(decrypt(row.access_token_encrypted))
    mapping_repo = SyncMappingRepo(db)
    for mapping in mapping_repo.list(user_id):
        mapping_repo.delete(mapping)
    repo.delete(row)
    db.commit()
    logger.info("notion disconnected for user {}", user_id)


@router.get(
    "/api/v1/me/notion/databases", response_model=list[NotionDatabaseOption]
)
async def list_notion_databases(repo: NotionPageRepo = Depends(get_notion_repo)):
    """The data sources the user ticked in Notion's consent picker."""
    with notion_errors():
        return repo.list_databases()
