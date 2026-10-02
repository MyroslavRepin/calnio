from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.orm import Session

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


class DatabaseRepo:
    """The database's schema revision against the one this build ships."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def current_revision(self) -> str | None:
        """The migration the database was last upgraded to."""
        return MigrationContext.configure(self.db.connection()).get_current_revision()

    def head_revision(self) -> str | None:
        """The newest migration in this build."""
        return ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_current_head()
