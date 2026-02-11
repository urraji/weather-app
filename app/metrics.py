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

# HTTP request latency histogram.
# Used to compute:
#   - p50 (median) latency → baseline performance
#   - p95 latency → SLO target
#   - p99 latency → tail amplification detection
#
# p50 helps detect general performance shifts.
# p95/p99 detect user-impacting slowdowns.
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["path", "method"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0),
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

# Upstream latency histogram.
# Used to compute p50/p95/p99 latency for dependency health.
# Helps detect slow dependency before outright failures.
openweather_request_duration_seconds = Histogram(
    "openweather_request_duration_seconds",
    "OpenWeather upstream latency in seconds",
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0),
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
