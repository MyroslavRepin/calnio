from sqlalchemy.orm import Mapped, mapped_column

from backend.core.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    sync_enabled: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )

    # False from startup until a graceful shutdown. Still False at the next
    # startup means the process died without one (OOM, power loss, kill -9),
    # which Docker's restart would otherwise hide.
    stopped_cleanly: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )
