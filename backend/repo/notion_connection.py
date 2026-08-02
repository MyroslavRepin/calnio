from datetime import datetime, timezone

import httpx
from authlib.integrations.base_client import OAuthError
from authlib.integrations.httpx_client import OAuth2Client
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.core.oauth import NOTION_REVOKE_URL
from backend.models.notion_connection import NotionConnection


class NotionConnectionRepo:
    """Notion grant persistence. Caller owns the session and the commit.

    Stores and returns the access token as ciphertext only. Encryption happens
    in backend/core/crypto.py, never here.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> NotionConnection | None:
        return self.db.scalar(
            select(NotionConnection).where(NotionConnection.user_id == user_id)
        )

    def upsert(
        self,
        user_id: int,
        access_token_encrypted: str,
        *,
        bot_id: str,
        workspace_id: str,
        workspace_name: str | None,
        workspace_icon: str | None,
    ) -> tuple[NotionConnection, bool]:
        """Create or replace the user's grant. Returns (row, created).

        Reconnecting to a *different* workspace clears the selected data
        source — an id from the old workspace means nothing under the new one.
        Re-authorizing the same workspace keeps the selection, which is what
        makes the "re-open Notion's picker to share more databases" flow
        non-destructive.
        """
        now = datetime.now(timezone.utc)
        row = self.get(user_id)

        if row is None:
            row = NotionConnection(
                user_id=user_id,
                access_token_encrypted=access_token_encrypted,
                bot_id=bot_id,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                workspace_icon=workspace_icon,
                last_verified_at=now,
            )
            self.db.add(row)
            self.db.flush()  # assign id before the caller serializes the row
            return row, True

        if row.workspace_id != workspace_id:
            row.data_source_id = None
            row.data_source_name = None
        row.access_token_encrypted = access_token_encrypted
        row.bot_id = bot_id
        row.workspace_id = workspace_id
        row.workspace_name = workspace_name
        row.workspace_icon = workspace_icon
        row.last_verified_at = now
        return row, False

    def set_data_source(
        self, row: NotionConnection, data_source_id: str, data_source_name: str
    ) -> None:
        row.data_source_id = data_source_id
        row.data_source_name = data_source_name

    def delete(self, row: NotionConnection) -> None:
        self.db.delete(row)

    def revoke(self, access_token: str) -> None:
        """Drop the grant on Notion's side. Best effort, never blocks a disconnect."""
        client = OAuth2Client(
            settings.notion_oauth_client_id, settings.notion_oauth_client_secret
        )
        try:
            client.revoke_token(
                NOTION_REVOKE_URL, token=access_token, token_type_hint="access_token"
            )
        except (OAuthError, httpx.HTTPError) as exc:
            logger.warning("notion revoke failed, forgetting the grant anyway: {}", exc)
