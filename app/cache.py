import time
import json
from dataclasses import dataclass
from typing import Any, Optional

from cachetools import TTLCache
from redis import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.metrics import weather_cache_hits_total, weather_cache_misses_total
from app.logging import get_logger

log = get_logger()

_memory_cache = TTLCache(maxsize=5000, ttl=settings.CACHE_TTL_SECONDS)

@dataclass
class CacheValue:
    value: Any
    cached_at: float

class Cache:
    def __init__(self):
        self.redis: Optional[Redis] = None
        if settings.REDIS_URL:
            try:
                self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception:
                self.redis = None
                log.warning('redis_init_failed', fallback='memory')

    def get(self, key: str) -> Optional[CacheValue]:
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw is not None:
                    weather_cache_hits_total.labels('redis').inc()
                    d = json.loads(raw)
                    return CacheValue(value=d['value'], cached_at=float(d['cached_at']))
                weather_cache_misses_total.labels('redis').inc()
            except RedisError:
                log.warning('redis_get_failed', key=key, fallback='memory')
                self.redis = None

        v = _memory_cache.get(key)
        if v is not None:
            weather_cache_hits_total.labels('memory').inc()
            return v
        weather_cache_misses_total.labels('memory').inc()
        return None

    def set(self, key: str, value: Any, ttl_seconds: int):
        cv = CacheValue(value=value, cached_at=time.time())
        if self.redis:
            try:
                self.redis.setex(key, ttl_seconds, json.dumps({'cached_at': cv.cached_at, 'value': cv.value}))
            except RedisError:
                log.warning('redis_set_failed', key=key, fallback='memory')
                self.redis = None
        _memory_cache[key] = cv

cache = Cache()
