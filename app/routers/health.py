"""Health and metrics routes."""

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.database.session import engine
from app.middleware.metrics import metrics_endpoint
from app.schemas.common import APIResponse, success_response
from app.utils.redis_client import redis_health_check

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=APIResponse)
async def health_check():
    settings = get_settings()
    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    redis_status = "healthy" if await redis_health_check() else "unhealthy"
    overall = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return success_response(
        data={
            "status": overall,
            "app": settings.app_name,
            "version": __version__,
            "database": db_status,
            "redis": redis_status,
        },
        message="Health check complete",
    )


router.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)
