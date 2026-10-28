#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rendered_runtime="$(mktemp)"
rendered_smoke="$(mktemp)"
trap 'rm -f "$rendered_runtime" "$rendered_smoke"' EXIT

kubectl kustomize "${repo_root}/tenants/product-team/apps/crewai/runtime" >"$rendered_runtime"
kubectl kustomize "${repo_root}/clusters/smoke" >"$rendered_smoke"

grep -q 'image: ghcr.io/justgithubaccount/app-poly-gitops-crewai:0.1.2' "$rendered_runtime"
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
grep -q 'targetRevision: v0.4.0' "$rendered_smoke"
grep -q 'targetRevision: v1.2.0' "$rendered_smoke"

if grep -Eq 'targetRevision: (main|[0-9a-f]{40})' "$rendered_smoke"; then
  echo "smoke environment contains a floating branch or opaque commit revision" >&2
  exit 1
fi
