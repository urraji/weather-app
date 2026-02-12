# 🌦 Weather Alert Service

A Weather Alert Service that:
1) Accepts requests for weather by location
2) Calls the OpenWeatherMap API
3) Caches responses (Redis, with in-memory fallback)
4) Implements comprehensive observability (Prometheus metrics + structured logs)
5) Handles failures gracefully (timeouts, retries, circuit breaker, stale cache, load shedding)

## Endpoints

## Configuration

All configuration is externalized via environment variables (and via ConfigMap/Secret in Kubernetes).

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `OPENWEATHER_API_KEY` | ✅ | *(none)* | OpenWeather API key (never logged). |
| `OPENWEATHER_URL` | ❌ | `https://api.openweathermap.org/data/2.5/weather` | Upstream base URL. |
| `HTTP_TIMEOUT_SECONDS` | ❌ | `2.0` | Upstream request timeout (seconds). |
| `CACHE_TTL_SECONDS` | ❌ | `300` | Fresh cache TTL (seconds). |
| `MAX_STALE_SECONDS` | ❌ | `1800` | Maximum stale age served when upstream is failing. |
| `REDIS_URL` | ❌ | *(empty)* | If set, enables Redis caching (fallback to in-memory if Redis unavailable). |
| `RATE_LIMIT` | ❌ | `50/minute` | Per-instance request rate limit for `/weather`. |
| `CIRCUIT_BREAKER_FAILS` | ❌ | `5` | Failures before circuit opens. |
| `CIRCUIT_BREAKER_WINDOW_SECONDS` | ❌ | `30` | Rolling window for failure counting. |
| `CIRCUIT_BREAKER_OPEN_SECONDS` | ❌ | `30` | Time circuit stays open before attempting half-open. |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

- `GET /weather/{location}` → temperature, conditions, humidity, wind_speed (+ source + age)
- `GET /health` → service health
- `GET /metrics` → Prometheus metrics

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENWEATHER_API_KEY="..."
# Optional Redis:
# export REDIS_URL="redis://localhost:6379/0"

make run
```

## Tests
```bash
make test
```

## Alerting configs
- `prometheus.yaml`
- `alertmanager.yaml`

## Kubernetes (bonus)
Reference manifests live in `k8s/` (Deployment, Service, HPA, PDB, probes, ConfigMap/Secret, Redis).

> In production, Redis would typically be managed (e.g., AWS ElastiCache Multi-AZ).

## Helm (bonus, minimal)
A minimal Helm chart is included under `charts/weather/` to avoid environment drift.

Dev:
```bash
helm upgrade --install weather charts/weather -n weather --create-namespace \
  -f charts/weather/values-dev.yaml \
  --set secrets.OPENWEATHER_API_KEY=YOUR_KEY
```

Prod:
```bash
helm upgrade --install weather charts/weather -n weather --create-namespace \
  -f charts/weather/values-prod.yaml \
  --set secrets.OPENWEATHER_API_KEY=YOUR_KEY
```

## AI assistance
Full AI usage is allowed for this task. I used an LLM to accelerate scaffolding and then reviewed/refined the implementation focusing on correctness, reliability behavior, and observability.


## Correlation IDs
Every request uses `X-Request-ID` as a correlation ID. If provided by the client, it is preserved; otherwise a UUID is generated and returned in the response. Logs include `request_id` for minimal request tracing.


## OpenTelemetry tracing (bonus, no code changes)

This repo includes optional Kubernetes manifests to enable distributed tracing via the **OpenTelemetry Operator**:

- `k8s/observability/otel-collector.yaml`: Collector gateway that receives OTLP and logs spans (easy validation).
- `k8s/weather/instrumentation-python.yaml`: Instrumentation CR for Python auto-instrumentation.
- Annotate the Weather API Deployment with `instrumentation.opentelemetry.io/inject-python: "true"` to enable injection.

See `k8s/observability/README.md` for steps.

---

## Deployment manifests: Helm is canonical (Option B)

This repo includes **both**:
- `charts/weather/` — **canonical** deployment artifacts (recommended for real environments, GitOps, multi-env values).
- `k8s/` — **reference / quick-start** manifests for reviewers (useful to quickly see/read probes, HPA, PDB, etc.).

**Source of truth:** treat **Helm (`charts/weather/`)** as the maintained deployment path. The `k8s/` folder is provided for clarity and fast validation and may lag behind Helm if you evolve the chart.

### Dev ingress: do you need it?
Not strictly.

For **local/dev** you can usually skip an Ingress and use one of:
- `kubectl port-forward svc/weather-api 8000:80`
- `kubectl proxy`
- `NodePort` (if you want cluster-external access without L7)

Enable Ingress in dev only if you specifically want to validate edge/L7 behavior (e.g., ALB routing, TLS, WAF integration). In the Helm chart, dev values typically default to **Ingress disabled**; you can turn it on via values:

```yaml
ingress:
  enabled: true
  host: weather.dev.example.com
  certificateArn: ""   # optional for dev
```

> In EKS, ALB Ingress requires AWS Load Balancer Controller. For an interview take-home, port-forward is usually sufficient for dev validation.

