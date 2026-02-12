from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from app.metrics import CACHE_ERRORS_TOTAL, CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL
from app.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class CacheItem:
    payload: dict[str, Any]
    fetched_at: float


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> Optional[str]:
        try:
            v = self._store.get(key)
            if v is None:
                CACHE_MISSES_TOTAL.labels("memory").inc()
                return None
            expires_at, data = v
            if time.time() > expires_at:
                self._store.pop(key, None)
                CACHE_MISSES_TOTAL.labels("memory").inc()
                return None
            CACHE_HITS_TOTAL.labels("memory").inc()
            return data
        except Exception:
            CACHE_ERRORS_TOTAL.labels("memory", "get").inc()
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            self._store[key] = (time.time() + ttl_seconds, value)
        except Exception:
            CACHE_ERRORS_TOTAL.labels("memory", "set").inc()


class RedisCache:
    def __init__(self, redis_client) -> None:
        self._r = redis_client

    async def get(self, key: str) -> Optional[str]:
        try:
            v = await self._r.get(key)
            if v is None:
                CACHE_MISSES_TOTAL.labels("redis").inc()
                return None
            CACHE_HITS_TOTAL.labels("redis").inc()
            return v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else str(v)
        except Exception:
            CACHE_ERRORS_TOTAL.labels("redis", "get").inc()
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            await self._r.set(key, value, ex=ttl_seconds)
        except Exception:
            CACHE_ERRORS_TOTAL.labels("redis", "set").inc()


def serialize_item(item: CacheItem) -> str:
    return json.dumps({"payload": item.payload, "fetched_at": item.fetched_at})


def deserialize_item(s: str) -> CacheItem:
    obj = json.loads(s)
    return CacheItem(payload=obj["payload"], fetched_at=float(obj["fetched_at"]))
