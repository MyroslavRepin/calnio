from datetime import datetime, timedelta, timezone

import jwt


class JWTService:
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
        return self._encode(user_id, "access", self.access_token_exp)

    def create_refresh_token(self, user_id: str) -> str:
        return self._encode(user_id, "refresh", self.refresh_token_exp)

    def create_token_pair(self, user_id: str) -> tuple[str, str]:
        """Mint both tokens at once — used on login and on refresh."""
        return self.create_access_token(user_id), self.create_refresh_token(user_id)

    def decode(self, token: str, expected_type: str | None = None) -> dict:
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        if expected_type is not None and payload.get("type") != expected_type:
            raise jwt.InvalidTokenError(
                f"expected {expected_type} token, got {payload.get('type')}"
            )
        return payload

    def verify(self, token: str, expected_type: str) -> str:
        """Validate a token and return its subject (user id).

        Raises jwt.InvalidTokenError (or a subclass, e.g. ExpiredSignatureError)
        on a bad signature, wrong type, or expiry.
        """
        payload = self.decode(token, expected_type=expected_type)
        sub = payload.get("sub")
        if not sub:
            raise jwt.InvalidTokenError("token missing sub claim")
        return sub

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Trade a valid refresh token for a fresh access + refresh pair.

        Rotates the refresh token so a leaked one has a bounded lifetime.
        """
        user_id = self.verify(refresh_token, expected_type="refresh")
        return self.create_token_pair(user_id)

    def _encode(self, user_id: str, token_type: str, exp_minutes: int) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(minutes=exp_minutes),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
