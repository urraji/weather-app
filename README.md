# Weather Alert Service

A production-minded Weather Alert Service demonstrating:
- External API integration (OpenWeatherMap)
- Redis-backed caching (with in-memory fallback)
- Comprehensive observability (Prometheus metrics + structured logs)
- Reliability patterns (timeouts, retries, circuit breaker, stale-while-revalidate)
- Graceful shutdown
- Kubernetes + Helm deployment artifacts
- Optional OpenTelemetry Operator setup (no app code changes)

---

## API Endpoints

- `GET /weather/{location}`  
  Returns current weather for `location` with:
  - `temperature` (°C)
  - `conditions`
  - `humidity` (%)
  - `wind_speed` (m/s)

- `GET /health`  
  Health endpoint used for readiness/liveness checks.

- `GET /metrics`  
  Prometheus-compatible metrics.

---

## Local execution

### Prereqs
- Python 3.9+
- (Optional) Redis (Docker recommended)
- OpenWeather API key

### Get an OpenWeather API key
OpenWeatherMap requires a free API key. Create an account and generate an API key, then set it as an environment variable.

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
make run
```

### Test
```bash
curl http://localhost:8000/weather/London
curl http://localhost:8000/health
curl http://localhost:8000/metrics | head
```

---

## Configuration

All configuration is externalized via environment variables (and via ConfigMap/Secret in Kubernetes). No credentials are hardcoded.

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `OPENWEATHER_API_KEY` | ✅ | *(none)* | OpenWeather API key (**never logged**). |
| `OPENWEATHER_URL` | ❌ | `https://api.openweathermap.org/data/2.5/weather` | Upstream base URL. |
| `HTTP_TIMEOUT_SECONDS` | ❌ | `2.0` | Upstream request timeout (seconds). |
| `CACHE_TTL_SECONDS` | ❌ | `300` | Fresh cache TTL (seconds). |
| `MAX_STALE_SECONDS` | ❌ | `1800` | Maximum stale age served when upstream is failing. |
| `REDIS_URL` | ❌ | *(empty)* | Enables Redis cache if set; falls back to in-memory if Redis is unavailable. |
| `RATE_LIMIT` | ❌ | `50/minute` | Per-instance rate limit for `/weather`. |
| `CIRCUIT_BREAKER_FAILS` | ❌ | `5` | Failures before circuit opens. |
| `CIRCUIT_BREAKER_WINDOW_SECONDS` | ❌ | `30` | Rolling window for failure counting. |
| `CIRCUIT_BREAKER_OPEN_SECONDS` | ❌ | `30` | Time circuit stays open before attempting half-open. |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## Logging

- Structured JSON logs
- Correlation IDs via `X-Request-ID`:
  - If client sends `X-Request-ID`, it is preserved
  - Otherwise a UUID is generated
  - Returned in response header and included as `request_id` in logs
- Sensitive data: API keys are never logged (httpx/httpcore request logging is suppressed)

---

## Observability

Observability is implemented at two levels:
1. **Application-level metrics** (emitted by the service at `/metrics`)
2. **Platform-level metrics** (collected from Kubernetes/infrastructure)

### Application metrics (Prometheus)

**HTTP / RED**
- `http_requests_total` (counter): request rate & error rate by endpoint/status
- `http_request_duration_seconds` (histogram): latency distribution (p50/p90/p95/p99)

**Upstream dependency**
- `upstream_requests_total` (counter): external API call volume (helps spot retry amplification)
- `upstream_request_duration_seconds` (histogram): dependency latency (separate internal vs external slowdowns)
- `upstream_errors_total` (counter): dependency errors (drives alerts/circuit breaker signals)

**Cache**
- `cache_hits_total` / `cache_misses_total`: cache effectiveness; compute hit ratio
- `weather_stale_served_total`: how often stale responses are served (degraded-mode indicator)

**Protection**
- `rate_limited_requests_total`: requests rejected due to throttling (abuse/spikes signal)

