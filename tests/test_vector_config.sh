#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
values_file="${repo_root}/platform/observability/opentelemetry/collector/otel-collector/values.yaml"
rendered_chart="$(mktemp)"
vector_config="$(mktemp)"
trap 'rm -f "${rendered_chart}" "${vector_config}"' EXIT

test -f "${values_file}"

helm repo add vector https://helm.vector.dev --force-update >/dev/null
helm repo update vector >/dev/null
helm template vector-gateway vector/vector \
  --version 0.60.0 \
  --namespace observability \
  --values "${values_file}" \
  >"${rendered_chart}"

awk '
  /^  vector\.yaml: \|$/ { in_config=1; next }
  in_config && /^---$/ { exit }
  in_config { sub(/^    /, ""); print }
' "${rendered_chart}" >"${vector_config}"

test -s "${vector_config}"
docker run --rm -i timberio/vector:0.60.0-debian \
  validate --no-environment --deny-warnings --config-yaml /dev/stdin \
  <"${vector_config}"
