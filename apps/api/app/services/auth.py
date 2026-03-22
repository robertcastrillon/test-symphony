import hashlib

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse


def _hash_token(token: str) -> str:
    """SHA-256 digest of token, safe to bcrypt (always 64 chars < 72 byte limit)."""
    return hashlib.sha256(token.encode()).hexdigest()


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

    hashed_password = get_password_hash(password)
    user = User(email=email, name=name, hashed_password=hashed_password)
    db.add(user)
    await db.flush()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    user.refresh_token_hash = get_password_hash(_hash_token(refresh_token))
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
        raise AuthenticationError("Invalid email or password")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    user.refresh_token_hash = get_password_hash(_hash_token(refresh_token))
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_token(
    refresh_token: str,
    db: AsyncSession,
) -> TokenResponse:
    try:
        payload = decode_refresh_token(refresh_token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise AuthenticationError("Invalid token")
    except JWTError:
        raise AuthenticationError("Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found")

    if user.refresh_token_hash is None or not verify_password(
        _hash_token(refresh_token), user.refresh_token_hash
    ):
        raise AuthenticationError("Token has been rotated or is invalid")

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    user.refresh_token_hash = get_password_hash(_hash_token(new_refresh_token))
    await db.commit()

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)
