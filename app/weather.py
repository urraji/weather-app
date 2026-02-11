import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

from app.config import settings
from app.metrics import openweather_requests_total, openweather_request_duration_seconds
from app.circuit import breaker

class UpstreamError(Exception): ...
class UpstreamTimeout(Exception): ...
class CircuitOpen(Exception): ...

def _to_result(payload: dict) -> dict:
    return {
        'temperature': float(payload['main']['temp']),
        'humidity': int(payload['main']['humidity']),
        'wind_speed': float(payload['wind']['speed']),
        'conditions': str(payload['weather'][0]['description']),
    }

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.2, max=1.5),
    retry=retry_if_exception_type((UpstreamError, UpstreamTimeout)),
)
async def fetch_weather(location: str) -> dict:
    if not breaker.allow():
        openweather_requests_total.labels('circuit_open').inc()
        raise CircuitOpen('circuit open')

    params = {'q': location, 'appid': settings.OPENWEATHER_API_KEY, 'units': 'metric'}
    timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS, connect=settings.HTTP_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            with openweather_request_duration_seconds.time():
                r = await client.get(settings.OPENWEATHER_URL, params=params)
        except httpx.TimeoutException as e:
            openweather_requests_total.labels('timeout').inc()
            breaker.record_failure()
            raise UpstreamTimeout(str(e))
        except httpx.HTTPError as e:
            openweather_requests_total.labels('error').inc()
            breaker.record_failure()
            raise UpstreamError(str(e))

    if r.status_code != 200:
        openweather_requests_total.labels('error').inc()
        breaker.record_failure()
        raise UpstreamError(f'status={r.status_code}')

    breaker.record_success()
    openweather_requests_total.labels('ok').inc()
    return _to_result(r.json())
