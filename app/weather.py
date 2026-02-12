from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.config import settings
from app.correlation import get_request_id
from app.metrics import (
    UPSTREAM_ERRORS_TOTAL,
    UPSTREAM_REQUEST_DURATION,
    UPSTREAM_REQUESTS_TOTAL,
)


class UpstreamError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _is_retryable_upstream_exception(exc: Exception) -> bool:
    # Retry only transient failures
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, UpstreamError) and exc.status_code is not None:
        return exc.status_code >= 500 or exc.status_code == 429
    return False


@retry(
    stop=stop_after_attempt(settings.UPSTREAM_MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=0.2, min=0.2, max=2),
    retry=retry_if_exception(_is_retryable_upstream_exception),
    reraise=True,
)
async def fetch_weather(http: httpx.AsyncClient, location: str) -> dict[str, Any]:
    params = {
        "q": location,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }
    headers = {}
    rid = get_request_id()
    if rid:
        headers["X-Request-ID"] = rid

    start = time.time()
    try:
        r = await http.get(settings.OPENWEATHER_URL, params=params, headers=headers, timeout=settings.HTTP_TIMEOUT_SECONDS)
    except Exception:
        UPSTREAM_REQUESTS_TOTAL.labels("openweather", "exception").inc()
        raise
    finally:
        UPSTREAM_REQUEST_DURATION.labels("openweather").observe(time.time() - start)

    status_class = f"{r.status_code // 100}xx"
    UPSTREAM_REQUESTS_TOTAL.labels("openweather", status_class).inc()

    if r.status_code != 200:
        UPSTREAM_ERRORS_TOTAL.labels("openweather", str(r.status_code)).inc()
        raise UpstreamError(f"status={r.status_code}", status_code=r.status_code)

    data = r.json()
    return {
        "temperature": data.get("main", {}).get("temp"),
        "conditions": (data.get("weather") or [{}])[0].get("description"),
        "humidity": data.get("main", {}).get("humidity"),
        "wind_speed": data.get("wind", {}).get("speed"),
    }
