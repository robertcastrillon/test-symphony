from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_db

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Dependency that extracts and validates the current user from the JWT token."""
    from sqlalchemy import select

    from app.models.user import User

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired access token") from exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token: missing subject")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found")

    return user


__all__ = ["get_current_user", "get_db"]
