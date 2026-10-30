# CLAUDE.md

## Назначение

Репозиторий хранит декларативное Kubernetes/Argo CD desired state для
`app-poly-gitops`. Наличие манифеста не доказывает, что ресурс развёрнут или
работает в живом кластере.

Текущие CI-supported roots:

- `clusters/dev` — FastAPI, CrewAI, networking, Loki, Grafana, Vector и Image
  Updater;
- `clusters/smoke` — FastAPI, CrewAI и локальный Jaeger;
- `clusters/tst`, `clusters/stg`, `clusters/prd` — неполные scaffolds.

Полная карта bootstrap, root Applications, ApplicationSets, child ownership и
prune-рисков: [`docs/ownership.md`](../docs/ownership.md). Не активируй
ApplicationSets или альтернативный `root-app.yaml` параллельно с environment
root без отдельной миграции ownership.

Компоненты под `platform/infrastructure/` могут быть optional/scaffold даже если
их манифесты существуют. Не называй их deployed без runtime evidence. UI остаётся
standalone и текущими roots не разворачивается.

## Offline-проверка

```bash
kubectl kustomize clusters/dev > /tmp/app-poly-dev.yaml
kubectl kustomize clusters/smoke > /tmp/app-poly-smoke.yaml

bash tests/test_chat_contract.sh
bash tests/test_crewai_contract.sh
bash tests/test_dev_contract.sh
bash tests/test_vector_config.sh

python3 -m venv /tmp/app-poly-manifest-validation
/tmp/app-poly-manifest-validation/bin/python -m pip install 'PyYAML==6.0.2'
/tmp/app-poly-manifest-validation/bin/python tests/test_dev_networking.py
/tmp/app-poly-manifest-validation/bin/python tests/test_gitops_ownership.py
/tmp/app-poly-manifest-validation/bin/python tests/test_opa_multidoc.py -v

opa check policies
/tmp/app-poly-manifest-validation/bin/python \
  scripts/validate_opa_manifests.py /tmp/app-poly-dev.yaml policies
kubeconform -summary -strict \
  -skip Application,ApplicationSet,Certificate,ClusterIssuer,SealedSecret,PostgresCluster,Cluster \
  /tmp/app-poly-dev.yaml
```

OPA должен получать каждый документ через `scripts/validate_opa_manifests.py`;
передавать multi-document render напрямую как один `opa eval -i` нельзя.

## Границы изменений

- Сначала установи точного Git/Argo владельца объекта и downstream payload.
- Не удаляй Namespace, Secret, CR или optional operator только из-за отсутствия
  в dev/smoke.
- Не меняй chart/image/source revision без отдельного release/deployment решения.
- Render и CI доказывают только корректность desired state, не convergence.
- Никаких `kubectl apply/edit/patch/delete`, Argo sync или cloud workflow в
  рамках repository validation.
