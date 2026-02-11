from fastapi import FastAPI
from prometheus_client import generate_latest
from app.weather import fetch_weather
from app.cache import get,set
from app.metrics import *

app=FastAPI()

@app.get("/weather/{city}")
async def weather(city:str):
    k=f"weather:{city}"
    if get(k):
        cache_hits.inc()
        return get(k)
    cache_misses.inc()
    d=await fetch_weather(city)
    set(k,d)
    return d

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/metrics")
def metrics(): return generate_latest()
