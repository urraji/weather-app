
# Weather Alert Service

## Application-Level Metrics (Detailed Explanation)

The `/metrics` endpoint exposes Prometheus-compatible metrics focused strictly on **application behavior**.

These metrics answer:

- Is the API healthy?
- Is it fast?
- Is the dependency healthy?
- Is caching effective?
- Are protection mechanisms activating?

They intentionally **do not include CPU/memory** metrics (those belong to Kubernetes/container telemetry).

---

# 1️⃣ HTTP (RED) Metrics

## http_requests_total

Type: Counter  
Labels: `method`, `path`, `status_code`

What it measures:
- Total number of HTTP requests processed.

Why it matters:
- Traffic volume trends
- Error rate calculation
- Availability SLI

Example PromQL:

Error rate:
```
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

Request rate:
```
sum(rate(http_requests_total[1m]))
```

---

## http_request_duration_seconds

Type: Histogram  
Labels: `method`, `path`

What it measures:
- Latency distribution of HTTP requests.

Why it matters:
- Detect performance degradation
- Identify tail latency issues
- Validate SLO targets

This histogram supports percentiles using:

p50:
```
histogram_quantile(0.50,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

p95:
```
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

p99:
```
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

---

# 2️⃣ Upstream Dependency Metrics

These measure interaction with OpenWeather (or equivalent provider).

## upstream_requests_total

Type: Counter  
Labels: `provider`, `status_class`

What it measures:
- Total outbound API calls.
- Broken down by 2xx/4xx/5xx class.

Why it matters:
- Detect retry amplification
- Detect upstream instability
- Capacity planning for dependency

---

## upstream_request_duration_seconds

Type: Histogram  
Labels: `provider`

What it measures:
- Latency of calls to external weather API.

Why it matters:
- Separate internal latency from dependency latency
- Identify external degradation early

---

## upstream_errors_total

Type: Counter  
Labels: `provider`, `status_code`

What it measures:
- Non-200 upstream responses.

Why it matters:
- Detect dependency outage
- Trigger alerting
- Drive circuit breaker decisions

---

## upstream_circuit_open_total

Type: Counter  
Labels: `provider`

What it measures:
- Number of times a request was blocked due to circuit breaker being open.

Why it matters:
- Indicates upstream instability
- Signals protective mode engagement

---

# 3️⃣ Cache Metrics

## cache_hits_total
## cache_misses_total

Type: Counter  
Labels: `tier` (memory | redis)

What they measure:
- Cache efficiency.

Why it matters:
- High hit ratio reduces upstream load
- Validates TTL configuration

Cache hit ratio:

```
sum(rate(cache_hits_total[5m]))
/
(
  sum(rate(cache_hits_total[5m]))
  +
  sum(rate(cache_misses_total[5m]))
)
```

---

## cache_errors_total

Type: Counter  
Labels: `tier`, `op` (get|set)

What it measures:
- Redis or memory cache failures.

Why it matters:
- Detect Redis connectivity issues
- Detect serialization bugs

---

## weather_stale_served_total

Type: Counter

What it measures:
- Number of times stale data was served during upstream failure.

Why it matters:
- Indicates degraded mode
- Useful for alerting if serving stale frequently

Example alert signal:

```
rate(weather_stale_served_total[10m]) > 0.1
```

---

# 4️⃣ Rate Limiting Metrics

## rate_limited_requests_total

Type: Counter  
Labels: `path`

What it measures:
- Requests rejected due to throttling.

Why it matters:
- Detect abuse or burst traffic
- Validate protection mechanisms
- Prevent upstream overload

---

# 5️⃣ What These Metrics Enable

Together, these metrics enable:

- RED monitoring (Rate, Errors, Duration)
- Dependency health monitoring
- Cache efficiency monitoring
- Degraded mode detection
- Circuit breaker visibility
- SLO calculation
- Alerting and paging decisions

---

# 6️⃣ What Is NOT Included (By Design)

These are intentionally NOT application metrics:

- CPU usage
- Memory usage
- Pod restarts
- CPU throttling
- HPA replica counts

Those belong to Kubernetes/platform telemetry and should be scraped via:

- kube-state-metrics
- cAdvisor
- node-exporter
- Metrics Server

---

This separation keeps the application responsible for logical correctness and behavior, while the platform handles resource and runtime telemetry.
