import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: str = "user"
    is_active: bool = True
    is_verified: bool = False
    bio: str | None = None
    company: str | None = None
    location: str | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class UserUpdate(BaseModel):
    full_name: str | None = None
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    password: str | None = Field(None, min_length=6, max_length=100)
    role: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
