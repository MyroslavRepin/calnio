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


settings = Settings()  # pyright: ignore[reportCallIssue]
