from prometheus_client import Counter, Histogram

# HTTP server metrics (RED)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency seconds (use histogram_quantile for p50/p95/p99)",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

# Upstream dependency metrics
UPSTREAM_REQUESTS_TOTAL = Counter(
    "upstream_requests_total",
    "Total upstream requests to weather provider",
    ["provider", "status_class"],
)
UPSTREAM_REQUEST_DURATION = Histogram(
    "upstream_request_duration_seconds",
    "Upstream request latency seconds",
    ["provider"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
UPSTREAM_ERRORS_TOTAL = Counter(
    "upstream_errors_total",
    "Total upstream errors (non-2xx)",
    ["provider", "status_code"],
)

# Cache metrics
CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Cache hits",
    ["tier"],  # redis|memory
)
CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Cache misses",
    ["tier"],
)
CACHE_ERRORS_TOTAL = Counter(
    "cache_errors_total",
    "Cache read/write errors",
    ["tier", "op"],  # get|set
)
STALE_SERVED_TOTAL = Counter(
    "weather_stale_served_total",
    "Stale responses served due to upstream failure",
)

# Rate limiting
RATE_LIMITED_TOTAL = Counter(
    "rate_limited_requests_total",
    "Requests rejected by rate limiting",
    ["path"],
)

# Circuit breaker
CIRCUIT_OPEN_TOTAL = Counter(
    "upstream_circuit_open_total",
    "Number of times upstream circuit is open when request attempted",
    ["provider"],
)
