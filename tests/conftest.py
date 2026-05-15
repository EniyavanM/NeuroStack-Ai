"""Pytest fixtures — in-memory SQLite and mocked Redis."""

import os

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("OPENAI_API_KEY", "")

from app.core.config import get_settings

get_settings.cache_clear()

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_db
from app.database.base import Base
import app.models  # noqa: F401
from app.main import app

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
        },
    )
    if signup.status_code == 201:
        token = signup.json()["data"]["tokens"]["access_token"]
    else:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!"},
        )
        token = login.json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
