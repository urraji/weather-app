import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.lifespan import lifespan

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.config import settings
from app.logging import configure_logging, get_logger
from app.middleware import CorrelationAndMetricsMiddleware
from app.metrics import weather_requests_total, weather_stale_served_total, rate_limited_requests_total
from app.cache import cache
from app.weather import fetch_weather, UpstreamError, UpstreamTimeout, CircuitOpen

configure_logging()
log = get_logger()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationAndMetricsMiddleware)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    rate_limited_requests_total.inc()
    return PlainTextResponse('rate limited', status_code=HTTP_429_TOO_MANY_REQUESTS)

@app.get("/")
async def root():
    return {
        "service": "weather-alert-service",
        "endpoints": {
            "weather": "/weather/{location}",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
        },
    }

@app.get("/favicon.ico")
async def favicon():
    # Browsers request /favicon.ico by default; return 204 to avoid noisy 404s.
    return Response(status_code=204)

def _age_seconds(cached_at: float) -> int:
    return max(0, int(time.time() - cached_at))

@app.get('/weather/{location}')
@limiter.limit(settings.RATE_LIMIT)
async def get_weather(location: str, request: Request):
    weather_requests_total.inc()

    key = f"weather:{location.strip().lower()}"
    cached = cache.get(key)
    if cached:
        age = _age_seconds(cached.cached_at)
        return {'location': location, **cached.value, 'source': 'cache', 'data_age_seconds': age}

    if not settings.OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail='OPENWEATHER_API_KEY not configured')

    try:
        data = await fetch_weather(location)
        cache.set(key, data, ttl_seconds=settings.CACHE_TTL_SECONDS)
        return {'location': location, **data, 'source': 'api', 'data_age_seconds': 0}
    except (CircuitOpen, UpstreamError, UpstreamTimeout) as e:
        stale = cache.get(key)
        if stale:
            age = _age_seconds(stale.cached_at)
            if age <= settings.MAX_STALE_SECONDS:
                weather_stale_served_total.inc()
                headers = {'X-Data-Freshness': 'stale', 'X-Data-Age-Seconds': str(age)}
                return Response(
                    content=json.dumps({'location': location, **stale.value, 'source': 'stale', 'data_age_seconds': age}),
                    media_type='application/json',
                    headers=headers,
                    status_code=200,
                )

        log.warning('upstream_unavailable', location=location, err=str(e))
        raise HTTPException(status_code=503, detail='upstream unavailable')

@app.get('/health')
def health():
    if getattr(app.state, 'shutting_down', False):
        return Response(status_code=503, content='shutting_down')
    mode = 'redis' if settings.REDIS_URL else 'memory'
    return {'status': 'ok', 'cache_mode': mode}

@app.get('/metrics')
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
