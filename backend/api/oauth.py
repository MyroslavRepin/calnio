import jwt
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.oauth import oauth
from backend.core.security import JWTService
from backend.deps.db import get_session
from backend.repo.user_repo import UserRepo

router = APIRouter()

jwt_service = JWTService(settings.jwt_secret)


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


@router.get("/auth/me")
async def get_me(request: Request, db: Session = Depends(get_session)):
    # Everything under the hood: pull Bearer token, validate, load user.
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = jwt_service.verify(token, expected_type="access")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
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


@router.post("/auth/refresh")
async def refresh_tokens(refresh_token: str = Body(..., embed=True)):
    try:
        access_token, new_refresh_token = jwt_service.refresh(refresh_token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired refresh token",
        )
    return {"access_token": access_token, "refresh_token": new_refresh_token}
