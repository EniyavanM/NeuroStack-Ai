"""Authentication API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]["tokens"]
    assert body["data"]["user"]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePass123!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "SecurePass123!"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["tokens"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"
