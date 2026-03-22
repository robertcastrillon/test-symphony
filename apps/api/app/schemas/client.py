from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    hourly_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class ClientResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    name: str
    email: str | None
    hourly_rate: Decimal
    currency: str