### Platform-level metrics (Kubernetes & infrastructure)

These are not emitted by the app; they come from kube-state-metrics, cAdvisor, node-exporter, Metrics Server, and the HPA controller.

**Resource utilization**
- CPU: `container_cpu_usage_seconds_total`
- Memory: `container_memory_working_set_bytes`
- CPU throttling: `container_cpu_cfs_throttled_seconds_total` (common root cause of latency)

**Pod stability**
- Restarts: `kube_pod_container_status_restarts_total`
- OOM signals: `kube_pod_container_status_last_terminated_reason`

**Autoscaling**
- `kube_horizontalpodautoscaler_status_current_replicas`
- `kube_horizontalpodautoscaler_status_desired_replicas`

**Edge/Ingress (usually via ALB/WAF/Ingress metrics + logs)**
- request rate, 4xx/5xx, latency
- “top client IPs” should be derived from edge logs (avoid high-cardinality Prometheus labels)

---

## Synthetic monitoring

Synthetic monitoring validates end-to-end behavior from outside the service (or outside the cluster):

A synthetic check should:
1. Call `/weather/{known_city}`
2. Assert HTTP 200
3. Validate response schema (temperature/conditions/humidity/wind_speed)
4. Record latency and alert on failures

This catches failures metrics may miss:
- DNS issues
- Ingress / ALB routing problems
- TLS/cert issues
- upstream dependency outages (without cached fallback)
- auth/throttling misconfiguration

You can run this as:
- a Kubernetes CronJob
- an external uptime checker (Pingdom, Datadog synthetics, etc.)

---

## Reliability patterns

- **Timeouts** on upstream calls
- **Retries only for transient failures** (timeouts/transport/5xx/429); no retries on 401/403/404
- **Circuit breaker** to prevent retry storms and reduce load during upstream incidents
- **Stale- demonstrating stale-while-revalidate**: serve cached data during outages (bounded by `MAX_STALE_SECONDS`)
- **Rate limiting** to protect upstream and maintain availability under bursts
- **Graceful shutdown**:
  - readiness returns 503 when shutting down so traffic drains
  - httpx/redis clients closed cleanly
  - K8s preStop sleep for connection draining

---

## Kubernetes and Helm

### Canonical deployment
**Helm (`charts/weather/`) is the canonical deployment path.**  
The `k8s/` folder is **reference/quick-start** for reviewers and may lag behind Helm over time.

### Dev access: do you need Ingress?
Not strictly. For dev/local validation:
- `kubectl port-forward svc/weather-api 8000:80` is sufficient.

Enable Ingress in dev only if you want to validate L7 behavior (ALB routing/TLS/WAF).

### Deploy via Helm (example)
```bash
kubectl create ns weather
helm upgrade --install weather charts/weather -n weather --create-namespace   --set secrets.OPENWEATHER_API_KEY=YOUR_KEY
```

---

## OpenTelemetry (optional, no code changes)

This repo includes optional manifests for OTEL Operator-based tracing:
- `k8s/observability/otel-collector.yaml` (Collector logs spans for validation)
- `k8s/weather/instrumentation-python.yaml` (Instrumentation CR for Python)
- Helm Deployment is annotated to enable injection

See `k8s/observability/README.md` for steps.

---

## Alerting configs (illustrative)

Sample `prometheus.yaml` and `alertmanager.yaml` are included to show how the metrics can drive alerting (e.g., high 5xx rate, high p95 latency, upstream outage, stale ratio rising).

---

## Troubleshooting

### 401 Unauthorized from OpenWeather
This means the API key is invalid or not active yet. Verify directly:
```bash
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY&units=metric"
```

### “Internal Server Error” on /weather
Check:
- `OPENWEATHER_API_KEY` is set
- upstream reachable
- Redis URL (if configured) is reachable
- logs include `request_id` for correlation

---

## Repo hygiene
- Do not commit `.venv/` (ignored via `.gitignore`)
