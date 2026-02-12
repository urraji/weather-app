# OpenTelemetry (Operator + Collector) Manifests (EKS-friendly)

This folder contains optional manifests to enable **distributed tracing without application code changes**.

## Components
- **OpenTelemetry Operator** (installed cluster-wide; not included here)
- **Instrumentation** CR (Python auto-instrumentation)
- **OpenTelemetryCollector** CR (gateway) exporting spans to **collector logs** for easy validation

## Quickstart
1) Install OTEL/ADOT Operator in your cluster (Helm or EKS add-on).
2) Apply the collector:
   kubectl create ns observability
   kubectl apply -f k8s/observability/otel-collector.yaml

3) Apply the instrumentation:
   kubectl create ns weather
   kubectl apply -f k8s/weather/instrumentation-python.yaml

4) Weather API Deployment is annotated in YAML for injection. You can also annotate manually (example):
   kubectl -n weather annotate deploy/weather-api instrumentation.opentelemetry.io/inject-python=true --overwrite
   kubectl -n weather rollout restart deploy/weather-api

5) Verify spans in collector logs:
   kubectl -n observability logs deploy/otel-gateway -f
