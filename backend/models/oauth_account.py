from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.base import Base

if TYPE_CHECKING:
    from backend.models.user import User


class OAuthAccount(Base):
    """One provider link for a user. A user can have several (google, apple, ...)."""

    __tablename__: str = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_account_id", name="uq_provider_account"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    provider: Mapped[str] = mapped_column(String)  # "google"
    provider_account_id: Mapped[str] = mapped_column(String)  # Google `sub` — stable id

    # Google API tokens — only filled if we call Google APIs; nullable otherwise.
    access_token: Mapped[str | None] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
