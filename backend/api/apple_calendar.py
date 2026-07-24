from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

import caldav.lib.error as caldav_error
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt, encrypt
from backend.core.logging import logger
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.caldav_credential import CaldavCredential
from backend.models.user import User
from backend.repo.caldav_credential_repo import CaldavCredentialRepo
from backend.repo.caldav_repo import create_calendar, list_calendars
from backend.schemas.caldav_calendar import CalDavCalendar

# Transport-level failures (DNS, TLS, timeouts) surface as the HTTP library's
# exception, not a DAVError. caldav 3.x prefers niquests and falls back to
# requests — mirror that choice so both installs are covered.
try:
    from niquests.exceptions import RequestException
except ImportError:  # pragma: no cover
    from requests.exceptions import RequestException

router = APIRouter(prefix="/api/v1", tags=["apple-calendar"])

BASE = "/me/apple-calendar"

DEFAULT_CALENDAR_NAME = "Calnio"


class ConnectRequest(BaseModel):
    icloud_email: str
    app_specific_password: str = Field(min_length=1)


class CreateCalendarRequest(BaseModel):
    name: str = Field(default=DEFAULT_CALENDAR_NAME, min_length=1, max_length=64)


class SelectCalendarRequest(BaseModel):
    calendar_url: str


class ConnectionStatus(BaseModel):
    """What the dashboard is allowed to see. Never carries the password."""

    connected: bool
    icloud_email: str
    calendar_url: str | None
    last_verified_at: datetime | None


class ConnectResponse(ConnectionStatus):
    # Returned inline so the setup wizard can render the calendar picker
    # without a second (slow) round trip to iCloud.
    calendars: list[CalDavCalendar]


def _status(row: CaldavCredential) -> ConnectionStatus:
    return ConnectionStatus(
        connected=True,
        icloud_email=row.icloud_email,
        calendar_url=row.calendar_url,
        last_verified_at=row.last_verified_at,
    )


@contextmanager
def _icloud_errors() -> Iterator[None]:
    """Map CalDAV failures onto HTTP status codes.

    Never 401 — the frontend's apiFetch auto-refreshes and retries on 401,
    which would resubmit a wrong password to Apple and risk locking the
    Apple ID. iCloud rejecting a credential is a 400.

    Raw exception text is logged, never returned: it can carry request URLs
    and headers.
    """
    try:
        yield
    except caldav_error.AuthorizationError as exc:
        logger.warning("icloud rejected credentials: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="icloud rejected these credentials",
        )
    except caldav_error.MkcalendarError as exc:
        logger.warning("icloud calendar creation failed: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="could not create the calendar",
        )
    except (caldav_error.DAVError, RequestException) as exc:
        logger.error("icloud unreachable: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="could not reach icloud, try again",
        )


def get_credential(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
) -> CaldavCredential:
    """The current user's stored credential, or 404."""
    row = CaldavCredentialRepo(db).get(user.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no apple calendar connection",
        )
    return row


@router.put(BASE, response_model=ConnectResponse)
async def connect_apple_calendar(
    body: ConnectRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Verify an iCloud app-specific password, then store it encrypted.

    Verification comes first, so a stored row always means "these credentials
    worked at least once" — the dashboard can show a connected state honestly.
    """
    with _icloud_errors():
        calendars = list_calendars(
            settings.caldav_url, body.icloud_email, body.app_specific_password
        )

    row, created = CaldavCredentialRepo(db).upsert(
        user.id, body.icloud_email, encrypt(body.app_specific_password)
    )
    db.commit()

    logger.info("apple calendar connected for user {}", user.id)
    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return ConnectResponse(**_status(row).model_dump(), calendars=calendars)


@router.get(BASE, response_model=ConnectionStatus)
async def get_apple_calendar(row: CaldavCredential = Depends(get_credential)):
    return _status(row)


@router.delete(BASE, status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_apple_calendar(
    row: CaldavCredential = Depends(get_credential),
    db: Session = Depends(get_session),
):
    """Forget the credential.

    Deliberately does not touch iCloud: events Calnio already pushed stay in
    the user's calendar, and a calendar Calnio created is left alone. Cleaning
    those up needs per-user sync state, which does not exist yet.
    """
    user_id = row.user_id
    CaldavCredentialRepo(db).delete(row)
    db.commit()
    logger.info("apple calendar disconnected for user {}", user_id)


@router.get(f"{BASE}/calendars", response_model=list[CalDavCalendar])
async def list_apple_calendars(row: CaldavCredential = Depends(get_credential)):
    with _icloud_errors():
        return list_calendars(
            settings.caldav_url, row.icloud_email, decrypt(row.password_encrypted)
        )


@router.post(
    f"{BASE}/calendars",
    response_model=CalDavCalendar,
    status_code=status.HTTP_201_CREATED,
)
async def create_apple_calendar(
    body: CreateCalendarRequest,
    row: CaldavCredential = Depends(get_credential),
):
    """Create a calendar in the user's iCloud account.

    Saves them a trip to the Calendar app mid-setup. Does not select it — the
    client follows up with PUT .../calendar.
    """
    with _icloud_errors():
        return create_calendar(
            settings.caldav_url,
            row.icloud_email,
            decrypt(row.password_encrypted),
            body.name,
        )


@router.put(f"{BASE}/calendar", response_model=ConnectionStatus)
async def select_apple_calendar(
    body: SelectCalendarRequest,
    row: CaldavCredential = Depends(get_credential),
    db: Session = Depends(get_session),
):
    """Point syncing at one of the user's calendars."""
    with _icloud_errors():
        calendars = list_calendars(
            settings.caldav_url, row.icloud_email, decrypt(row.password_encrypted)
        )

    # Only a calendar the account actually owns — never store a URL we were
    # handed but cannot see.
    if not any(cal.url == body.calendar_url for cal in calendars):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="unknown calendar"
        )

    CaldavCredentialRepo(db).set_calendar_url(row, body.calendar_url)
    db.commit()
    logger.info("calendar selected for user {}", row.user_id)
    return _status(row)
