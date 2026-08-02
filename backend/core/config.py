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

    # Global off-switch: false registers no interval job and refuses one-off
    # runs, so a dev instance pointed at the real database never writes into a
    # user's calendar. Per-user enabled is the finer switch.
    scheduler_enabled: bool
    event_due_date_field_name: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str

    # A public integration (notion.so/my-integrations), not the internal one
    # notion_token belongs to. The redirect URI must match it exactly.
    notion_oauth_client_id: str
    notion_oauth_client_secret: str
    notion_oauth_redirect_uri: str

    session_secret: str
    jwt_secret: str

    # Encrypts per-user secrets at rest. Losing it makes every stored
    # credential unreadable and every user has to reconnect.
    # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    credentials_encryption_key: str

    # Where the OAuth callback redirects back to, and the CORS allow-origin.
    frontend_url: str = "http://localhost:5173"

    # Defaults suit dev cross-origin (Vite :5173 to API :8080), where a
    # cross-site cookie must be SameSite=None and Secure. Prod is same-origin,
    # so it sets cookie_samesite=lax. Literal, not str, so a typo in .env fails
    # at boot instead of at the first login.
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "none"
    cookie_domain: str | None = None


settings = Settings()  # pyright: ignore[reportCallIssue]
