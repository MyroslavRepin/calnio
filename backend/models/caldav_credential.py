from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.base import Base

if TYPE_CHECKING:
    from backend.models.user import User


class CaldavCredential(Base):
    """A user's iCloud CalDAV credential + the calendar they sync into.

    One row per user (unique `user_id`) — multi-account is not a feature.
    A row only exists if the credential authenticated against iCloud at least
    once, so "row exists" means "these credentials worked".
    """

    __tablename__: str = "caldav_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    icloud_email: Mapped[str] = mapped_column(String)

    password_encrypted: Mapped[str] = mapped_column(String)

    calendar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="caldav_credential")
