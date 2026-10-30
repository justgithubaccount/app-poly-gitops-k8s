# Kubernetes GitOps Platform

Argo CD desired state for the `app-poly-gitops` engineering lab. The repository
assembles application, networking, observability, and GitOps components with
Kustomize.

## Overview

Two environment roots are active and validated in CI:

| Root | Purpose | Included services |
| --- | --- | --- |
| `clusters/dev` | Complete application development profile | FastAPI, CrewAI, ingress-nginx, cert-manager, external-dns, Loki, Grafana, Vector, image updater |
| `clusters/smoke` | Small disposable acceptance profile | FastAPI, CrewAI, and Jaeger |

`clusters/tst`, `clusters/stg`, and `clusters/prd` are retained scaffolding.
They contain incomplete environment wiring and are not validated by the current
CI matrix. The additional operators under `platform/` are reusable building
blocks, not evidence that they are enabled in either active root.

No running cluster is implied by this repository. Argo CD applies an environment
only after a separately authorized provisioning and bootstrap step.

## Architecture

Argo CD reads one `clusters/<environment>` Kustomize root. That root renders
Argo CD `Application` objects for platform and tenant components. The FastAPI
application is packaged by
[app-poly-gitops-helm](https://github.com/justgithubaccount/app-poly-gitops-helm);
CrewAI uses manifests stored in this repository.

The dev telemetry path is:

~~~text
FastAPI / CrewAI -> OTLP/HTTP -> Vector
                                |-> logs -> Loki -> Grafana
                                `-> traces -> structured Vector output
~~~

The smoke root uses a small Jaeger deployment instead. See
[docs/architecture.md](docs/architecture.md) for component boundaries.

## Getting started

Requirements: `kubectl` with Kustomize support, Helm 3, OPA, Node.js 22.22.2,
Python 3, and optionally `kubeconform`. The networking test pins
`PyYAML==6.0.2`.

Render the CI-supported roots without contacting a cluster:

~~~bash
kubectl kustomize clusters/dev > /tmp/app-poly-dev.yaml
kubectl kustomize clusters/smoke > /tmp/app-poly-smoke.yaml
~~~

Run repository contracts:

~~~bash
bash tests/test_chat_contract.sh
bash tests/test_crewai_contract.sh
bash tests/test_dev_contract.sh
bash tests/test_vector_config.sh
python3 -m venv /tmp/app-poly-manifest-validation
/tmp/app-poly-manifest-validation/bin/python -m pip install 'PyYAML==6.0.2'
/tmp/app-poly-manifest-validation/bin/python tests/test_dev_networking.py
npm ci --ignore-scripts
node tests/test_release_notes.mjs
~~~

Parse and evaluate the Rego policy:

~~~bash
opa check policies
/tmp/app-poly-manifest-validation/bin/python \
  scripts/validate_opa_manifests.py /tmp/app-poly-dev.yaml policies
~~~

The validator evaluates every Kubernetes resource in the multi-document render
separately and exits non-zero when any document violates a policy.

These checks do not provision infrastructure or mutate Kubernetes.

## Repository structure

- `clusters/` — environment entrypoints
- `platform/core/` — namespaces, RBAC, and root applications
- `platform/infrastructure/` — optional networking, security, storage, database, and AI components
- `platform/observability/` — Loki, Grafana, Vector, and smoke Jaeger definitions
- `platform/gitops/` — image updater and ApplicationSet definitions
- `tenants/` — FastAPI and CrewAI applications plus team scaffolding
- `policies/` — OPA validation policy
- `tests/` — rendered-contract and release checks

## Documentation

- [Architecture](docs/architecture.md)
- [Golden install](docs/golden-install.md)
- [Dev web entrypoints](docs/DEV-WEBS.md)

## Related repositories

- [app-poly-gitops-infra](https://github.com/justgithubaccount/app-poly-gitops-infra) — Timeweb provisioning and Argo CD bootstrap
- [app-poly-gitops-helm](https://github.com/justgithubaccount/app-poly-gitops-helm) — FastAPI chart
- [app-poly-gitops-fastapi](https://github.com/justgithubaccount/app-poly-gitops-fastapi) — chat backend
- [app-poly-gitops-crewai](https://github.com/justgithubaccount/app-poly-gitops-crewai) — Kubernetes automation service
- [app-poly-gitops-ui](https://github.com/justgithubaccount/app-poly-gitops-ui) — standalone frontend; not deployed by the current roots
- [app-mono-gitops](https://github.com/justgithubaccount/app-mono-gitops) — archived predecessor

## License

MIT
