from cachetools import TTLCache
cache=TTLCache(maxsize=1000,ttl=300)
def get(k):return cache.get(k)
def set(k,v):cache[k]=v
