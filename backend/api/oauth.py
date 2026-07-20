import jwt
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.core.oauth import oauth
from backend.core.security import JWTService
from backend.deps.db import get_session
from backend.repo.user_repo import UserRepo

router = APIRouter()

jwt_service = JWTService(settings.jwt_secret)

# Both tokens ride in httpOnly cookies (never readable by JS).
# access_token  — sent to every route (path "/"), short-lived.
# refresh_tokens — sent only to /auth/* (path "/auth"), long-lived.
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
ACCESS_COOKIE_PATH = "/"
REFRESH_COOKIE_PATH = "/auth"
ACCESS_MAX_AGE = jwt_service.access_token_exp * 60  # minutes → seconds
REFRESH_MAX_AGE = jwt_service.refresh_token_exp * 60


def _set_cookie(response: Response, name: str, value: str, path: str, max_age: int) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=path,
    )


def _clear_cookie(response: Response, name: str, path: str) -> None:
    response.delete_cookie(
        name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=path,
    )


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    _set_cookie(response, ACCESS_COOKIE, access_token, ACCESS_COOKIE_PATH, ACCESS_MAX_AGE)
    _set_cookie(response, REFRESH_COOKIE, refresh_token, REFRESH_COOKIE_PATH, REFRESH_MAX_AGE)


def _clear_auth_cookies(response: Response) -> None:
    _clear_cookie(response, ACCESS_COOKIE, ACCESS_COOKIE_PATH)
    _clear_cookie(response, REFRESH_COOKIE, REFRESH_COOKIE_PATH)


@router.get("/auth/oauth/google/login")
async def oauth_google_login(request: Request):
    return await oauth.google.authorize_redirect(
        request, settings.google_oauth_redirect_uri
    )


@router.get("/auth/oauth/google/callback")
async def oauth_google_callback(request: Request, db: Session = Depends(get_session)):
    # authlib validates the `state` (CSRF) and exchanges the code. Any failure
    # here is a bounce back to the frontend with an error flag, never a 500.
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning("google oauth failed: {}", exc.error)
        return RedirectResponse(f"{settings.frontend_url}/?auth_error=oauth")

    info = token.get("userinfo")  # sub, email, name, picture
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

    # Both tokens land in httpOnly cookies; the browser sends them on every
    # subsequent request. No token in the URL.
    access_token, refresh_token = jwt_service.create_token_pair(str(user.id))
    response = RedirectResponse(f"{settings.frontend_url}/")
    _set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/auth/refresh")
async def refresh_tokens(request: Request):
    """Rotate both cookies off a valid refresh cookie.

    The frontend calls this on any 401. The tokens live only in httpOnly
    cookies — never sent in a body or returned in the response.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="no refresh cookie"
        )

    try:
        access_token, new_refresh_token = jwt_service.refresh(refresh_token)
    except jwt.InvalidTokenError:
        # Bad/expired refresh: clear stale cookies so the client stops retrying.
        response = JSONResponse(
            {"detail": "invalid or expired refresh token"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        _clear_auth_cookies(response)
        return response

    response = JSONResponse({"ok": True})
    _set_auth_cookies(response, access_token, new_refresh_token)
    return response


@router.post("/auth/logout")
async def logout():
    response = JSONResponse({"ok": True})
    _clear_auth_cookies(response)
    return response


@router.get("/auth/me")
async def get_me(request: Request, db: Session = Depends(get_session)):
    # Access token comes from the httpOnly cookie the browser sends automatically.
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing access cookie"
        )

    try:
        user_id = jwt_service.verify(token, expected_type="access")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        )

    user = UserRepo(db).get(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )

    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
