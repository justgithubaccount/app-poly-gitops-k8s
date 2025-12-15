# Golden Install Guide

Руководство по чистой установке платформы с нуля.

## Prerequisites

- Timeweb Cloud account с API токеном
- Cloudflare account с API токеном для DNS
- GitHub account с PAT для ArgoCD Image Updater

## Step 1: Infrastructure (app-poly-gitops-infra)

```bash
# Clone repo
git clone https://github.com/justgithubaccount/app-poly-gitops-infra
cd app-poly-gitops-infra

# Configure environment
cp .env.example .env
# Edit .env:
# - TF_VAR_timeweb_token
# - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (S3 backend)
# - CLOUDFLARE_TOKEN
# - GITHUB_PAT / GITHUB_USERNAME

# Full setup
task up
```

## Step 2: Create Secrets

После установки sealed-secrets контроллера:

```bash
# OpenRouter API key
task seal:openrouter

# GitHub credentials for Image Updater
task seal:github

# Cloudflare token (creates in external-dns namespace, reflector copies to cert-manager)
task seal:cloudflare
```

## Step 3: Verify Installation

```bash
# Check ArgoCD status
task status

# Get ArgoCD password
task argocd-password

# Access UI
open https://argo.syncjob.ru
```

## Known Issues & Fixes

### 1. ArgoCD 502 Bad Gateway

**Причина**: Ingress с `backend-protocol: HTTPS`, но ArgoCD в insecure mode.

**Решение**: В `ingress-argo.yaml` НЕ использовать аннотацию:
```yaml
# nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"  # WRONG
```

### 2. cert-manager не видит Cloudflare token

**Причина**: Секрет не реплицирован в namespace cert-manager.

**Решение**: Добавить reflector аннотации к секрету в external-dns:
```yaml
annotations:
  reflector.v1.k8s.emberstack.com/reflection-allowed: "true"
  reflector.v1.k8s.emberstack.com/reflection-allowed-namespaces: "cert-manager"
  reflector.v1.k8s.emberstack.com/reflection-auto-enabled: "true"
  reflector.v1.k8s.emberstack.com/reflection-auto-namespaces: "cert-manager"
```

### 3. Cloudflare token key mismatch

**Причина**: cert-manager ожидает ключ `CF_API_TOKEN`, а в секрете другое имя.

**Решение**: Убедиться что секрет содержит ключ `CF_API_TOKEN`:
```yaml
stringData:
  CF_API_TOKEN: "your-token-here"
```

### 4. CRD not found errors

**Причина**: CR деплоится раньше оператора (CRD).

**Решение**: Использовать sync-waves:
```yaml
# Operator (wave 1)
annotations:
  argocd.argoproj.io/sync-wave: "1"

# CR (wave 3+)
annotations:
  argocd.argoproj.io/sync-wave: "3"
  argocd.argoproj.io/sync-options: SkipDryRunOnMissingResource=true
```

### 5. PostgreSQL connection refused

**Причина**: chat-api стартует раньше чем PostgreSQL готов.

**Решение**: Для dev окружений использовать CloudNativePG вместо Crunchy PGO:
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: chat-db-cnpg
  annotations:
    argocd.argoproj.io/sync-wave: "3"
```

Секрет для приложения: `chat-db-cnpg-app` с ключом `uri`.

### 6. OutOfSync warnings

**Нормальны для**:
- Shared resources (Ingress используемый несколькими apps)
- CRD drift (longhorn, sealed-secrets operators обновляют свои CRD)

Можно игнорировать если приложение работает корректно.

## Sync Wave Reference

| Wave | Purpose | Examples |
|------|---------|----------|
| 0 | Core resources | Namespaces |
| 1 | CRD Operators | cert-manager, sealed-secrets, cloudnative-pg, longhorn |
| 2 | Cluster-wide configs | ClusterIssuers, StorageClasses |
| 3 | Namespace resources | Secrets, ConfigMaps, Ingresses, DB Clusters |
| 5 | Applications | chat-api |

## Verification Checklist

- [ ] ArgoCD UI accessible at https://argo.syncjob.ru
- [ ] All ArgoCD applications Synced (некоторые OutOfSync warnings OK)
- [ ] cert-manager выдаёт сертификаты (check Certificate resources)
- [ ] external-dns создаёт DNS записи в Cloudflare
- [ ] longhorn storage class available (`kubectl get sc`)
- [ ] PostgreSQL cluster ready (`kubectl get cluster -n chat-api`)
- [ ] chat-api responds (`curl https://chat-dev.syncjob.ru/health`)
- [ ] Logs visible in Grafana/Loki

## Cleanup

```bash
cd app-poly-gitops-infra
task destroy
```

Это удалит Kubernetes кластер и все ресурсы в Timeweb Cloud.
