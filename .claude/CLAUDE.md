# CLAUDE.md

## Обзор проекта

GitOps-репозиторий для управления Kubernetes через ArgoCD. Использует App-of-Apps паттерн с Kustomize для управления несколькими окружениями.

**Домен:** syncjob.ru

## Структура

```
clusters/       # Точки входа для каждого окружения (dev, prd)
platform/       # Платформенные компоненты
  core/           # namespaces, cluster-bootstrap
  infrastructure/ # security, networking, storage, database, ai-platform
  observability/  # monitoring (loki, grafana), opentelemetry
  gitops/         # argocd-image-updater
tenants/        # Приложения команд (product-team/apps/chat)
policies/       # OPA Rego политики для валидации
```

## Ключевые файлы

- `clusters/<env>/kustomization.yaml` — главный файл окружения, собирает все ресурсы
- `clusters/<env>/destination.yaml` — патч для подстановки имени кластера
- `platform/core/cluster-bootstrap/app-of-apps.yaml` — root ArgoCD Application
- `platform/gitops/appsets/` — ApplicationSets для генерации Applications

## Паттерны

### ArgoCD Application
Каждый компонент — это ArgoCD Application в `base/application.yaml`:
- Helm charts указываются через `spec.source.repoURL` + `chart`
- Kustomize через `spec.source.path`
- `destination.name: CLUSTER` — placeholder, заменяется патчем

### Sync Waves
`argocd.argoproj.io/sync-wave: "N"` — порядок деплоя (меньше = раньше)

### Image Updater
Аннотации для автообновления образов:
```yaml
argocd-image-updater.argoproj.io/image-list: alias=registry/image:^1
argocd-image-updater.argoproj.io/alias.update-strategy: semver
argocd-image-updater.argoproj.io/write-back-method: git
```

## Команды

```bash
# Рендер манифестов
kubectl kustomize clusters/dev/

# Валидация
kubeconform -summary -strict rendered.yaml

# Проверка политик
opa eval -f pretty -d policies/ -i rendered.yaml "data.kubernetes.deny[msg]"
```

## Добавление компонента

1. Создай `platform/infrastructure/<category>/<name>/base/`
2. Добавь `application.yaml` и `kustomization.yaml`
3. Включи в `clusters/<env>/kustomization.yaml`

## Добавление tenant приложения

1. Создай `tenants/<team>/apps/<app>/base/`
2. Добавь Application с нужными аннотациями
3. Включи в `clusters/<env>/kustomization.yaml`

## Развёрнутые компоненты

**Networking:**
- ingress-nginx — LoadBalancer ingress controller
- cert-manager — Let's Encrypt сертификаты через DNS challenge (letsencrypt-dns ClusterIssuer)
- external-dns — автоматическое управление DNS записями в Cloudflare

**Security:**
- sealed-secrets — шифрование секретов (kubeseal)
- reflector — репликация секретов между namespaces
- external-secrets — получение секретов из внешних хранилищ

**Storage:**
- longhorn — distributed block storage

**Database:**
- pgo-operator — Crunchy PostgreSQL Operator (Patroni-based, enterprise-grade)
- cloudnative-pg — CloudNativePG Operator (simple, lightweight, рекомендуется для dev)

**Observability:**
- loki — логирование
- grafana — дашборды
- vector-gateway — сбор логов
- otel-collector — OpenTelemetry collector (OTLP → Loki)

**AI Platform:**
- open-webui — веб-интерфейс для LLM

## SealedSecrets

Секреты шифруются в `app-poly-gitops-infra` репе через `task seal:*` команды.
Reflector аннотации используются для репликации между namespaces (например cloudflare-token из external-dns в cert-manager).

## Важно

- Все Applications деплоятся в namespace `argocd`
- Секреты шифруются через sealed-secrets с reflector для репликации
- Политики в `policies/kubernetes.rego` проверяются в CI
- sync-wave аннотации критичны для правильного порядка деплоя CRD-зависимых ресурсов

## Golden Install — важные настройки

1. **ArgoCD Ingress** (ingress-argo.yaml) — НЕ использовать `backend-protocol: HTTPS` (ArgoCD в insecure mode).

2. **CloudNativePG Cluster** — создаёт секрет `<cluster-name>-app` с ключом `uri` для DATABASE_URL.

3. **OutOfSync warnings** — нормальны для:
   - Shared resources (например Ingress используемый несколькими apps)
   - CRD drift (longhorn, sealed-secrets operators)

4. **OpenTelemetry pipeline**: chat-api SDK → OTel Collector (OTLP) → Loki → Grafana
   - Логи содержат trace_id, span_id, k8s metadata

5. **Cloudflare token** — ключ в секрете: `CF_API_TOKEN`. Reflector реплицирует из external-dns в cert-manager namespace.
