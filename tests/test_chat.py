"""Chat endpoint tests (LLM calls may be skipped if Ollama/OpenAI unavailable)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_history_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/chat/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert isinstance(response.json()["data"], list)


@pytest.mark.asyncio
async def test_delete_history(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/api/v1/chat/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
