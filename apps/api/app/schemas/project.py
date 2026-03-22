import re

from pydantic import BaseModel, Field, field_validator

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    color: str = Field(default="#6366f1")
    client_id: str | None = None
    is_active: bool = True

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not HEX_COLOR_RE.match(v):
            raise ValueError("color must be a valid hex color string (e.g. #a1b2c3)")
        return v


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = None
    client_id: str | None = None
    is_active: bool | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and not HEX_COLOR_RE.match(v):
            raise ValueError("color must be a valid hex color string (e.g. #a1b2c3)")
        return v


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    client_id: str | None
    name: str
    description: str | None
    color: str
    is_active: bool
