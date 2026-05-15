"""Redis connection and helpers for cache, rate limiting, and sessions."""

from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


async def redis_health_check() -> bool:
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False


async def cache_get(key: str) -> str | None:
    client = await get_redis()
    return await client.get(key)


async def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
    client = await get_redis()
    await client.setex(key, ttl_seconds, value)


async def cache_delete(key: str) -> None:
    client = await get_redis()
    await client.delete(key)


async def rate_limit_check(identifier: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """Return (allowed, remaining). Uses sliding window counter."""
    client = await get_redis()
    key = f"rate_limit:{identifier}"
    current = await client.incr(key)
    if current == 1:
        await client.expire(key, window_seconds)
    remaining = max(0, limit - current)
    return current <= limit, remaining


async def session_set(session_id: str, data: dict[str, Any], ttl_seconds: int = 3600) -> None:
    import json

    client = await get_redis()
    await client.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))


async def session_get(session_id: str) -> dict[str, Any] | None:
    import json

    client = await get_redis()
    raw = await client.get(f"session:{session_id}")
    if raw is None:
        return None
    return json.loads(raw)
