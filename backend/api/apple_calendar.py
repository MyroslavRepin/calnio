from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import encrypt
from backend.core.logging import logger
from backend.deps.auth import get_current_user
from backend.deps.caldav import get_credential, icloud_credentials, icloud_errors
from backend.deps.db import get_session
from backend.models.caldav_credential import CaldavCredential
from backend.models.user import User
from backend.repo.caldav_credential import CaldavCredentialRepo
from backend.repo.caldav import create_calendar, list_calendars
from backend.schemas.apple_calendar import (
    ConnectionStatus,
    ConnectRequest,
    ConnectResponse,
    CreateCalendarRequest,
    SelectCalendarRequest,
)
from backend.schemas.caldav_calendar import CalDavCalendar

router = APIRouter(tags=["apple-calendar"])


@router.put("/api/v1/me/apple-calendar", response_model=ConnectResponse)
async def connect_apple_calendar(
    body: ConnectRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Verify an iCloud app-specific password, then store it encrypted.

    Verification comes first, so a stored row always means these credentials
    worked at least once.
    """
    with icloud_errors():
        calendars = list_calendars(
            settings.caldav_url, body.icloud_email, body.app_specific_password
        )

    row, created = CaldavCredentialRepo(db).upsert(
        user.id, body.icloud_email, encrypt(body.app_specific_password)
    )
    db.commit()

    logger.info("apple calendar connected for user {}", user.id)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return ConnectResponse(
        icloud_email=row.icloud_email,
        calendar_url=row.calendar_url,
        last_verified_at=row.last_verified_at,
        calendars=calendars,
    )


@router.get("/api/v1/me/apple-calendar", response_model=ConnectionStatus)
async def get_apple_calendar(row: CaldavCredential = Depends(get_credential)):
    """The stored credential as the dashboard sees it."""
    return row


@router.delete(
    "/api/v1/me/apple-calendar", status_code=status.HTTP_204_NO_CONTENT
)
async def disconnect_apple_calendar(
    row: CaldavCredential = Depends(get_credential),
    db: Session = Depends(get_session),
):
    """Forget the credential, leaving everything in iCloud untouched."""
    user_id = row.user_id
    CaldavCredentialRepo(db).delete(row)
    db.commit()
    logger.info("apple calendar disconnected for user {}", user_id)


@router.get(
    "/api/v1/me/apple-calendar/calendars", response_model=list[CalDavCalendar]
)
async def list_apple_calendars(row: CaldavCredential = Depends(get_credential)):
    """Every calendar on the connected iCloud account."""
    with icloud_errors():
        return list_calendars(*icloud_credentials(row))


@router.post(
    "/api/v1/me/apple-calendar/calendars",
    response_model=CalDavCalendar,
    status_code=status.HTTP_201_CREATED,
)
async def create_apple_calendar(
    body: CreateCalendarRequest,
    row: CaldavCredential = Depends(get_credential),
):
    """Create a calendar in the user's iCloud account, without selecting it."""
    with icloud_errors():
        return create_calendar(*icloud_credentials(row), body.name)


@router.put("/api/v1/me/apple-calendar/calendar", response_model=ConnectionStatus)
async def select_apple_calendar(
    body: SelectCalendarRequest,
    row: CaldavCredential = Depends(get_credential),
    db: Session = Depends(get_session),
):
    """Point syncing at one of the user's calendars."""
    with icloud_errors():
        calendars = list_calendars(*icloud_credentials(row))

    # Never store a URL the account cannot see, whoever handed it to us.
    if not any(calendar.url == body.calendar_url for calendar in calendars):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="unknown calendar"
        )

    CaldavCredentialRepo(db).set_calendar_url(row, body.calendar_url)
    db.commit()
    return row
