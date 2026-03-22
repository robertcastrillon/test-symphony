from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    hash_token,
    verify_password,
    verify_token_hash,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, data: RegisterRequest) -> TokenResponse:
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == data.email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise ConflictError("A user with this email already exists")

        hashed_pw = get_password_hash(data.password)
        user = User(
            email=data.email,
            name=data.name,
            hashed_password=hashed_pw,
        )
        self.db.add(user)
        await self.db.flush()  # Get the user ID assigned

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        user.refresh_token_hash = hash_token(refresh_token)

        await self.db.commit()
        await self.db.refresh(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        user.refresh_token_hash = hash_token(refresh_token)

        await self.db.commit()
        await self.db.refresh(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise AuthenticationError("Invalid or expired refresh token") from exc

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid refresh token: missing subject")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise AuthenticationError("User not found")

        if user.refresh_token_hash is None:
            raise AuthenticationError("No refresh token stored for this user")

        if not verify_token_hash(refresh_token, user.refresh_token_hash):
            raise AuthenticationError("Refresh token mismatch or already used")

        # Issue new token pair (token rotation)
        new_access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)
        user.refresh_token_hash = hash_token(new_refresh_token)

        await self.db.commit()
        await self.db.refresh(user)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
