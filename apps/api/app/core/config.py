from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./chronotrack.db"
    jwt_secret_key: str = "dev-secret-key"
    jwt_refresh_secret_key: str = "dev-refresh-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    telegram_token: str = ""
    telegram_webhook_url: str = ""


settings = Settings()
