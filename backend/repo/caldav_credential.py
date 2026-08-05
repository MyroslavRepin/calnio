from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.caldav_credential import CaldavCredential


class CaldavCredentialRepo:
    """iCloud credential persistence. Caller owns the session and the commit.

    Stores and returns the password as ciphertext only. Encryption happens in
    backend/core/crypto.py, never here.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> CaldavCredential | None:
        return self.db.scalar(
            select(CaldavCredential).where(CaldavCredential.user_id == user_id)
        )

    def upsert(
        self, user_id: int, icloud_email: str, password_encrypted: str
    ) -> tuple[CaldavCredential, bool]:
        """Create or replace the user's credential. Returns (row, created).

        Replacing an account clears calendar_url, since a URL from the old
        account is meaningless under new credentials.
        """
        now = datetime.now(timezone.utc)
        row = self.get(user_id)

        if row is None:
            row = CaldavCredential(
                user_id=user_id,
                icloud_email=icloud_email,
                password_encrypted=password_encrypted,
                last_verified_at=now,
            )
            self.db.add(row)
            self.db.flush()  # assign id before the caller serializes the row
            return row, True

        if row.icloud_email != icloud_email:
            row.calendar_url = None
        row.icloud_email = icloud_email
        row.password_encrypted = password_encrypted
        row.last_verified_at = now
        return row, False

    def set_calendar_url(self, row: CaldavCredential, calendar_url: str) -> None:
        row.calendar_url = calendar_url

    def delete(self, row: CaldavCredential) -> None:
        self.db.delete(row)
