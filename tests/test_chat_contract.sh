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

grep -q 'targetRevision: v0.4.0' \
  "${repo_root}/tenants/product-team/apps/chat/base/application.yaml"
awk '
  /repoURL: https:\/\/github.com\/justgithubaccount\/app-poly-gitops-helm/ {
    getline
    if ($0 !~ /targetRevision: v0.4.0/) exit 1
    helm_sources++
  }
  /repoURL: https:\/\/github.com\/justgithubaccount\/app-poly-gitops-k8s/ {
    getline
    if ($0 !~ /targetRevision: main/) exit 1
    values_sources++
  }
  END { if (helm_sources != 2 || values_sources != 2) exit 1 }
' "${repo_root}/platform/gitops/appsets/tenant-apps.yaml"
grep -q 'PostgresCluster,Cluster' "${repo_root}/.github/workflows/validate.yaml"

for env in dev tst stg prd; do
  grep -q 'repository: ghcr.io/justgithubaccount/app-poly-gitops-fastapi' \
    "${repo_root}/tenants/product-team/apps/chat/overlays/${env}/values.yaml"
  kubectl kustomize "${repo_root}/tenants/product-team/apps/chat/overlays/${env}" >/dev/null
done
