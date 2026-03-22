from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    """User ORM model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
