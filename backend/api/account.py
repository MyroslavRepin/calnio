from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.core.crypto import decrypt
from backend.core.logging import logger
from backend.core.scheduler import scheduler
from backend.deps.auth import clear_auth_cookies, get_current_user
from backend.deps.db import get_session
from backend.models.user import User
from backend.repo.notion_connection import NotionConnectionRepo
from backend.repo.user import UserRepo
from backend.schemas.account import DeleteAccountRequest

router = APIRouter(tags=["account"])


def cancel_queued_sync(user_id: int) -> None:
    """Drop a one-off sync job that has not fired yet.

    A run already in flight is not stopped: it holds its own session, and its
    next commit fails against the deleted rows, which sync_user logs and
    run_all_users contains.
    """
    job_id = f"sync-user-{user_id}"
    if scheduler.get_job(job_id) is not None:
        scheduler.remove_job(job_id)


@router.delete("/api/v1/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    body: DeleteAccountRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Delete the account and every row belonging to it.

    iCloud is deliberately untouched: events Calnio pushed are the user's data
    and stay in their calendar. The Notion grant is the opposite case, it
    belongs to Calnio and is revoked.
    """
    if body.email.strip().lower() != user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="that is not the email you are signed in with",
        )

    user_id = user.id
    cancel_queued_sync(user_id)

    notion_connections = NotionConnectionRepo(db)
    connection = notion_connections.get(user_id)
    if connection is not None:
        notion_connections.revoke(decrypt(connection.access_token_encrypted))

    UserRepo(db).delete(user)
    db.commit()

    clear_auth_cookies(response)
    logger.info("account deleted for user {}", user_id)
