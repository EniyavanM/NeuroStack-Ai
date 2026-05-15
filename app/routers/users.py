"""User profile routes."""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.common import APIResponse, success_response
from app.schemas.user import UserProfileUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=APIResponse)
async def get_profile(current_user: CurrentUser):
    return success_response(data=user_service.profile_to_dict(current_user))


@router.patch("/profile", response_model=APIResponse)
async def update_profile(payload: UserProfileUpdate, current_user: CurrentUser, db: DbSession):
    user = await user_service.update_profile(db, current_user, payload)
    return success_response(data=user_service.profile_to_dict(user), message="Profile updated")
