<<<<<<< HEAD
# Weather App

## Project Description
The Weather App is a web application that provides users with up-to-date weather information. Built with modern web technologies, this application fetches data from reliable weather APIs and presents it in a user-friendly interface.

## Features
- Real-time weather data
- Search for any city
- 7-day forecast
- Responsive design for mobile and desktop

## Installation Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/urraji/weather-app.git
   ```
2. Navigate to the project directory:
   ```bash
   cd weather-app
   ```
3. Install the required packages:
   ```bash
   npm install
   ```

## Usage
Run the application:
```bash
npm start
```
Open your web browser and navigate to `http://localhost:3000` to view the app.

## Contribution Guidelines
We welcome contributions! Please follow these steps:
1. Fork the repository.
2. Create a new feature branch.
3. Make your changes and commit them.
4. Push to the branch.
5. Open a Pull Request.

Thank you for considering contributing to our project!
=======
# Weather Alert Platform (Principal SRE Reference Implementation)

A production-oriented, cloud-native **Weather Alert Service** built with **FastAPI**, **Prometheus metrics**, and **Redis caching**, packaged with **Kubernetes manifests**, **Alertmanager rules**, and **synthetic monitoring**.

This repository is intentionally opinionated toward **Principal SRE thinking**:
- Explicit failure-mode handling (upstream down, cache down, overload)
- SLO-friendly observability (latency, success rate, cache hit ratio, stale-serve rate)
- Clear operational controls (timeouts, retries, circuit breaking, load shedding)
- Secure-by-default patterns (no secrets in code, correlation IDs, no API key logging)

> Edge components (DNS/CDN/S3/API Gateway/WAF/DDoS/ALB/cert-manager/Secrets Manager) are represented as architecture + integration notes. The runnable code focuses on the application + K8s runtime layer.

---

## Architecture

```
Client (Browser / Mobile / Curl)
        |
        v
DNS (Route53 / Cloudflare)
        |
        v
CDN (CloudFront / Cloudflare)  [edge cache + DDoS absorption]
        |
        v
S3 Static Website (optional UI)
        |
        v
API Gateway (auth + throttling)  ->  WAF (OWASP rules)  ->  DDoS protection (Shield)
        |
        v
ALB / Ingress (TLS via cert-manager)
        |
        v
Kubernetes (EKS/GKE/AKS)
  ├─ weather-api (FastAPI)
  │    ├─ in-memory TTL cache (fallback)
  │    ├─ Redis cache (primary)
  │    ├─ retries + timeout + circuit breaker
  │    └─ /metrics (Prometheus)
  ├─ redis-proxy (Envoy)  [optional: stable endpoint + telemetry]
  └─ redis (StatefulSet example; in prod prefer managed Redis)
        |
        v
Outbound egress firewall (allowlist OpenWeather only)
        |
        v
OpenWeather API (3rd party)
```

---

## API

### `GET /weather/{location}`
Returns current weather for a location (city string).

Response example:
```json
{
  "location": "seattle",
  "temperature": 7.2,
  "conditions": "light rain",
  "humidity": 84,
  "wind_speed": 3.6,
  "source": "cache|api|stale",
  "data_age_seconds": 12
}
```

Headers (when serving stale):
- `X-Data-Freshness: stale`
- `X-Data-Age-Seconds: <N>`

### `GET /health`
Basic service health plus cache mode.

### `GET /metrics`
Prometheus metrics endpoint.

---

## Failure handling

### If the upstream weather API is down
- short **timeouts**
- bounded **retries** (exponential backoff)
- **circuit breaker** (fast-fail)
- **stale-while-revalidate** (serve cached data within max staleness)
- **load shedding** (503 when no acceptable stale)

### If Redis is down
- fallback to **in-memory TTL cache**
- emit metrics + alert

---

## Configuration

All configuration is externalized via env vars (see `app/config.py`).

Key vars:
- `OPENWEATHER_API_KEY` (required)
- `REDIS_URL` (optional)
- `CACHE_TTL_SECONDS`, `MAX_STALE_SECONDS`
- `HTTP_TIMEOUT_SECONDS`
- circuit breaker knobs

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENWEATHER_API_KEY="..."
# optional
# export REDIS_URL="redis://localhost:6379/0"

make run
```

Test:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/weather/seattle
curl http://localhost:8000/metrics
```

---

## Kubernetes deploy (reference)

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/redis-proxy.yaml
kubectl apply -f k8s/weather-api.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/networkpolicy-egress.yaml
```

---

## Synthetic monitoring
See `synthetic/k6.js`.

---

## License
MIT
>>>>>>> a71e228 (updated)
