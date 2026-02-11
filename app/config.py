from pydantic import BaseSettings
class Settings(BaseSettings):
 OPENWEATHER_API_KEY:str
 WEATHER_URL:str='https://api.openweathermap.org/data/2.5/weather'
 TIMEOUT:int=2
settings=Settings()
