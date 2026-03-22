import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
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
    if result.scalar_one_or_none() is not None:
        raise ConflictError("Email already registered")

    hashed = get_password_hash(password)
    user = User(email=email, name=name, hashed_password=hashed)
    db.add(user)
    await db.flush()  # get the user.id

    access_token = create_access_token(str(user.id))
    refresh_token, jti = create_refresh_token(str(user.id))
    user.refresh_token_jti = jti
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
    refresh_token, jti = create_refresh_token(str(user.id))
    user.refresh_token_jti = jti
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(
    refresh_token: str,
    db: AsyncSession,
) -> TokenResponse:
    from jose import JWTError

    try:
        payload = decode_refresh_token(refresh_token)
    except JWTError:
        raise AuthenticationError("Invalid or expired refresh token")

    user_id = payload.get("sub")
    jti = payload.get("jti")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    # Validate refresh token rotation — the JTI must match the stored one
    if user.refresh_token_jti != jti:
        raise AuthenticationError("Refresh token has been rotated or invalidated")

    # Issue new pair and rotate
    access_token = create_access_token(str(user.id))
    new_refresh_token, new_jti = create_refresh_token(str(user.id))
    user.refresh_token_jti = new_jti
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


async def get_current_user(token: str, db: AsyncSession) -> User:
    from jose import JWTError

    from app.core.security import decode_access_token

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise AuthenticationError("Invalid or expired access token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found")
    return user
