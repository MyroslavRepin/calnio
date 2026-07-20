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
    event_due_date_field_name: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str
    session_secret: str
    jwt_secret: str

    # Frontend origin the callback redirects back to (and the CORS allow-origin).
    frontend_url: str = "http://localhost:5173"

    # Refresh-token cookie policy. Defaults suit dev cross-origin
    # (Vite :5173 → API :8080): a cross-site cookie must be SameSite=None and
    # Secure (Chrome treats localhost as a secure context, so Secure works over
    # http://localhost). For prod same-origin (FastAPI StaticFiles serving the
    # built Vue app) set cookie_samesite=lax.
    cookie_secure: bool = True
    cookie_samesite: str = "none"
    cookie_domain: str | None = None


settings = Settings()  # pyright: ignore[reportCallIssue]
