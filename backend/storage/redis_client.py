"""
MAJE – Redis Client Wrapper
"""
from __future__ import annotations

import os
from typing import Optional, Union

import redis.asyncio as aioredis
from loguru import logger


class RedisClient:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        # Prefer a full REDIS_URL (redis://[:password@]host:port/db) if provided,
        # otherwise fall back to REDIS_HOST / REDIS_PORT / REDIS_PASSWORD.
        url = os.getenv("REDIS_URL")
        if url:
            self._client = aioredis.from_url(
                url,
                decode_responses=False,
                socket_connect_timeout=5,
            )
        else:
            host = os.getenv("REDIS_HOST", "redis")
            port = int(os.getenv("REDIS_PORT", "6379"))
            password = os.getenv("REDIS_PASSWORD", None)
            self._client = aioredis.Redis(
                host=host, port=port, password=password,
                decode_responses=False,
                socket_connect_timeout=5,
            )
        await self.ping()
        # Inject into cost_tracker
        from core.cost_tracker import cost_tracker
        cost_tracker._set_redis(self._client)
        logger.success(f"✅ Redis connected ({url or 'host/port'})")

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    async def ping(self) -> bool:
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def get(self, key: str) -> Optional[bytes]:
        return await self._client.get(key)

    async def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None):
        await self._client.set(key, value, ex=ex)

    async def delete(self, *keys: str):
        await self._client.delete(*keys)

    async def keys(self, pattern: str) -> list:
        return await self._client.keys(pattern)

    async def sadd(self, key: str, *values):
        await self._client.sadd(key, *values)

    async def srem(self, key: str, *values):
        await self._client.srem(key, *values)

    async def smembers(self, key: str) -> set:
        return await self._client.smembers(key)

    async def publish(self, channel: str, message: str):
        await self._client.publish(channel, message)

    async def subscribe(self, channel: str):
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Singleton
redis_client = RedisClient()
