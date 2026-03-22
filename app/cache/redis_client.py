"""Async Redis cache client with JSON serialization."""
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis cache client with JSON serialization and TTL support."""

    def __init__(self, url: str | None = None) -> None:
        settings = get_settings()
        self._url = url or settings.redis_url
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        self._client = aioredis.from_url(self._url, decode_responses=True)
        logger.info("Redis cache connected at %s", self._url)

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_connected(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Any | None:
        """Return cached value for key, or None if missing/expired."""
        client = self._ensure_connected()
        raw = await client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store value as JSON with an optional TTL in seconds."""
        client = self._ensure_connected()
        serialized = json.dumps(value, default=str)
        await client.setex(key, ttl, serialized)

    async def delete(self, key: str) -> bool:
        """Delete a cached key. Returns True if it existed."""
        client = self._ensure_connected()
        deleted = await client.delete(key)
        return bool(deleted)

    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the cache."""
        client = self._ensure_connected()
        count = await client.exists(key)
        return bool(count)
