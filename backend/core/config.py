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


settings = Settings()  # pyright: ignore[reportCallIssue]
