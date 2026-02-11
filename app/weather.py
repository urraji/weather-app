import httpx
from tenacity import retry, stop_after_attempt
from app.config import settings
from app.metrics import upstream_errors

@retry(stop=stop_after_attempt(3))
async def fetch_weather(city):
    params={"q":city,"appid":settings.OPENWEATHER_API_KEY,"units":"metric"}
    async with httpx.AsyncClient(timeout=settings.TIMEOUT) as c:
        r=await c.get(settings.WEATHER_URL,params=params)
    if r.status_code!=200:
        upstream_errors.inc()
        raise Exception()
    d=r.json()
    return {
      "temperature":d["main"]["temp"],
      "humidity":d["main"]["humidity"],
      "wind_speed":d["wind"]["speed"],
      "conditions":d["weather"][0]["description"]
    }
