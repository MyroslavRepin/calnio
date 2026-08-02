from collections.abc import Iterator
from contextlib import contextmanager

import caldav.lib.error as caldav_error
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.crypto import decrypt
from backend.core.logging import logger
from backend.deps.auth import get_current_user
from backend.deps.db import get_session
from backend.models.caldav_credential import CaldavCredential
from backend.models.user import User
from backend.repo.caldav_credential import CaldavCredentialRepo

# Transport failures (DNS, TLS, timeouts) surface as the HTTP library's own
# exception, not a DAVError. caldav 3.x prefers niquests and falls back to
# requests, so both installs are covered here.
try:
    from niquests.exceptions import RequestException
except ImportError:  # pragma: no cover
    from requests.exceptions import RequestException


@contextmanager
def icloud_errors() -> Iterator[None]:
    """Map CalDAV failures onto HTTP status codes, never onto a 401.

    A 401 would make the frontend refresh and resubmit a wrong password to
    Apple, which risks locking the Apple ID.
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
    """The current user's stored iCloud credential, or 404."""
    row = CaldavCredentialRepo(db).get(user.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no apple calendar connection",
        )
    return row


def icloud_credentials(row: CaldavCredential) -> tuple[str, str, str]:
    """CalDAV url, iCloud email and decrypted password for this account."""
    return settings.caldav_url, row.icloud_email, decrypt(row.password_encrypted)
