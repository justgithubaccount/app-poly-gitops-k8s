#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rendered_runtime="$(mktemp)"
rendered_smoke="$(mktemp)"
rendered_smoke_runtime="$(mktemp)"
trap 'rm -f "$rendered_runtime" "$rendered_smoke" "$rendered_smoke_runtime"' EXIT

kubectl kustomize "${repo_root}/tenants/product-team/apps/crewai/runtime" >"$rendered_runtime"
kubectl kustomize "${repo_root}/clusters/smoke" >"$rendered_smoke"
kubectl kustomize "${repo_root}/tenants/product-team/apps/crewai/overlays/smoke" >"$rendered_smoke_runtime"

grep -q 'image: ghcr.io/justgithubaccount/app-poly-gitops-crewai:0.1.3' "$rendered_runtime"
grep -q 'serviceAccountName: crewai' "$rendered_runtime"
grep -q 'automountServiceAccountToken: true' "$rendered_runtime"
grep -q 'runAsNonRoot: true' "$rendered_runtime"
grep -q 'readOnlyRootFilesystem: true' "$rendered_runtime"
grep -q 'name: ALLOW_MUTATING' "$rendered_runtime"
grep -q 'value: "false"' "$rendered_runtime"
grep -q 'name: OPENAI_API_KEY' "$rendered_runtime"
grep -q 'name: crewai-llm' "$rendered_runtime"
grep -q 'key: openai-api-key' "$rendered_runtime"

grep -q 'name: chat-api' "$rendered_smoke"
grep -q 'name: crewai' "$rendered_smoke"
grep -q 'targetRevision: v0.4.1' "$rendered_smoke"
grep -q 'targetRevision: v1.2.3' "$rendered_smoke"
grep -q 'path: tenants/product-team/apps/crewai/overlays/smoke' "$rendered_smoke"
grep -q 'image: cr.jaegertracing.io/jaegertracing/jaeger:2.22.0' "$rendered_smoke"
grep -q 'name: jaeger' "$rendered_smoke"
grep -q 'name: OTEL_EXPORTER_OTLP_ENDPOINT' "$rendered_smoke_runtime"
grep -q 'value: http://jaeger.observability.svc.cluster.local:4318' "$rendered_smoke_runtime"
grep -q 'name: OTEL_TRACES_EXPORTER' "$rendered_smoke_runtime"
grep -q 'value: otlp' "$rendered_smoke_runtime"

if grep -Eq 'targetRevision: (main|[0-9a-f]{40})' "$rendered_smoke"; then
  echo "smoke environment contains a floating branch or opaque commit revision" >&2
  exit 1
fi
