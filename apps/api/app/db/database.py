from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def create_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.DATABASE_URL
    return create_async_engine(
        url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )


engine = create_engine()
