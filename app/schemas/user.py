from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    telegram_id: str | None = None
    whatsapp_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    telegram_id: str | None = None
    whatsapp_id: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    telegram_id: str | None
    whatsapp_id: str | None
    created_at: datetime
    updated_at: datetime
