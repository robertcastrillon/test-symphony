import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Client(BaseModel):
    __tablename__ = "clients"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hourly_rate: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
