from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.deps.notion import notion_errors
from backend.models.sync_mapping import SyncMapping
from backend.models.user import User
from backend.repo.notion import NotionPageRepo
from backend.repo.sync_mapping import SyncMappingRepo
from backend.schemas.sync_mapping import MappingStatus


def get_mapping(
    mapping_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SyncMapping:
    """One of the current user's syncs, or 404.

    Scoped to the signed-in user, so somebody else's id reads as missing rather
    than as forbidden, which tells the caller nothing about what exists.
    """
    row = SyncMappingRepo(db).get(user.id, mapping_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such sync")
    return row


def date_property_names(mapping: SyncMapping, notion: NotionPageRepo) -> list[str]:
    """Date column names on this sync's data source, in schema order."""
    with notion_errors():
        database = notion.get_database(mapping.data_source_id)
    return [
        name for name, prop in database.properties.items() if prop.get("type") == "date"
    ]


# Column names worth guessing, best first. Matched case-insensitively against
# the database's date columns so a user who calls it "Deadline" is served too.
PREFERRED_DATE_NAMES = (
    "due date",
    "due",
    "deadline",
    "date",
    "when",
    "start date",
)


def pick_date_property(names: list[str]) -> str | None:
    """Guess which date column a user meant, or None when it is ambiguous.

    One date column is not a decision, it is the only answer, so asking for it
    is a step that loses people. Several columns are a real choice, but a name
    Notion users reach for anyway resolves most of those too.
    """
    if not names:
        return None
    if len(names) == 1:
        return names[0]

    lowered = {name.lower(): name for name in names}
    for candidate in PREFERRED_DATE_NAMES:
        if candidate in lowered:
            return lowered[candidate]
    return None


def calendar_name_for(title: str) -> str:
    """The calendar name a database gets, within what CalDAV will accept."""
    cleaned = title.strip()
    if not cleaned:
        return "Calnio"
    return cleaned[:64]


def mapping_eligible(mapping: SyncMapping) -> bool:
    """Whether this sync has everything a run needs."""
    return mapping.due_date_property is not None and mapping.calendar_url is not None


def mapping_status(mapping: SyncMapping) -> MappingStatus:
    """The row plus the eligibility the client needs to render its toggle."""
    return MappingStatus(
        id=mapping.id,
        data_source_id=mapping.data_source_id,
        data_source_name=mapping.data_source_name,
        due_date_property=mapping.due_date_property,
        calendar_url=mapping.calendar_url,
        calendar_name=mapping.calendar_name,
        enabled=mapping.enabled,
        eligible=mapping_eligible(mapping),
        last_run_at=mapping.last_run_at,
        last_status=mapping.last_status,
    )
