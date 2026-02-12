from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import httpx
import redis.asyncio as redis
from fastapi import FastAPI

from app.cache import MemoryCache, RedisCache
from app.config import settings
from app.circuit import CircuitBreaker
from app.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class AppState:
    http: httpx.AsyncClient
    cache: Any
    memory_cache: MemoryCache
    redis_client: Optional[redis.Redis]
    breaker: CircuitBreaker
    shutting_down: asyncio.Event


async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    shutting_down = asyncio.Event()
    http = httpx.AsyncClient()
    memory_cache = MemoryCache()
    breaker = CircuitBreaker()

    redis_client = None
    cache = memory_cache
    if settings.REDIS_URL:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, encoding=None, decode_responses=False)
            await redis_client.ping()
            cache = RedisCache(redis_client)
            log.info("redis_connected")
        except Exception:
            log.warning("redis_unavailable_falling_back_to_memory")
            redis_client = None
            cache = memory_cache

    app.state.state = AppState(
        http=http,
        cache=cache,
        memory_cache=memory_cache,
        redis_client=redis_client,
        breaker=breaker,
        shutting_down=shutting_down,
    )
    yield
    shutting_down.set()
    await http.aclose()
    if redis_client is not None:
        await redis_client.aclose()
