import jwt
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.core.oauth import oauth
from backend.core.security import jwt_service
from backend.deps.auth import clear_auth_cookies, get_current_user, set_auth_cookies
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.user import UserRepo
from backend.schemas.auth import MeResponse

router = APIRouter(tags=["auth"])


@router.get("/auth/oauth/google/login")
async def google_login(request: Request):
    """Send the browser to Google's consent screen."""
    return await oauth.google.authorize_redirect(
        request, settings.google_oauth_redirect_uri
    )


@router.get("/auth/oauth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_session)):
    """Exchange Google's code, mint tokens, land on the dashboard."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning("google oauth failed: {}", exc.error)
        return RedirectResponse(f"{settings.frontend_url}/?auth_error=oauth")

    info = token.get("userinfo")
    if not info or not info.get("sub"):
        logger.warning("google oauth: missing userinfo in token response")
        return RedirectResponse(f"{settings.frontend_url}/?auth_error=userinfo")

    user = UserRepo(db).get_or_create_user_oauth(
        "google",
        info["sub"],
        email=info["email"],
        name=info.get("name"),
        picture=info.get("picture"),
    )
    db.commit()

    access_token, refresh_token = jwt_service.create_token_pair(str(user.id))
    response = RedirectResponse(f"{settings.frontend_url}/dashboard")
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/auth/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_tokens(request: Request, response: Response):
    """Rotate both cookies off a valid refresh cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="no refresh cookie"
        )

    try:
        access_token, new_refresh_token = jwt_service.refresh(refresh_token)
    except jwt.InvalidTokenError:
        # Raising would discard the injected response, so the stale cookies are
        # cleared on a response built here instead.
        expired = JSONResponse(
            {"detail": "invalid or expired refresh token"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        clear_auth_cookies(expired)
        return expired

    set_auth_cookies(response, access_token, new_refresh_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """Clear both auth cookies."""
    clear_auth_cookies(response)


@router.get("/auth/me", response_model=MeResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Return the signed-in user's profile."""
    return user
