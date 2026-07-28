from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.base import Base

if TYPE_CHECKING:
    from backend.models.user import User


class NotionConnection(Base):
    """A user's Notion workspace grant + the data source they sync from.

    One row per user (unique `user_id`) — multi-workspace is not a feature.
    A row only exists once Notion minted a token for us, so "row exists" means
    "the grant worked". `data_source_id` staying NULL means the user authorized
    the workspace but has not picked a database yet — the two-stage state the
    dashboard renders as "connected" vs "configured".

    Distinct from `oauth_accounts`, which answers "who is this user" (a login
    identity keyed by Google `sub`, N per user). This answers "what does this
    user connect to" — a resource grant, 1 per user.
    """

    __tablename__: str = "notion_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    access_token_encrypted: Mapped[str] = mapped_column(String)

    # Straight from Notion's token response. `bot_id` identifies this specific
    # grant — kept for the revoke call and for support questions.
    bot_id: Mapped[str] = mapped_column(String)
    workspace_id: Mapped[str] = mapped_column(String)
    workspace_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # Either an image URL or a literal emoji — Notion sends both shapes.
    workspace_icon: Mapped[str | None] = mapped_column(String, nullable=True)

    # NULL until the user picks a database. API 2025-09-03: pages and schema
    # live on the *data source*, not the database container, so the id stored
    # here is the one `data_sources.query` takes.
    data_source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    data_source_name: Mapped[str | None] = mapped_column(String, nullable=True)

    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="notion_connection")
