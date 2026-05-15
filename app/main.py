"""NeuroStack AI — FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.core.config import get_settings
from app.database.session import init_db
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.routers import agents, auth, chat, documents, health, users
from app.schemas.common import error_response
from app.utils.logger import setup_logging
from app.utils.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    for path in (settings.upload_dir, settings.chroma_persist_dir):
        from pathlib import Path

        Path(path).mkdir(parents=True, exist_ok=True)
    await init_db()
    yield
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Production-grade multi-agent AI backend with JWT auth, RAG, "
            "PostgreSQL, Redis, LangChain, and ChromaDB."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    prefix = settings.api_v1_prefix
    app.include_router(health.router)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(agents.router, prefix=prefix)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_response("Validation error", data={"errors": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception):
        if settings.debug:
            detail = str(exc)
        else:
            detail = "Internal server error"
        return JSONResponse(status_code=500, content=error_response(detail))

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "app": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
