"""Redis-backed rate limiting."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.utils.redis_client import rate_limit_check


class RateLimitMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        import os

        if os.getenv("TESTING") == "true" or request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"{client_ip}:{request.url.path}"
        allowed, remaining = await rate_limit_check(
            identifier,
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Try again later.",
                    "data": None,
                },
                headers={"X-RateLimit-Remaining": "0"},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
