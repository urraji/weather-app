from prometheus_client import Counter,Histogram
cache_hits=Counter('cache_hits_total','hits')
cache_misses=Counter('cache_misses_total','miss')
upstream_errors=Counter('openweather_errors_total','err')
