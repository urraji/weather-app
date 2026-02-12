from __future__ import annotations

from contextlib import asynccontextmanager
import httpx

try:
    # Redis is optional; only used when REDIS_URL is set
    from redis.asyncio import Redis  # type: ignore
except Exception:  # pragma: no cover
    Redis = None  # type: ignore

from app.config import settings


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan hook to enable graceful shutdown.

    Startup:
      - Create shared httpx.AsyncClient (reused across requests)
      - Optionally create shared Redis client
      - Initialize shutdown flag

    Shutdown:
      - Flip shutdown flag so readiness fails fast
      - Close httpx and redis connections cleanly
    """
    app.state.shutting_down = False
    app.state.http = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)

    if settings.REDIS_URL and Redis is not None:
        app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    else:
        app.state.redis = None

    try:
        yield
    finally:
        app.state.shutting_down = True
        try:
            await app.state.http.aclose()
        except Exception:
            pass
        if getattr(app.state, "redis", None):
            try:
                await app.state.redis.aclose()
            except Exception:
                pass
