from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Client(BaseModel):
    __tablename__ = "clients"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
