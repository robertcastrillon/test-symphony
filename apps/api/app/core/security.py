import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, str]:
    """Returns (token, jti) so caller can store jti for rotation tracking."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises JWTError on failure."""
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Raises JWTError on failure."""
    payload = jwt.decode(
        token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("type") != "refresh":
        raise JWTError("Not a refresh token")
    return payload
