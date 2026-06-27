from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_specific_password: str
    icloud_email: str
    notion_token: str = ""
    db_url: str


settings = Settings()  # pyright: ignore[reportCallIssue]
