from __future__ import annotations

import time
from fastapi import FastAPI, HTTPException, Response, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.correlation import correlation_id_middleware
from app.logging_utils import configure_logging, get_logger
from app.lifespan import lifespan
from app.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION, RATE_LIMITED_TOTAL, STALE_SERVED_TOTAL, CIRCUIT_OPEN_TOTAL
from app.rate_limit import _global_limiter
from app.cache import CacheItem, serialize_item, deserialize_item
from app.weather import fetch_weather, UpstreamError

configure_logging()
log = get_logger(__name__)

app = FastAPI(lifespan=lifespan)
app.middleware("http")(correlation_id_middleware)


@app.get("/")
async def root():
    return {"service": "weather-alert-service"}


@app.get("/health")
async def health(response: Response, request: Request):
    st = request.app.state.state
    if st.shutting_down.is_set():
        response.status_code = 503
        return {"status": "shutting_down"}
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/weather/{location}")
async def weather(location: str, request: Request):
    # Simple per-process fixed window rate limit
    if not _global_limiter.allow():
        RATE_LIMITED_TOTAL.labels("/weather").inc()
        raise HTTPException(status_code=429, detail="rate_limited")

    st = request.app.state.state

    if not settings.OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY not set")

    key = f"weather:{location.strip().lower()}"

    cached = await st.cache.get(key)
    if cached:
        item = deserialize_item(cached)
        age = time.time() - item.fetched_at
        # Fresh enough: return immediately
        if age <= settings.CACHE_TTL_SECONDS:
            return item.payload
        # Stale: we'll attempt refresh, but may serve stale on failure within MAX_STALE_SECONDS

    # Circuit breaker
    if st.breaker.is_open():
        CIRCUIT_OPEN_TOTAL.labels("openweather").inc()
        if cached:
            item = deserialize_item(cached)
            age = time.time() - item.fetched_at
            if age <= settings.MAX_STALE_SECONDS:
                STALE_SERVED_TOTAL.inc()
                return item.payload
        raise HTTPException(status_code=503, detail="upstream_circuit_open")

    try:
        payload = await fetch_weather(st.http, location)
        st.breaker.record_success()
        await st.cache.set(key, serialize_item(CacheItem(payload=payload, fetched_at=time.time())), settings.CACHE_TTL_SECONDS)
        return payload
    except UpstreamError as e:
        st.breaker.record_failure()
        if cached:
            item = deserialize_item(cached)
            age = time.time() - item.fetched_at
            if age <= settings.MAX_STALE_SECONDS:
                STALE_SERVED_TOTAL.inc()
                return item.payload
        raise HTTPException(status_code=503, detail="upstream_error")
    except Exception:
        st.breaker.record_failure()
        if cached:
            item = deserialize_item(cached)
            age = time.time() - item.fetched_at
            if age <= settings.MAX_STALE_SECONDS:
                STALE_SERVED_TOTAL.inc()
                return item.payload
        raise HTTPException(status_code=503, detail="upstream_unavailable")


@app.middleware("http")
async def prom_middleware(request: Request, call_next):
    start = time.time()
    path = request.url.path
    method = request.method
    try:
        resp = await call_next(request)
        status = str(resp.status_code)
        return resp
    finally:
        dur = time.time() - start
        # Avoid high-cardinality paths by bucketing dynamic path
        metric_path = path if not path.startswith("/weather/") else "/weather/{location}"
        HTTP_REQUESTS_TOTAL.labels(method, metric_path, status if 'status' in locals() else "500").inc()
        HTTP_REQUEST_DURATION.labels(method, metric_path).observe(dur)
