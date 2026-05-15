"""User profile management."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserProfileUpdate


async def update_profile(db: AsyncSession, user: User, payload: UserProfileUpdate) -> User:
    if payload.username and payload.username != user.username:
        existing = await db.execute(select(User).where(User.username == payload.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        user.username = payload.username

    if payload.email and payload.email != user.email:
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")
        user.email = payload.email

    if payload.full_name is not None:
        user.full_name = payload.full_name

    await db.flush()
    await db.refresh(user)
    return user


def profile_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "full_name": user.full_name,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }
