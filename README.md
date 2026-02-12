# Weather Alert Service

## Overview
A small, production-minded service that fetches current weather data by location, caches responses, and exposes comprehensive observability.

### Endpoints
- `GET /weather/{location}`: temperature, conditions, humidity, wind speed
- `GET /health`: service health (readiness/liveness)
- `GET /metrics`: Prometheus metrics

---

## Local execution

### Prereqs
- Python 3.9+
- OpenWeather API key (free tier)
- Optional Redis (Docker)

### Run (no Redis)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENWEATHER_API_KEY="YOUR_KEY"
make run
```

### Run (with Redis)
```bash
docker run --rm -p 6379:6379 redis:7
export REDIS_URL="redis://localhost:6379/0"
export OPENWEATHER_API_KEY="YOUR_KEY"
make run
```

### Test
```bash
curl http://localhost:8000/weather/London
curl http://localhost:8000/health
curl -s http://localhost:8000/metrics | head
```

---

## Configuration (env vars)

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `OPENWEATHER_API_KEY` | ✅ | *(none)* | Upstream API key (never logged). |
| `OPENWEATHER_URL` | ❌ | `https://api.openweathermap.org/data/2.5/weather` | Upstream URL. |
| `HTTP_TIMEOUT_SECONDS` | ❌ | `2.0` | Upstream request timeout. |
| `UPSTREAM_MAX_ATTEMPTS` | ❌ | `3` | Retry attempts (bounded). |
| `CACHE_TTL_SECONDS` | ❌ | `300` | Fresh TTL. |
| `MAX_STALE_SECONDS` | ❌ | `1800` | Max stale age served during failures. |
| `REDIS_URL` | ❌ | *(empty)* | Enables Redis cache; falls back to memory if Redis unavailable. |
| `RATE_LIMIT` | ❌ | `50/60` | Fixed-window rate limit for `/weather` per process. |
| `CIRCUIT_BREAKER_FAILS` | ❌ | `5` | Failures before opening circuit. |
| `CIRCUIT_BREAKER_OPEN_SECONDS` | ❌ | `30` | Open duration. |
| `LOG_LEVEL` | ❌ | `INFO` | Log verbosity. |

---

## Logging
- Structured JSON logs (structlog)
- Correlation ID (`X-Request-ID`) is preserved or generated and returned in responses
- Sensitive data: httpx/httpcore request logging is suppressed; API keys are never logged

---

## Metrics (application-level)

### HTTP
- `http_requests_total{method,path,status_code}`: request volume & error rate
- `http_request_duration_seconds_bucket{method,path,...}`: latency histogram  
  Use `histogram_quantile(0.50, ...)` for p50 and similarly for p95/p99.

### Upstream
- `upstream_requests_total{provider,status_class}`
- `upstream_request_duration_seconds{provider}`
- `upstream_errors_total{provider,status_code}`
- `upstream_circuit_open_total{provider}`

### Cache
- `cache_hits_total{tier}` / `cache_misses_total{tier}`
- `cache_errors_total{tier,op}`
- `weather_stale_served_total`

### Protection
- `rate_limited_requests_total{path}`

---

## Platform metrics (Kubernetes / EKS)
These are collected via kube-state-metrics, cAdvisor, node-exporter, Metrics Server, etc. (not emitted by the app):

- CPU: `container_cpu_usage_seconds_total`
- Memory: `container_memory_working_set_bytes`
- CPU throttling: `container_cpu_cfs_throttled_seconds_total`
- Restarts: `kube_pod_container_status_restarts_total`
- HPA: `kube_horizontalpodautoscaler_status_*`

Avoid “top client IPs” as Prometheus labels (high-cardinality). Derive it from edge logs (ALB/WAF/Ingress).

---

## Synthetic monitoring
A small synthetic check should periodically:
1) Call `/weather/{known_city}`
2) Assert HTTP 200
3) Validate response schema
4) Track latency and alert on failure

Run it as a K8s CronJob or external synthetic tool.

---

## Deployment manifests (Option B)
- `charts/weather/` is **canonical** (preferred for environments/GitOps)
- `k8s/` are reference manifests for quick reviewer validation

Ingress is not required for dev; port-forward is sufficient. Enable Ingress only to validate L7/ALB behavior.

---

## OpenTelemetry Operator (optional, no app code changes)
See:
- `k8s/observability/otel-collector.yaml` (collector logs spans)
- `k8s/weather/instrumentation-python.yaml` (instrumentation resource)
