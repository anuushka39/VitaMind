"""
Pydantic schemas for the User resource.

Separate from the SQLAlchemy model on purpose: the ORM model describes what's
stored in MySQL, these schemas describe what's allowed over the API boundary.
For example, `id`/`created_at` are server-generated and must never be
accepted on create, but they ARE returned on read — that asymmetry is exactly
what separate Create/Update/Out schemas express.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import Platform


class UserBase(BaseModel):
    platform: Platform
    platform_user_id: str = Field(..., max_length=64)
    name: str | None = Field(default=None, max_length=100)
    goals: dict | None = None
    allergies: list[str] | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    # All fields optional — PATCH should let the client send only what's
    # changing, not force a full resend of the resource.
    name: str | None = Field(default=None, max_length=100)
    goals: dict | None = None
    allergies: list[str] | None = None


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Lets Pydantic build this schema directly from a SQLAlchemy model
    # instance (model.id, model.name, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)
