import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override settings before importing the app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret-key-for-tests-only")


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create a fresh in-memory SQLite engine per test function."""
    from app.core.config import settings

    settings.DATABASE_URL = "sqlite+aiosqlite://"

    test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
    )

    import app.models  # noqa: F401
    from app.db.database import Base

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Create a DB session for the test."""
    test_session_local = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with test_session_local() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(engine, db_session):
    """Create an async test client with DB dependency override."""
    from app.core.dependencies import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(client: AsyncClient):
    """Create a test user and return their credentials and tokens."""
    payload = {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "securepass123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, f"Failed to create test user: {response.json()}"
    tokens = response.json()
    return {
        "email": payload["email"],
        "password": payload["password"],
        "name": payload["name"],
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }
