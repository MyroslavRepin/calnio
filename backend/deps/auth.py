import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import JWTService
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.user_repo import UserRepo

# Name of the httpOnly cookie carrying the access token (set in api/oauth.py).
ACCESS_COOKIE = "access_token"

jwt_service = JWTService(settings.jwt_secret)


def get_current_user(
    request: Request, db: Session = Depends(get_session)
) -> User:
    """Authenticate the request from the access cookie, or 401.

    The token rides in an httpOnly cookie the browser sends automatically — JS
    never holds it, so there is no Authorization header to read.

    Loads the user row (not just the id) so a deleted account cannot keep
    acting on a still-valid token.
    """
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

    return user
