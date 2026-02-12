from app.correlation import get_request_id
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

from app.config import settings
from app.metrics import openweather_requests_total, openweather_request_duration_seconds
from app.circuit import breaker

class UpstreamError(Exception): ...
class UpstreamTimeout(Exception): ...
class CircuitOpen(Exception): ...

def _is_retryable_upstream_exception(exc: Exception) -> bool:
    """Return True only for transient failures.

    We retry on:
      - network/transport errors
      - timeouts
      - upstream 5xx
      - upstream 429 (rate limit) (optional; still bounded retries)

    We do NOT retry on:
      - 400/401/403/404 (client/config issues or not-found)
    """
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, UpstreamError) and getattr(exc, "status_code", None) is not None:
        return exc.status_code >= 500 or exc.status_code == 429
    return False



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
    # retry policy patched
    retry=retry_if_exception(_is_retryable_upstream_exception)),
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
        raise UpstreamError(f'status={r.status_code}', status_code=r.status_code)

    breaker.record_success()
    openweather_requests_total.labels('ok').inc()
    return _to_result(r.json())
