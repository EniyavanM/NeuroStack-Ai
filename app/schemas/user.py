"""User profile schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserProfileUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=100)


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    full_name: str | None
    created_at: str
    updated_at: str
