# CLAUDE.md

## Обзор проекта

GitOps-репозиторий для управления Kubernetes через ArgoCD. Использует App-of-Apps паттерн с Kustomize для управления несколькими окружениями.

## Структура

```
clusters/       # Точки входа для каждого окружения (dev, prd)
platform/       # Платформенные компоненты (infra, observability, gitops)
tenants/        # Приложения команд
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

## Важно

- Все Applications деплоятся в namespace `argocd`
- Секреты шифруются через sealed-secrets или тянутся через external-secrets
- Политики в `policies/kubernetes.rego` проверяются в CI
