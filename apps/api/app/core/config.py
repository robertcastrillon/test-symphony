from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "CHRONOTRACK_"}

    app_name: str = "ChronoTrack API"
    debug: bool = False
    version: str = "0.1.0"

    database_url: str = (
        "postgresql+asyncpg://chronotrack:chronotrack@localhost:5432/chronotrack"
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
