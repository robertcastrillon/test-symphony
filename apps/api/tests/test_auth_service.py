"""Direct service tests to ensure coverage of async service functions."""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.exceptions import AuthenticationError, ConflictError
from app.db.database import Base
from app.services import auth as auth_service

_TEST_URL = "sqlite+aiosqlite://"
_CONNECT_ARGS = {"check_same_thread": False}


def _make_engine():
    return create_async_engine(
        _TEST_URL,
        echo=False,
        connect_args=_CONNECT_ARGS,
        poolclass=StaticPool,
    )


async def _setup(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_register_service_success():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        result = await auth_service.register("svc@example.com", "Service User", "password123", db)
    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_register_service_duplicate():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        await auth_service.register("dup@example.com", "User", "password123", db)
    async with SessionLocal() as db:
        with pytest.raises(ConflictError):
            await auth_service.register("dup@example.com", "User", "password123", db)


@pytest.mark.asyncio
async def test_login_service_success():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        await auth_service.register("login@example.com", "User", "password123", db)
    async with SessionLocal() as db:
        result = await auth_service.login("login@example.com", "password123", db)
    assert result.access_token
    assert result.refresh_token


@pytest.mark.asyncio
async def test_login_service_wrong_password():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        await auth_service.register("badpw@example.com", "User", "password123", db)
    async with SessionLocal() as db:
        with pytest.raises(AuthenticationError):
            await auth_service.login("badpw@example.com", "wrongpassword", db)


@pytest.mark.asyncio
async def test_login_service_no_user():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        with pytest.raises(AuthenticationError):
            await auth_service.login("nobody@example.com", "password123", db)


@pytest.mark.asyncio
async def test_refresh_service_success():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        tokens = await auth_service.register("ref@example.com", "User", "password123", db)

    async with SessionLocal() as db:
        new_tokens = await auth_service.refresh_token(tokens.refresh_token, db)
    assert new_tokens.access_token
    assert new_tokens.refresh_token != tokens.refresh_token


@pytest.mark.asyncio
async def test_refresh_service_invalid_token():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        with pytest.raises(AuthenticationError):
            await auth_service.refresh_token("invalid.token.here", db)


@pytest.mark.asyncio
async def test_refresh_service_rotation():
    engine = _make_engine()
    SessionLocal = await _setup(engine)

    async with SessionLocal() as db:
        tokens = await auth_service.register("rot@example.com", "User", "password123", db)

    old_rt = tokens.refresh_token
    async with SessionLocal() as db:
        await auth_service.refresh_token(old_rt, db)

    async with SessionLocal() as db:
        with pytest.raises(AuthenticationError):
            await auth_service.refresh_token(old_rt, db)
