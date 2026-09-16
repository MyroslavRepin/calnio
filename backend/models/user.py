from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.base import Base
from backend.models.caldav_credential import CaldavCredential
from backend.models.notion_connection import NotionConnection
from backend.models.oauth_account import OAuthAccount
from backend.models.sync_mapping import SyncMapping
from backend.models.sync_settings import SyncSettings


class User(Base):
    """App identity: one row per person, independent of how they logged in."""

    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    picture: Mapped[str | None] = mapped_column(String, nullable=True)

    # Sees the admin dashboard, which reads every account's numbers. Granted by
    # hand in the database: there is no route that hands it out, because a
    # route that grants admin is a route that can be tricked into it.
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    row_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    row_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    caldav_credential: Mapped["CaldavCredential | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    notion_connection: Mapped["NotionConnection | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    sync_settings: Mapped["SyncSettings | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    sync_mappings: Mapped[list["SyncMapping"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
