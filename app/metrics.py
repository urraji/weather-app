from prometheus_client import Counter, Histogram

# ================================
# HTTP RED Metrics (Request Layer)
# ================================

# Total HTTP requests.
# Used to calculate request rate and error rate.
# Primary input for availability SLI.
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["path", "method", "status"],
)

# HTTP request latency.
# Used for p95/p99 latency SLO monitoring.
# Key signal for user experience degradation.
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["path", "method"],
)


# ===================================
# Business-Level Metric (Weather API)
# ===================================

# Total weather endpoint requests.
# Helps separate business traffic from health/metrics endpoints.
weather_requests_total = Counter(
    "weather_requests_total",
    "Total weather requests",
)


# ============================
# Cache Effectiveness Metrics
# ============================

# Cache hits (redis or memory).
# Used to monitor cache efficiency.
# A drop in hit ratio may indicate upstream instability or TTL misconfiguration.
weather_cache_hits_total = Counter(
    "weather_cache_hits_total",
    "Weather cache hits",
    ["tier"],  # redis | memory
)

# Cache misses.
# Combined with hits to calculate cache hit ratio.
weather_cache_misses_total = Counter(
    "weather_cache_misses_total",
    "Weather cache misses",
    ["tier"],  # redis | memory
)

# Number of requests served using stale data.
# High values may indicate upstream degradation.
weather_stale_served_total = Counter(
    "weather_stale_served_total",
    "Requests served with stale cached data",
)


# ===============================
# Upstream Dependency Monitoring
# ===============================

# Upstream request outcomes.
# Tracks health of OpenWeather dependency.
# Used to alert on error rate and circuit breaker activity.
openweather_requests_total = Counter(
    "openweather_requests_total",
    "OpenWeather upstream requests",
    ["result"],  # ok | error | timeout | circuit_open
)

# Upstream latency.
# Critical for detecting dependency slowness before failures occur.
openweather_request_duration_seconds = Histogram(
    "openweather_request_duration_seconds",
    "OpenWeather upstream latency in seconds",
)

# Circuit breaker open events.
# Indicates sustained upstream instability.
# Useful for paging when breaker opens frequently.
openweather_circuit_open_total = Counter(
    "openweather_circuit_open_total",
    "Circuit breaker opened events",
)


# ======================
# Protection / Throttle
# ======================

# Requests rejected due to rate limiting.
# Detects abuse or unexpected traffic spikes.
rate_limited_requests_total = Counter(
    "rate_limited_requests_total",
    "Requests rejected due to rate limiting",
)
