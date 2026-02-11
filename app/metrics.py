from prometheus_client import Counter, Histogram

http_requests_total = Counter('http_requests_total','Total HTTP requests',['path','method','status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds','HTTP request latency seconds',['path','method'])

weather_requests_total = Counter('weather_requests_total','Total weather requests')

weather_cache_hits_total = Counter('weather_cache_hits_total','Cache hits',['tier'])
weather_cache_misses_total = Counter('weather_cache_misses_total','Cache misses',['tier'])
weather_stale_served_total = Counter('weather_stale_served_total','Served stale responses')

openweather_requests_total = Counter('openweather_requests_total','Upstream requests',['result'])
openweather_request_duration_seconds = Histogram('openweather_request_duration_seconds','Upstream latency seconds')
openweather_circuit_open_total = Counter('openweather_circuit_open_total','Circuit open events')

rate_limited_requests_total = Counter('rate_limited_requests_total','Rate limited requests')
