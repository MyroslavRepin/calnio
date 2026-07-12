from fastapi import APIRouter, Request

from backend.core.config import settings
from backend.core.oauth import oauth

router = APIRouter()


@router.get("/auth/oauth/google/login")
async def oauth_google_login(request: Request):
    return await oauth.google.authorize_redirect(
        request, settings.google_oauth_redirect_uri
    )


@router.get("/auth/oauth/google/callback")
async def oauth_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token["userinfo"]  # sub, email, name, picture
    return {
        "sub": user["sub"],
        "email": user["email"],
        "name": user.get("name"),
        "picture": user.get("picture"),
        "access_token": token["access_token"],
    }
