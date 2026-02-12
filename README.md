
# Weather Alert Service

## Overview

The Weather Alert Service exposes:

- `GET /weather/{location}` – Returns temperature, conditions, humidity, and wind speed.
- `GET /health` – Health endpoint for liveness/readiness checks.
- `GET /metrics` – Prometheus-compatible metrics endpoint.

The service integrates with a third-party weather API, applies caching, and implements production-grade observability and reliability patterns.

---

# Observability

Observability is implemented at two levels:

1. **Application-level metrics** (emitted by the service)
2. **Platform-level metrics** (collected from Kubernetes and infrastructure)

---

# Application Metrics

## HTTP Metrics

**`http_requests_total` (Counter)**  
Tracks total number of HTTP requests by endpoint and status code.

Used for:
- Traffic rate monitoring
- Error rate calculation
- Availability SLI measurement

---

**`http_request_duration_seconds` (Histogram)**  
Tracks request latency distribution including p50, p90, p95, p99.

Used for:
- Detecting latency regressions
- Monitoring tail latency
- Validating performance SLOs

---

## Upstream Dependency Metrics

**`upstream_requests_total` (Counter)**  
Tracks calls to the external weather API.

**`upstream_request_duration_seconds` (Histogram)**  
Measures latency of third-party API calls.

**`upstream_errors_total` (Counter)**  
Counts non-success responses from the external API.

Used for:
- Detecting dependency degradation
- Triggering circuit breaker logic
- Alerting on external failures

---

## Cache Metrics

**`cache_hits_total` (Counter)**  
**`cache_misses_total` (Counter)**  

Used to calculate cache hit ratio and validate TTL effectiveness.

---

## Rate Limiting Metrics

**`rate_limited_requests_total` (Counter)**  

Used to detect abusive traffic and validate protective throttling behavior.

---

# Platform-Level Metrics (Kubernetes & Infrastructure)

These metrics are not implemented in application code. They are collected via:

- kube-state-metrics
- cAdvisor
- node-exporter
- Metrics Server
- HPA controller

---

## Resource Utilization

**CPU Usage**
- `container_cpu_usage_seconds_total`

Used to detect CPU saturation and scaling needs.

**Memory Usage**
- `container_memory_working_set_bytes`

Used to detect memory pressure and OOM risk.

**CPU Throttling**
- `container_cpu_cfs_throttled_seconds_total`

Used to identify latency caused by CPU limits being too restrictive.

---

## Pod Stability Signals

**Pod Restarts**
- `kube_pod_container_status_restarts_total`

Used to detect crash loops, OOM kills, and probe misconfiguration.

**OOM Events**
- `kube_pod_container_status_last_terminated_reason`

Used to identify memory exhaustion issues.

---

## Scaling Signals (HPA)

If using CPU-based HPA:

- `kube_horizontalpodautoscaler_status_current_replicas`
- `kube_horizontalpodautoscaler_status_desired_replicas`

Used to observe scaling behavior and verify autoscaling decisions.

In production, scaling may also use:
- Request rate
- Latency thresholds
- Custom metrics

---

## Edge & Ingress Metrics

Collected from Ingress / Load Balancer / WAF layer:

- Request rate
- 4xx/5xx rates
- Top client IP distribution (via logs, not Prometheus labels)

High-cardinality dimensions like raw IP addresses are intentionally not emitted as application metrics.

---

# Synthetic Monitoring

Synthetic monitoring validates end-to-end system behavior from outside the cluster.

Synthetic checks:

1. Call `/weather/{known_city}`
2. Validate status code
3. Validate response structure
4. Measure latency

Synthetic monitoring detects:

- DNS issues
- Ingress or ALB misrouting
- TLS certificate problems
- Authentication failures
- Third-party dependency outages
- Full-path availability failures

Unlike metrics, synthetic monitoring validates the complete request path from client to backend.

---

# Reliability Patterns Implemented

- Retry logic (transient upstream failures only)
- Timeout management
- Circuit breaker behavior
- Rate limiting
- Shared Redis caching (or in-memory fallback)
- Graceful shutdown
- Structured logging with correlation IDs

---

# Configuration Management

All configuration is externalized via environment variables.

No credentials are hardcoded.

Examples:

- `WEATHER_API_KEY`
- `REDIS_URL`
- `LOG_LEVEL`
- Retry and timeout settings
- Cache TTL configuration

---

# Deployment Strategy

Helm chart is the canonical deployment mechanism.

Raw Kubernetes manifests are included for quick inspection and validation.

---

# Production Considerations

- Use managed Redis (e.g., AWS ElastiCache Multi-AZ)
- Define rolling update strategy (`maxUnavailable: 0`, `maxSurge: 1`)
- Configure PodDisruptionBudget
- Enable HPA
- Use OpenTelemetry Operator for tracing
- Monitor both application and platform-level metrics

