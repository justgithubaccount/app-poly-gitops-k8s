# GitOps Kubernetes Platform

GitOps-репозиторий для управления Kubernetes-инфраструктурой через ArgoCD.

## Архитектура

```
├── clusters/           # Конфигурации окружений
│   ├── dev/            # Development кластер
│   └── prd/            # Production кластер
├── platform/           # Платформенные компоненты
│   ├── core/           # Bootstrap ArgoCD, RBAC
│   ├── gitops/         # ApplicationSets, Image Updater
│   ├── infrastructure/ # Инфраструктура (nginx, cert-manager, storage)
│   └── observability/  # Мониторинг (Grafana, Loki, OTEL)
├── tenants/            # Приложения команд
│   └── product-team/   # Tenant: product-team
├── policies/           # OPA Rego политики
└── .github/workflows/  # CI валидация
```

## Как это работает

### App-of-Apps паттерн

1. **Root Application** (`platform/core/cluster-bootstrap/app-of-apps.yaml`) указывает на `clusters/<env>/`
2. **Kustomization** (`clusters/<env>/kustomization.yaml`) собирает все ArgoCD Applications
3. **Патчи** подставляют правильный destination кластер через `destination.yaml`

```
Git Push → ArgoCD → Sync Applications → Kubernetes
              ↑
    argocd-image-updater (автообновление образов)
```

### Sync Waves

Порядок деплоя контролируется через `argocd.argoproj.io/sync-wave`:
- `0` — Ingress, базовая инфраструктура
- `5` — Приложения (chat-api)

## Компоненты

### Infrastructure
| Компонент | Описание |
|-----------|----------|
| ingress-nginx | Ingress controller |
| cert-manager | TLS сертификаты (Let's Encrypt) |
| external-dns | DNS записи в Cloudflare |
| sealed-secrets | Шифрование секретов в git |
| external-secrets | Синхронизация секретов из внешних хранилищ |
| reflector | Репликация секретов между namespace |
| longhorn | Distributed storage |

### Observability
| Компонент | Описание |
|-----------|----------|
| Grafana | Дашборды и визуализация |
| Loki | Агрегация логов |
| OTEL Collector | Сбор телеметрии |

### AI Platform
| Компонент | Описание |
|-----------|----------|
| Open WebUI | UI для LLM моделей |

## Добавление нового приложения

1. Создай директорию в `tenants/<team>/apps/<app>/base/`
2. Добавь `application.yaml` с ArgoCD Application
3. Добавь `kustomization.yaml`
4. Включи в `clusters/<env>/kustomization.yaml`:
   ```yaml
   resources:
     - ../../tenants/<team>/apps/<app>/base
   ```

## Автообновление образов

Для автоматического обновления версий используется argocd-image-updater:

```yaml
annotations:
  argocd-image-updater.argoproj.io/image-list: app=ghcr.io/org/app:^1
  argocd-image-updater.argoproj.io/app.update-strategy: semver
  argocd-image-updater.argoproj.io/write-back-method: git
```

## CI/CD

GitHub Actions валидирует манифесты на каждый PR:

1. **Kustomize build** — рендеринг манифестов
2. **Kubeconform** — валидация против JSON схем
3. **OPA** — проверка политик безопасности

### Политики (policies/)

- Контейнеры должны иметь limits (cpu, memory)
- Обязательные probes (liveness, readiness)
- Запуск не от root (`runAsNonRoot: true`)
- Наличие namespace
- OTEL endpoint для телеметрии

## Локальная разработка

```bash
# Рендеринг манифестов
kubectl kustomize clusters/dev/

# Валидация
kubeconform -summary -strict <(kubectl kustomize clusters/dev/)

# Проверка политик
opa eval -f pretty -d policies/ -i rendered.yaml "data.kubernetes.deny[msg]"
```

## Требования

- Kubernetes кластер
- ArgoCD установлен в namespace `argocd`
- Доступ к GitHub репозиторию

## Лицензия

MIT
