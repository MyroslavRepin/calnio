from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_specific_password: str
    icloud_email: str
    notion_token: str
    db_url: str
    caldav_url: str
    tasks_data_source: str
    syncing_interval_minutes: str
    active_sync: bool
    event_due_date_field_name: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str

    # Notion OAuth — a *public* integration (notion.so/my-integrations), not the
    # internal one `notion_token` belongs to. Redirect URI must match the value
    # registered there exactly.
    notion_oauth_client_id: str
    notion_oauth_client_secret: str
    notion_oauth_redirect_uri: str

    session_secret: str
    jwt_secret: str

    # Fernet key encrypting per-user secrets at rest: iCloud app-specific
    # passwords and Notion access tokens.
    # Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Losing it makes every stored credential permanently unreadable — users
    # would have to re-enter their app-specific password.
    credentials_encryption_key: str

    # Frontend origin the callback redirects back to (and the CORS allow-origin).
    frontend_url: str = "http://localhost:5173"

    # Refresh-token cookie policy. Defaults suit dev cross-origin
    # (Vite :5173 → API :8080): a cross-site cookie must be SameSite=None and
    # Secure (Chrome treats localhost as a secure context, so Secure works over
    # http://localhost). For prod same-origin (FastAPI StaticFiles serving the
    # built Vue app) set cookie_samesite=lax.
    # Literal, not str: Starlette's set_cookie and SessionMiddleware both take
    # this as a Literal, and it makes a typo in .env fail at boot.
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "none"
    cookie_domain: str | None = None


settings = Settings()  # pyright: ignore[reportCallIssue]
