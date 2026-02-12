# 🌦 Weather Alert Service

A production-minded Weather Alert Service demonstrating:

- Correctness & maintainability
- Redis-backed caching (with in-memory fallback)
- Comprehensive observability (Prometheus metrics + structured logs)
- Reliability patterns (timeouts, retries, circuit breaker, stale-while-revalidate)
- Graceful shutdown
- Kubernetes + Helm (bonus)
- Edge architecture awareness (CDN, DNS, WAF, etc.)

---

# 🌍 End-to-End Client → Backend Flow (AWS Example)

Below is the recommended production request path.

## 1️⃣ Client Layer
User → Browser / Mobile App / API Consumer

## 2️⃣ DNS
**Route53**
- Resolves `api.example.com`
- Health checks + routing policies (latency, failover, weighted)

## 3️⃣ CDN / Edge
**CloudFront**
- TLS termination (ACM certificate)
- Edge caching (optional for /weather if acceptable)
- Origin: ALB or API Gateway
- Reduces latency globally

## 4️⃣ WAF / DDoS Protection
- **AWS WAF** attached to CloudFront or ALB
- Blocks malicious IPs, rate-based rules
- SQLi/XSS protection
- AWS Shield Standard (automatic)

## 5️⃣ Load Balancing Layer
**Application Load Balancer (ALB)**
- Routes traffic to Kubernetes Service
- Health checks `/health`
- Supports path-based routing

Alternative:
**API Gateway** (if authentication/throttling required at edge)

## 6️⃣ Kubernetes Cluster (EKS)
Within the cluster:

- Ingress (ALB controller)
- Service (ClusterIP)
- Deployment (Weather API Pods)
- HPA (CPU or custom metrics scaling)
- PDB (minAvailable to avoid total disruption)
- NetworkPolicies (egress restriction to Redis + OpenWeather only)

## 7️⃣ Weather API Pod
FastAPI app with:

- Shared httpx client
- Redis caching
- Circuit breaker
- Retry logic (transient errors only)
- Prometheus metrics
- Structured logging
- Graceful shutdown (lifespan + SIGTERM handling)

## 8️⃣ Redis
- In-cluster Redis (demo)
- Production: AWS ElastiCache (Multi-AZ)
- Used for:
  - Cache TTL
  - Stale-while-revalidate
  - Hit/miss observability

## 9️⃣ Upstream Dependency
**OpenWeatherMap API**
- External dependency
- Timeout enforced
- Circuit breaker protects system
- Stale data served during outages

---

# 🔁 Failure Scenarios

## Upstream Down
- Retries (bounded)
- Circuit breaker opens
- Serve stale cache if within MAX_STALE_SECONDS
- Otherwise return 503

## Redis Down
- Fallback to in-memory cache
- Continue serving traffic

## Pod Termination
- Readiness returns 503
- preStop sleep for connection draining
- In-flight requests complete
- httpx + Redis connections closed cleanly

---

# 📡 Observability

## RED Metrics
- http_requests_total
- http_request_duration_seconds (p50/p95/p99 via histogram_quantile)

## Dependency Metrics
- openweather_requests_total
- openweather_request_duration_seconds
- openweather_circuit_open_total

## Cache Metrics
- weather_cache_hits_total
- weather_cache_misses_total
- weather_stale_served_total

## Protection Metrics
- rate_limited_requests_total

---

# 🧪 Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENWEATHER_API_KEY="your_key"
make run
```

Test:
```bash
curl http://localhost:8000/
curl http://localhost:8000/weather/London
curl http://localhost:8000/metrics
```

---

# ☸ Kubernetes (Bonus)

Apply manifests:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/weather-api.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/networkpolicy-egress.yaml
```

---

# 📦 Helm (Bonus)

```bash
helm upgrade --install weather charts/weather -n weather --create-namespace   -f charts/weather/values-prod.yaml   --set secrets.OPENWEATHER_API_KEY=YOUR_KEY
```

---

# 🤖 AI Usage

Full AI usage was encouraged for this task.  
AI was used to accelerate scaffolding and documentation.  
All reliability, observability, and architectural decisions were reviewed and refined manually.

---

# 🎯 Design Philosophy

This solution prioritizes:

- Resilience over freshness
- Observability over guesswork
- Controlled degradation over cascading failure
- Simplicity over over-engineering

In production, Redis would typically be managed (AWS ElastiCache Multi-AZ), and CloudFront + WAF would be configured according to organizational security standards.
