
# Weather Alert Service

## Overview

The Weather Alert Service exposes:

- `GET /weather/{location}` – Returns temperature, conditions, humidity, and wind speed.
- `GET /health` – Health endpoint for liveness/readiness checks.
- `GET /metrics` – Prometheus-compatible metrics endpoint.

The service integrates with a third-party weather API, applies caching, and implements production-grade observability and reliability patterns.

---

# Observability

## Prometheus Metrics

The service exposes the following core metrics:

### 1. HTTP Request Metrics

**`http_requests_total` (Counter)**  
Tracks total number of HTTP requests by endpoint and status code.

**Why it matters:**  
- Detect traffic spikes  
- Calculate error rate  
- Drive SLI/SLO availability measurements  

---

**`http_request_duration_seconds` (Histogram)**  
Tracks request latency distribution.

Includes:
- p50 (50th percentile)
- p90
- p95
- p99

**Why it matters:**  
- Detect latency degradation  
- Identify tail latency issues  
- Validate performance SLOs  
- Detect downstream dependency slowdowns  

---

### 2. Upstream (Weather API) Metrics

**`upstream_requests_total` (Counter)**  
Tracks calls to the third-party weather API.

**Why it matters:**  
- Detect dependency traffic volume  
- Identify retry amplification  
- Monitor external API usage rate  

---

**`upstream_request_duration_seconds` (Histogram)**  
Measures latency of calls to the external weather provider.

**Why it matters:**  
- Detect external API slowness  
- Trigger alerts when dependency latency increases  
- Differentiate internal vs external latency  

---

**`upstream_errors_total` (Counter)**  
Counts non-success responses from the external weather API.

**Why it matters:**  
- Detect dependency outages  
- Trigger circuit breaker logic  
- Alert on error-rate SLO breaches  

---

### 3. Cache Metrics

**`cache_hits_total` (Counter)**  
Counts cache hits.

**`cache_misses_total` (Counter)**  
Counts cache misses.

**Why they matter:**  
- Calculate cache hit ratio  
- Validate cache effectiveness  
- Detect TTL misconfiguration  
- Identify traffic patterns  

---

### 4. Rate Limiting Metrics

**`rate_limited_requests_total` (Counter)**  
Counts requests rejected due to rate limiting.

**Why it matters:**  
- Detect abuse or traffic bursts  
- Validate protective throttling  
- Protect upstream API from overload  

---

# Synthetic Monitoring

Synthetic monitoring continuously validates service behavior from outside the system.

## What is implemented

A synthetic check periodically:

1. Calls `/weather/{known_city}`
2. Validates response structure
3. Ensures status code is 200
4. Measures latency

This can be deployed as:

- A Kubernetes CronJob
- An external uptime service
- A lightweight monitoring container

---

## What Synthetic Monitoring Detects

Unlike metrics, synthetic checks validate:

- End-to-end API functionality
- DNS resolution issues
- Ingress or ALB routing failures
- TLS certificate problems
- Dependency failures
- Authentication misconfiguration

Metrics may show healthy pods while traffic fails at the edge. Synthetic monitoring detects those gaps.

---

# Reliability Patterns Implemented

- Retry logic (only for transient upstream errors)
- Timeout management for external calls
- Circuit breaker behavior on repeated failures
- Rate limiting to protect dependencies
- Shared caching via Redis (or in-memory fallback)
- Graceful shutdown support
- Structured logging with correlation IDs

---

# Configuration Management

All configuration is externalized via environment variables.

No credentials are hardcoded.

Examples include:

- `WEATHER_API_KEY`
- `REDIS_URL`
- `LOG_LEVEL`
- Timeout and retry configuration
- Cache TTL configuration

---

# Deployment Strategy

Helm chart is the canonical deployment mechanism.

Raw Kubernetes manifests are included for quick inspection and validation.

---

# Production Recommendations

- Use managed Redis (e.g., AWS ElastiCache Multi-AZ)
- Use HPA for scaling
- Configure PodDisruptionBudget
- Set rolling update strategy (`maxUnavailable: 0`, `maxSurge: 1`)
- Enable OpenTelemetry tracing via Operator

---

This service demonstrates correctness, reliability, and production-grade observability practices suitable for SRE review.
