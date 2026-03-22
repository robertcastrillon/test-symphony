from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": ""}

    app_name: str = "ChronoTrack API"
    version: str = "1.0.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://chronotrack:chronotrack@localhost:5432/chronotrack"

    jwt_secret_key: str = "change-me-in-production"
    jwt_refresh_secret_key: str = "change-me-refresh-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:5173"]

    telegram_token: str = ""
    telegram_webhook_url: str = ""


settings = Settings()
