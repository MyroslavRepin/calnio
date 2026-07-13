from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.oauth import oauth
from backend.core.security import JWTService
from backend.deps.db import get_session
from backend.repo.user_repo import UserRepo

router = APIRouter()


@router.get("/auth/oauth/google/login")
async def oauth_google_login(request: Request):
    return await oauth.google.authorize_redirect(
        request, settings.google_oauth_redirect_uri
    )


@router.get("/auth/oauth/google/callback")
async def oauth_google_callback(request: Request, db: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    info = token["userinfo"]  # sub, email, name, picture

    # Repos build
    user_repo = UserRepo(db)
    jwt_service = JWTService(settings.jwt_secret)
    user = user_repo.get_or_create_user_oauth(
        "google",
        info["sub"],
        email=info["email"],
        name=info.get("name"),
        picture=info.get("picture"),
    )
    db.commit()

    access_token = jwt_service.create_access_token(str(user.id))
    refresh_token = jwt_service.create_refresh_token(str(user.id))

    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "access_token": access_token,
        "refresh_token": refresh_token,
        # Debug only — decoded payloads to eyeball the claims; remove later.
        "access_payload": jwt_service.decode(access_token, expected_type="access"),
        "refresh_payload": jwt_service.decode(refresh_token, expected_type="refresh"),
    }
