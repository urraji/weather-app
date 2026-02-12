import os


def _get_int(name: str, default: int) -> int:
    v = os.getenv(name)
    return int(v) if v is not None and v != "" else default


def _get_float(name: str, default: float) -> float:
    v = os.getenv(name)
    return float(v) if v is not None and v != "" else default


class Settings:
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Upstream (OpenWeather)
    # Never log this value
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_URL: str = os.getenv("OPENWEATHER_URL", "https://api.openweathermap.org/data/2.5/weather")

    # Timeouts / retries
    HTTP_TIMEOUT_SECONDS: float = _get_float("HTTP_TIMEOUT_SECONDS", 2.0)
    UPSTREAM_MAX_ATTEMPTS: int = _get_int("UPSTREAM_MAX_ATTEMPTS", 3)

    # Cache
    CACHE_TTL_SECONDS: int = _get_int("CACHE_TTL_SECONDS", 300)
    MAX_STALE_SECONDS: int = _get_int("MAX_STALE_SECONDS", 1800)
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Rate limiting (simple fixed window per process for /weather)
    # Format: "<requests>/<seconds>" e.g. "50/60"
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "50/60")

    # Circuit breaker
    CIRCUIT_BREAKER_FAILS: int = _get_int("CIRCUIT_BREAKER_FAILS", 5)
    CIRCUIT_BREAKER_OPEN_SECONDS: int = _get_int("CIRCUIT_BREAKER_OPEN_SECONDS", 30)


settings = Settings()
