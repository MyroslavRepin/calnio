from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt
from backend.core.logging import logger
from backend.deps.auth import get_current_user
from backend.deps.caldav import get_credential, icloud_credentials, icloud_errors
from backend.deps.db import get_session
from backend.deps.mapping import (
    calendar_name_for,
    date_property_names,
    get_mapping,
    mapping_eligible,
    mapping_status,
    pick_date_property,
)
from backend.deps.notion import get_notion_repo, notion_errors
from backend.deps.sync import queue_run
from backend.models.caldav_credential import CaldavCredential
from backend.models.sync_mapping import SyncMapping
from backend.models.synced_event import SyncedEvent
from backend.models.user import User
from backend.repo.caldav import CalDavAccountRepo, CalDavEventRepo
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.notion import NotionPageRepo
from backend.repo.sync_mapping import SyncMappingRepo
from backend.repo.sync_settings import SyncSettingsRepo
from backend.schemas.sync_mapping import (
    CreateMappingRequest,
    MappingStatus,
    UpdateMappingRequest,
)

router = APIRouter(tags=["sync-mappings"])


@router.get("/api/v1/me/syncs", response_model=list[MappingStatus])
async def list_syncs(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
):
    """Every sync this user has set up. Local rows only, no third party call."""
    rows = SyncMappingRepo(db).list(user.id)
    return [mapping_status(row) for row in rows]


@router.post(
    "/api/v1/me/syncs",
    response_model=list[MappingStatus],
    status_code=status.HTTP_201_CREATED,
)
async def create_syncs(
    body: CreateMappingRequest,
    user: User = Depends(get_current_user),
    repo: NotionPageRepo = Depends(get_notion_repo),
    credential: CaldavCredential = Depends(get_credential),
    db: Session = Depends(get_session),
):
    """Start syncing the given databases, configured and switched on.

    One call does what used to be five decisions: the date column is inferred,
    a calendar named after the database is reused or created, the sync is
    enabled, and the master switch goes on. Everything stays editable on the
    sync afterwards, so nothing here is a one-way door.

    A database whose date column cannot be guessed is still created, just not
    enabled, and its card asks the one question that is left.
    """
    mapping_repo = SyncMappingRepo(db)

    for data_source_id in body.data_source_ids:
        if mapping_repo.get_by_source(user.id, data_source_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="one of those databases already syncs to a calendar",
            )

    # One retrieve per database proves it is still shared with us and hands back
    # both the authoritative title and the column schema, so the date column is
    # guessed without a second round trip.
    with notion_errors():
        databases = [
            repo.get_database(data_source_id)
            for data_source_id in body.data_source_ids
        ]

    # Listed once for the whole batch, because iCloud is slow to answer it.
    account = CalDavAccountRepo(*icloud_credentials(credential))
    with icloud_errors():
        calendars = account.list_calendars()

    created: list[SyncMapping] = []
    for database in databases:
        mapping = mapping_repo.create(user.id, database.id, database.title)

        date_names = [
            name
            for name, prop in database.properties.items()
            if prop.get("type") == "date"
        ]
        guess = pick_date_property(date_names)
        if guess is not None:
            mapping_repo.set_date_property(mapping, guess)

        # Reuse a calendar the user already has under that name before making
        # another one, so running this twice does not litter their account. A
        # Reminders list answers to a name but refuses events, so it never wins.
        wanted = calendar_name_for(database.title)
        match = next(
            (
                calendar
                for calendar in calendars
                if calendar.name.lower() == wanted.lower()
                and "reminder" not in calendar.name.lower()
            ),
            None,
        )
        if match is None:
            with icloud_errors():
                match = account.create_calendar(wanted)
            calendars.append(match)  # a later database of the same name reuses it
        mapping_repo.set_calendar(mapping, match.url, match.name)

        # Nothing to ask about, so it runs. A mapping missing its column stays
        # off until the user answers that one question.
        if mapping_eligible(mapping):
            mapping.enabled = True
        created.append(mapping)

    # The master switch is a pause button, not a gate. Leaving it off here is
    # what made people set everything up and see nothing happen.
    settings_row = SyncSettingsRepo(db).get_or_create(user.id)
    runnable = any(mapping.enabled for mapping in created)
    if runnable and not settings_row.enabled:
        settings_row.enabled = True

    db.commit()
    logger.info(
        "syncs created for user {}: {}",
        user.id,
        ", ".join(database.title for database in databases),
    )

    # After the commit: a queued job opens its own session and would otherwise
    # race the transaction that enabled these syncs.
    if runnable:
        queue_run(user.id)

    return [mapping_status(mapping) for mapping in created]


