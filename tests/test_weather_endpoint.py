import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def _set_key(monkeypatch):
    monkeypatch.setattr(settings, 'OPENWEATHER_API_KEY', 'testkey')

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

@respx.mock
def test_weather_success_then_cache():
    route = respx.get(settings.OPENWEATHER_URL).mock(
        return_value=Response(200, json={'main': {'temp': 10.0, 'humidity': 80}, 'wind': {'speed': 3.2}, 'weather': [{'description': 'clear sky'}]})
    )

    r1 = client.get('/weather/seattle')
    assert r1.status_code == 200
    assert r1.json()['source'] == 'api'
    assert route.called

    r2 = client.get('/weather/seattle')
    assert r2.status_code == 200
    assert r2.json()['source'] == 'cache'

@respx.mock
def test_weather_upstream_failure_returns_503_without_cache():
    respx.get(settings.OPENWEATHER_URL).mock(return_value=Response(500, json={'err': 'nope'}))
    r = client.get('/weather/nowhere')
    assert r.status_code == 503
