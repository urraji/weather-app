# OpenTelemetry Operator (no code changes)

1) Install OTEL/ADOT Operator in EKS (cluster-wide).
2) Apply collector:
   kubectl create ns observability
   kubectl apply -f k8s/observability/otel-collector.yaml
3) Apply instrumentation:
   kubectl create ns weather
   kubectl apply -f k8s/weather/instrumentation-python.yaml
4) Deploy app (Helm or k8s). Deployment is already annotated at pod template level.
5) Verify collector logs:
   kubectl -n observability logs deploy/otel-gateway -f
