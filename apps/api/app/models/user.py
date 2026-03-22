from typing import Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # For refresh token rotation — stores the JTI of the currently valid refresh token
    refresh_token_jti: Mapped[Optional[str]] = mapped_column(String, nullable=True)
