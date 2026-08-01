from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.notion import _revoke
from backend.api.oauth import _clear_auth_cookies
from backend.core.crypto import decrypt
from backend.core.logging import logger
from backend.core.scheduler import scheduler
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.notion_connection_repo import NotionConnectionRepo
from backend.repo.user_repo import UserRepo

router = APIRouter(prefix="/api/v1", tags=["account"])

BASE = "/me"


class DeleteAccountRequest(BaseModel):
    """Typed-back confirmation.

    Checked on the server rather than trusted from the UI: the auth cookie is
    SameSite=None (the Vite dev origin is cross-site), so CORS preflight is the
    only thing standing between this route and a stray cross-origin DELETE.
    """

    email: str


def _cancel_queued_sync(user_id: int) -> None:
    """Drop a one-off sync job that has not fired yet.

    Same job id api/sync.py queues under. A run already in flight is not
    stopped: it holds its own session, and its next commit fails against the
    deleted rows, which sync_user logs and run_all_users contains.
    """
    job_id = f"sync-user-{user_id}"
    if scheduler.get_job(job_id) is not None:
        scheduler.remove_job(job_id)
        logger.info("queued sync cancelled for user {}", user_id)


@router.delete(BASE, status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    body: DeleteAccountRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Delete the account and every row belonging to it.

    Deliberately does not touch iCloud. Events Calnio pushed are the user's
    data and stay in their calendar, same as disconnecting Apple Calendar —
    but Calnio can no longer remove them afterwards, which the UI says out loud.

    The Notion grant is the opposite case and is revoked: it belongs to Calnio,
    and leaving it live would keep the integration listed in the user's Notion
    connections after they asked us to go away.
    """
    if body.email.strip().lower() != user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="that is not the email you are signed in with",
        )

    user_id = user.id
    _cancel_queued_sync(user_id)

    connection = NotionConnectionRepo(db).get(user_id)
    if connection is not None:
        _revoke(decrypt(connection.access_token_encrypted))

    UserRepo(db).delete(user)
    db.commit()

    # The tokens are self-contained JWTs, so they stay signed-valid until they
    # expire; get_current_user would 401 on the missing row anyway, but leaving
    # dead cookies on the browser has no upside.
    _clear_auth_cookies(response)
    logger.info("account deleted for user {}", user_id)
