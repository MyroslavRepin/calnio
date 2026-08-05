from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.base import Base

if TYPE_CHECKING:
    from backend.models.user import User

# Values `last_status` takes. "auth_error" is kept apart from "error" because
# only it disables the user: a rejected credential never fixes itself, and
# re-sending a bad app-specific password every interval risks locking the
# Apple ID.
STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_AUTH_ERROR = "auth_error"


class SyncSettings(Base):
    """A user's sync switch, its one setting, and how the last run went.

    One row per user, created on demand. No row means the user has never
    touched syncing, which reads exactly like disabled. `enabled` starts False:
    Calnio writes to somebody's calendar only after they ask for it.

    `due_date_property` is the Notion column read for dates. It has no default
    on purpose. Guessing "Due Date" would let a user turn syncing on, see a
    successful run, and get no events. The schema decides the name, so the
    user picks it.
    """

    __tablename__: str = "sync_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    due_date_property: Mapped[str | None] = mapped_column(String, nullable=True)

    # Outcome of the last run. NULL until the user has ever synced.
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String, nullable=True)

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="sync_settings")
