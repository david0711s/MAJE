"""
MAJE – Redis Client Wrapper with automatic In-Memory Fallback
Allows running MAJE without a Redis server (standalone / local / on-the-go mode).
"""
from __future__ import annotations


import fnmatch
import os
import time
from typing import Optional, Union, Any

import redis.asyncio as aioredis
from loguru import logger


class InMemoryStore:
    """Lightweight in-memory replacement when Redis is not available."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expires: dict[str, float] = {}
        self._sets: dict[str, set] = {}

    def _purge_if_expired(self, key: str):
        if key in self._expires and time.time() > self._expires[key]:
            self._data.pop(key, None)
            self._expires.pop(key, None)
            self._sets.pop(key, None)

    def get(self, key: str) -> Optional[bytes]:
        self._purge_if_expired(key)
        val = self._data.get(key)
        if val is None:
            return None
        if isinstance(val, bytes):
            return val
        return str(val).encode("utf-8")

    def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None):
        self._data[key] = value
        if ex:
            self._expires[key] = time.time() + ex
        else:
            self._expires.pop(key, None)

    def delete(self, *keys: str):
        for k in keys:
            self._data.pop(k, None)
            self._expires.pop(k, None)
            self._sets.pop(k, None)

    def keys(self, pattern: str = "*") -> list:
        now = time.time()
        for k in list(self._expires.keys()):
            if now > self._expires[k]:
                self.delete(k)
        all_keys = list(set(self._data.keys()) | set(self._sets.keys()))
        matched = fnmatch.filter(all_keys, pattern)
        return [k.encode("utf-8") for k in matched]

    def sadd(self, key: str, *values):
        s = self._sets.setdefault(key, set())
        for v in values:
            s.add(v.encode("utf-8") if isinstance(v, str) else v)

    def srem(self, key: str, *values):
        s = self._sets.get(key)
        if s:
            for v in values:
                s.discard(v.encode("utf-8") if isinstance(v, str) else v)

    def smembers(self, key: str) -> set:
        return set(self._sets.get(key, set()))


class RedisClient:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._mem = InMemoryStore()
        self._use_fallback: bool = False

    async def connect(self):
        # Explicit disable flag
        if os.getenv("DISABLE_REDIS", "false").lower() in ("true", "1", "yes"):
            self._use_fallback = True
            logger.info("ℹ️ Redis disabled via DISABLE_REDIS=true. Using In-Memory store.")
            return

        url = os.getenv("REDIS_URL")
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = os.getenv("REDIS_PASSWORD", None)

        try:
            if url:
                client = aioredis.from_url(
                    url,
                    decode_responses=False,
                    socket_connect_timeout=1.5,
                )
            else:
                client = aioredis.Redis(
                    host=host, port=port, password=password,
                    decode_responses=False,
                    socket_connect_timeout=1.5,
                )
            await client.ping()
            self._client = client
            self._use_fallback = False
            from core.cost_tracker import cost_tracker
            cost_tracker._set_redis(self._client)
            logger.success(f"✅ Redis connected ({url or f'{host}:{port}'})")
        except Exception:
            self._client = None
            self._use_fallback = True
            logger.info("⚡ Kein Redis-Server gefunden -> Nutze In-Memory-Modus (Standalone / Unterwegs aktiv).")

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    async def ping(self) -> bool:
        if self._use_fallback or not self._client:
            return True
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    async def get(self, key: str) -> Optional[bytes]:
        if self._use_fallback or not self._client:
            return self._mem.get(key)
        try:
            return await self._client.get(key)
        except Exception:
            return self._mem.get(key)

    async def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None):
        if self._use_fallback or not self._client:
            self._mem.set(key, value, ex=ex)
            return
        try:
            await self._client.set(key, value, ex=ex)
        except Exception:
            self._mem.set(key, value, ex=ex)

    async def delete(self, *keys: str):
        if self._use_fallback or not self._client:
            self._mem.delete(*keys)
            return
        try:
            await self._client.delete(*keys)
        except Exception:
            self._mem.delete(*keys)

    async def keys(self, pattern: str = "*") -> list:
        if self._use_fallback or not self._client:
            return self._mem.keys(pattern)
        try:
            return await self._client.keys(pattern)
        except Exception:
            return self._mem.keys(pattern)

    async def sadd(self, key: str, *values):
        if self._use_fallback or not self._client:
            self._mem.sadd(key, *values)
            return
        try:
            await self._client.sadd(key, *values)
        except Exception:
            self._mem.sadd(key, *values)

    async def srem(self, key: str, *values):
        if self._use_fallback or not self._client:
            self._mem.srem(key, *values)
            return
        try:
            await self._client.srem(key, *values)
        except Exception:
            self._mem.srem(key, *values)

    async def smembers(self, key: str) -> set:
        if self._use_fallback or not self._client:
            return self._mem.smembers(key)
        try:
            return await self._client.smembers(key)
        except Exception:
            return self._mem.smembers(key)

    async def publish(self, channel: str, message: str):
        if self._use_fallback or not self._client:
            return
        try:
            await self._client.publish(channel, message)
        except Exception:
            pass

    async def subscribe(self, channel: str):
        if self._use_fallback or not self._client:
            class DummyPubSub:
                async def subscribe(self, *args, **kwargs):
                    pass
                async def listen(self):
                    if False:
                        yield {}
            return DummyPubSub()
        return self._client.pubsub()


# Singleton
redis_client = RedisClient()
