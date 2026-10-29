#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rendered_dev="$(mktemp)"
rendered_crewai="$(mktemp)"
vector_values="${repo_root}/platform/observability/opentelemetry/collector/otel-collector/values.yaml"
trap 'rm -f "${rendered_dev}" "${rendered_crewai}"' EXIT

kubectl kustomize "${repo_root}/clusters/dev" >"${rendered_dev}"
kubectl kustomize \
  "${repo_root}/tenants/product-team/apps/crewai/overlays/dev" \
  >"${rendered_crewai}"

# The dev entrypoint is the complete application cluster, not the reduced CI smoke.
grep -q 'name: chat-api' "${rendered_dev}"
grep -q 'name: crewai' "${rendered_dev}"
grep -q 'path: tenants/product-team/apps/crewai/overlays/dev' "${rendered_dev}"
grep -Fq 'targetRevision: v1.4.2' "${rendered_dev}"
if grep -q 'image: cr.jaegertracing.io/jaegertracing/jaeger:' "${rendered_dev}"; then
  echo 'dev includes a redundant Jaeger backend instead of using Vector' >&2
  exit 1
fi
grep -q 'name: loki' "${rendered_dev}"
grep -q 'name: grafana' "${rendered_dev}"
grep -q 'name: vector-gateway' "${rendered_dev}"
grep -Fq 'targetRevision: 0.60.0' "${rendered_dev}"

# Dev runs the released app and sends every OTLP signal to the existing Vector gateway.
grep -q 'tag: "1.1.2"' "${rendered_dev}"
grep -q 'OTEL_EXPORTER_OTLP_ENDPOINT: http://vector-gateway.observability.svc.cluster.local:4318' \
  "${rendered_dev}"
grep -q 'OTEL_TRACES_EXPORTER: otlp' "${rendered_dev}"
grep -q 'OTEL_LOGS_EXPORTER: otlp' "${rendered_dev}"
grep -q 'value: http://vector-gateway.observability.svc.cluster.local:4318' \
  "${rendered_crewai}"

# Vector routes logs to Loki and exposes traces on its own structured output.
grep -q 'inputs: \[otel.logs\]' "${vector_values}"
grep -q 'inputs: \[otel.traces\]' "${vector_values}"
grep -A4 '^    traces:' "${vector_values}" | grep -q 'type: console'
if grep -q 'jaeger.observability.svc.cluster.local' "${vector_values}"; then
  echo 'Vector dev config still depends on Jaeger' >&2
  exit 1
fi
grep -q 'inputs: \[otel.metrics\]' "${vector_values}"
if grep -Fq '"deployment.environment": "dev"' "${vector_values}"; then
  echo 'shared Vector config overwrites the emitting service environment' >&2
  exit 1
fi

# A clean dev cluster must not depend on a SealedSecret encrypted for another cluster.
grep -q 'type: filesystem' "${rendered_dev}"
grep -q 'persistence:' "${rendered_dev}"
grep -q 'enabled: false' "${rendered_dev}"
grep -q 'mountPath: /var/loki' "${rendered_dev}"
grep -q 'name: loki-storage' "${rendered_dev}"
grep -q 'emptyDir: {}' "${rendered_dev}"
if grep -q 'name: loki-s3-secret' "${rendered_dev}"; then
  echo 'dev Loki still depends on the old cluster-bound S3 secret' >&2
  exit 1
fi

# Root must contain only resources the base Kubernetes API and Argo CD can apply.
if grep -Eq '^kind: (Certificate|ClusterIssuer|SealedSecret|Cluster)$' "${rendered_dev}"; then
  echo 'dev root contains a custom resource before its operator CRD exists' >&2
  exit 1
fi
if grep -Eq '^  name: (longhorn|cloudnative-pg|pgo-operator)$' \
  "${rendered_dev}"; then
  echo 'dev includes platform components not required by the application runtime' >&2
  exit 1
fi

if grep -Eq 'targetRevision: (main|[0-9a-f]{40})' "${rendered_dev}"; then
  echo 'dev environment contains a floating branch or opaque commit revision' >&2
  exit 1
fi
