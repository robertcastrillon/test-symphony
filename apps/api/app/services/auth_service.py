import uuid

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


class AuthService:
    @staticmethod
    async def register(
        email: str, name: str, password: str, db: AsyncSession
    ) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is not None:
            raise ConflictError(f"Email already registered: {email}")

        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        user_id = str(user.id)
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    @staticmethod
    async def login(email: str, password: str, db: AsyncSession) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        user_id = str(user.id)
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    @staticmethod
    async def refresh_token(refresh_token: str, db: AsyncSession) -> TokenResponse:
        try:
            user_id = decode_refresh_token(refresh_token)
        except JWTError as e:
            raise AuthenticationError("Invalid or expired refresh token") from e

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthenticationError("User not found")

        uid = str(user.id)
        return TokenResponse(
            access_token=create_access_token(uid),
            refresh_token=create_refresh_token(uid),
        )
