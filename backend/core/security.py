from datetime import datetime, timedelta, timezone

import jwt

from backend.core.config import settings


class JWTService:
    """Mints and validates the access and refresh tokens, HS256."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_exp: int = 5,
        refresh_token_exp: int = 43200,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_exp = access_token_exp
        self.refresh_token_exp = refresh_token_exp

    def create_access_token(self, user_id: str) -> str:
        """Mint a short-lived access token."""
        return self.encode(user_id, "access", self.access_token_exp)

    def create_refresh_token(self, user_id: str) -> str:
        """Mint a long-lived refresh token."""
        return self.encode(user_id, "refresh", self.refresh_token_exp)

    def create_token_pair(self, user_id: str) -> tuple[str, str]:
        """Mint both tokens at once, on login and on refresh."""
        return self.create_access_token(user_id), self.create_refresh_token(user_id)

    def decode(self, token: str, expected_type: str | None = None) -> dict:
        """Decode a token, rejecting one whose type is not the expected one."""
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        if expected_type is not None and payload.get("type") != expected_type:
            raise jwt.InvalidTokenError(
                f"expected {expected_type} token, got {payload.get('type')}"
            )
        return payload

    def verify(self, token: str, expected_type: str) -> str:
        """Validate a token and return its subject, or raise jwt.InvalidTokenError."""
        payload = self.decode(token, expected_type=expected_type)
        sub = payload.get("sub")
        if not sub:
            raise jwt.InvalidTokenError("token missing sub claim")
        return sub

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Trade a valid refresh token for a fresh, rotated pair."""
        user_id = self.verify(refresh_token, expected_type="refresh")
        return self.create_token_pair(user_id)

    def encode(self, user_id: str, token_type: str, exp_minutes: int) -> str:
        """Sign one token carrying the subject, its type, and an expiry."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(minutes=exp_minutes),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


jwt_service = JWTService(settings.jwt_secret)
