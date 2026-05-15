"""Authentication schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserSignup(BaseModel):
    username: str = Field(min_length=3, max_length=50, examples=["johndoe"])
    email: EmailStr = Field(examples=["john@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["SecurePass123!"])
    full_name: str | None = Field(default=None, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["john@example.com"])
    password: str = Field(min_length=8, examples=["SecurePass123!"])


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    full_name: str | None
    created_at: str

    model_config = {"from_attributes": True}
