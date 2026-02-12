# 🌦 Weather Alert Service

A Weather Alert Service that:
1) Accepts requests for weather by location
2) Calls the OpenWeatherMap API
3) Caches responses (Redis, with in-memory fallback)
4) Implements comprehensive observability (Prometheus metrics + structured logs)
5) Handles failures gracefully (timeouts, retries, circuit breaker, stale cache, load shedding)

## Endpoints
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