@router.get(
    "/api/v1/me/syncs/{mapping_id}/date-properties", response_model=list[str]
)
async def list_sync_date_properties(
    mapping: SyncMapping = Depends(get_mapping),
    repo: NotionPageRepo = Depends(get_notion_repo),
):
    """Candidates for this sync's date column, empty if the database has none."""
    return date_property_names(mapping, repo)


@router.put("/api/v1/me/syncs/{mapping_id}", response_model=MappingStatus)
async def configure_sync(
    body: UpdateMappingRequest,
    mapping: SyncMapping = Depends(get_mapping),
    repo: NotionPageRepo = Depends(get_notion_repo),
    db: Session = Depends(get_session),
):
    """Set this sync's date column, its calendar, its switch, or any of them."""
    mapping_repo = SyncMappingRepo(db)

    if body.due_date_property is not None:
        # Checked against the live schema: a name that is not a date column
        # would sync cleanly and produce nothing at all.
        if body.due_date_property not in date_property_names(mapping, repo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="that is not a date property on this database",
            )
        mapping_repo.set_date_property(mapping, body.due_date_property)

    if body.calendar_url is not None:
        # Loaded here rather than injected, so changing only the date column
        # still works for somebody who has disconnected Apple Calendar.
        credential = CaldavCredentialRepo(db).get(mapping.user_id)
        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="connect apple calendar first",
            )

        with icloud_errors():
            calendars = CalDavAccountRepo(
                *icloud_credentials(credential)
            ).list_calendars()

        # Never store a URL the account cannot see, whoever handed it to us. The
        # matching row also gives us the display name, straight from iCloud.
        matched = next(
            (calendar for calendar in calendars if calendar.url == body.calendar_url),
            None,
        )
        if matched is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="unknown calendar"
            )
        # A Reminders list answers CalDAV but refuses events, so a sync pointed
        # at one fails every run with nothing the user could fix.
        if "reminder" in matched.name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="that is a reminders list, it cannot hold events",
            )
        mapping_repo.set_calendar(mapping, matched.url, matched.name)

    turned_on = False
    if body.enabled is not None:
        if body.enabled and not mapping_eligible(mapping):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="pick a date column and a calendar before turning this on",
            )
        turned_on = body.enabled and not mapping.enabled
        mapping.enabled = body.enabled

    db.commit()

    # After the commit: a queued job opens its own session and would otherwise
    # race the transaction that enabled the mapping.
    if turned_on:
        queue_run(mapping.user_id)

    return mapping_status(mapping)


@router.delete(
    "/api/v1/me/syncs/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_sync(
    mapping: SyncMapping = Depends(get_mapping),
    db: Session = Depends(get_session),
):
    """Remove a sync and the events it pushed.

    The events go, unlike an Apple Calendar disconnect which leaves them: a
    disconnect keeps the link rows, so reconnecting reconciles cleanly, but
    deleting the sync destroys them. Events left behind would be unreachable
    forever, and re-adding the same database would answer iCloud 412 duplicate
    on every page. They can only be cleaned up while the hrefs are still known.
    """
    mapping_id = mapping.id
    user_id = mapping.user_id
    rows = db.scalars(
        select(SyncedEvent).where(SyncedEvent.mapping_id == mapping_id)
    ).all()

    # No credential means Apple was disconnected, and the events are already
    # beyond reach. The sync still goes, otherwise a stale row is unremovable.
    credential = CaldavCredentialRepo(db).get(user_id)

    if credential is not None and mapping.calendar_url is not None and rows:
        # iCloud unreachable is a 502 and the mapping survives, so the user can
        # retry rather than being left with a half-deleted sync.
        with icloud_errors():
            calendar = CalDavEventRepo(
                caldav_url=settings.caldav_url,
                username=credential.icloud_email,
                password=decrypt(credential.password_encrypted),
                calendar_url=mapping.calendar_url,
            )
            for row in rows:
                calendar.delete_by_href(row.caldav_href)

    SyncMappingRepo(db).delete(mapping)
    db.commit()
    logger.info(
        "sync {} deleted for user {}: {} events removed",
        mapping_id,
        user_id,
        len(rows),
    )
