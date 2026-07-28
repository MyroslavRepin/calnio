from fastapi import APIRouter, Depends, Request, Response

from backend.deps.auth import get_current_user
from backend.models.user import User

router = APIRouter(tags=["user-settings"])


@router.get("/api/user")
def delete_user(user: User = Depends(get_current_user)):
    return user.email
