from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    sync_enabled: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )
