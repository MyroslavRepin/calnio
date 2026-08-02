import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import jwt_service
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.user import UserRepo


def get_current_user(request: Request, db: Session = Depends(get_session)) -> User:
    """Authenticate the request from the access cookie, or 401."""
    token = request.cookies.get("access_token")
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

    # The row, not just the id, so a deleted account cannot act on a live token.
    user = UserRepo(db).get(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )

    return user


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Write both httpOnly auth cookies. The refresh one is scoped to /auth."""
    response.set_cookie(
        "access_token",
        access_token,
        max_age=jwt_service.access_token_exp * 60,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=jwt_service.refresh_token_exp * 60,
        path="/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    """Drop both auth cookies. Paths must match the ones they were set with."""
    response.delete_cookie(
        "access_token",
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        "refresh_token",
        path="/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
