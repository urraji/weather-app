import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_has_request_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health", headers={"X-Request-ID": "abc-123"})
        assert r.status_code == 200
        assert r.headers.get("X-Request-ID") == "abc-123"


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/metrics")
        assert r.status_code == 200
        assert "http_requests_total" in r.text
