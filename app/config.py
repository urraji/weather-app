from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    LOG_LEVEL: str = os.getenv(\"LOG_LEVEL\", \"INFO\").upper()
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    OPENWEATHER_API_KEY  # Never log this value: str = ''
    OPENWEATHER_URL: str = 'https://api.openweathermap.org/data/2.5/weather'
    HTTP_TIMEOUT_SECONDS: float = 2.0

    CACHE_TTL_SECONDS: int = 300
    MAX_STALE_SECONDS: int = 1800
    REDIS_URL: str = ''

    RATE_LIMIT: str = '50/minute'

    CIRCUIT_BREAKER_FAILS: int = 5
    CIRCUIT_BREAKER_WINDOW_SECONDS: int = 30
    CIRCUIT_BREAKER_OPEN_SECONDS: int = 30

settings = Settings()
