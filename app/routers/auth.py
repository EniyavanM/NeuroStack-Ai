"""Authentication routes."""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.auth import TokenRefresh, UserLogin, UserSignup
from app.schemas.common import APIResponse, success_response
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
async def signup(payload: UserSignup, db: DbSession):
    user = await auth_service.register_user(db, payload)
    tokens = auth_service.issue_tokens(user)
    return success_response(
        data={"user": auth_service.user_to_public(user), "tokens": tokens},
        message="Account created successfully",
    )


@router.post("/login", response_model=APIResponse)
async def login(payload: UserLogin, db: DbSession):
    user = await auth_service.authenticate_user(db, payload)
    tokens = auth_service.issue_tokens(user)
    return success_response(
        data={"user": auth_service.user_to_public(user), "tokens": tokens},
        message="Login successful",
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh(payload: TokenRefresh, db: DbSession):
    tokens = await auth_service.refresh_access_token(db, payload.refresh_token)
    return success_response(data=tokens, message="Token refreshed")


@router.get("/me", response_model=APIResponse)
async def me(current_user: CurrentUser):
    return success_response(data=auth_service.user_to_public(current_user))
