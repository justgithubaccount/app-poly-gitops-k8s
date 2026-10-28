#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if grep -R -q --include='*.yaml' 'ghcr.io/justgithubaccount/chat-api' \
  "${repo_root}/tenants" "${repo_root}/platform/gitops"; then
  echo "legacy chat-api image reference found" >&2
  exit 1
fi

if grep -R -q --include='*.yaml' 'path: chat' "${repo_root}/platform/gitops"; then
  echo "nonexistent Helm chart path found" >&2
  exit 1
fi

grep -q 'targetRevision: c3f071092d36b3cf02728aa7e06785a343e68f3c' \
  "${repo_root}/tenants/product-team/apps/chat/base/application.yaml"

for env in dev tst stg prd; do
  grep -q 'repository: ghcr.io/justgithubaccount/app-poly-gitops-fastapi' \
    "${repo_root}/tenants/product-team/apps/chat/overlays/${env}/values.yaml"
  kubectl kustomize "${repo_root}/tenants/product-team/apps/chat/overlays/${env}" >/dev/null
done
