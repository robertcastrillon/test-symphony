from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse


async def register(
    email: str,
    name: str,
    password: str,
    db: AsyncSession,
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Email already registered")

    hashed = get_password_hash(password)
    user = User(email=email, name=name, hashed_password=hashed)
    db.add(user)
    await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    user.refresh_token_hash = get_password_hash(refresh_token)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def login(
    email: str,
    password: str,
    db: AsyncSession,
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid credentials")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    user.refresh_token_hash = get_password_hash(refresh_token)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_token(
    refresh_token_str: str,
    db: AsyncSession,
) -> TokenResponse:
    from jose import JWTError

    from app.core.security import decode_refresh_token

    try:
        user_id = decode_refresh_token(refresh_token_str)
    except JWTError:
        raise AuthenticationError("Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found")

    if user.refresh_token_hash is None or not verify_password(
        refresh_token_str, user.refresh_token_hash
    ):
        raise AuthenticationError("Refresh token has been rotated or revoked")

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))
    user.refresh_token_hash = get_password_hash(new_refresh)
    await db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
