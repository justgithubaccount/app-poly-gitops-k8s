# Architecture

This repository is the declarative Kubernetes layer of the
`app-poly-gitops` lab. It contains desired state only; provisioning and Argo CD
bootstrap are owned by
[`app-poly-gitops-infra`](https://github.com/justgithubaccount/app-poly-gitops-infra).

## Reconciliation model

~~~mermaid
flowchart LR
    Infra[Terraform and Argo CD bootstrap] --> Argo[Argo CD]
    GitOps[clusters/dev or clusters/smoke] --> Argo
    Helm[FastAPI Helm chart] --> Argo
    Argo --> Cluster[Kubernetes resources]
    FastAPI[FastAPI image] --> Cluster
    CrewAI[CrewAI image] --> Cluster
~~~

An environment root renders Argo CD `Application` objects. Each child
application then pulls a pinned chart or a versioned path and reconciles it into
the in-cluster destination. Sync waves order Argo CD child applications; they do
not replace readiness checks inside a child chart.

## Supported environment roots

### Development

`clusters/dev` is the full application profile validated by CI. It includes:

- namespace definitions;
- ingress-nginx, cert-manager, and external-dns for the documented dev hosts;
- Loki, Grafana, and a Vector OTLP gateway;
- Argo CD Image Updater;
- the FastAPI Helm release and CrewAI runtime.

FastAPI uses local SQLite in this profile. Database operators and custom database
resources exist as optional building blocks but are not included by the dev root.
The standalone UI repository is also not included.

### Smoke

`clusters/smoke` is the bounded disposable profile used by the infrastructure
acceptance workflow. It contains FastAPI, CrewAI, and a small Jaeger deployment.
It has no public ingress, DNS automation, Grafana, Loki, or Vector.

### Scaffolding

`clusters/tst`, `clusters/stg`, and `clusters/prd` are not in the CI
Kustomize matrix. Their tenant secrets, destination setup, and operational
procedures are incomplete. Treat them as scaffolding, not deployable environment
contracts.

## Application delivery

FastAPI is rendered from
[`app-poly-gitops-helm`](https://github.com/justgithubaccount/app-poly-gitops-helm).
Environment overlays supply the image tag, provider URL/model, telemetry
endpoint, resources, and existing Secret references. CrewAI is rendered from
`tenants/product-team/apps/crewai/runtime` with environment telemetry patches.

Image Updater annotations are present on the FastAPI Argo CD application, but a
configured Git write-back credential and an active updater are required before
automatic changes can occur.

## Observability

The development profile sends OTLP/HTTP data to Vector:

~~~text
FastAPI and CrewAI
  -> Vector gateway
     -> OTLP logs to Loki
     -> OTLP traces to structured console output
     -> metrics discarded
~~~

Grafana is configured with Loki as a data source. The development profile does
not deploy Jaeger. The smoke profile instead sends traces directly to Jaeger and
does not deploy the development observability stack.

## Networking and secrets

The development profile declares three intended hosts:

- `argo.syncjob.ru`
- `grafana.syncjob.ru`
- `chat-dev.syncjob.ru`

External DNS is restricted to annotated Ingresses in `syncjob.ru`, uses
upsert-only policy, and tracks ownership with TXT records. cert-manager uses a
Cloudflare DNS-01 issuer. Fresh `cloudflare-token`, `grafana-admin`, and
`chat-api-basic-auth` Secrets must be created outside Git for a new cluster.
The provider key for FastAPI and the LLM key for CrewAI are also runtime Secrets.

See [DEV-WEBS.md](DEV-WEBS.md) for the security boundaries and exact Secret
names. No secret value is stored in this repository.

## Repository layout

~~~text
clusters/                 environment entrypoints
platform/core/            namespaces, RBAC, and bootstrap applications
platform/infrastructure/  optional platform components
platform/observability/   dev and smoke telemetry components
platform/gitops/          Argo CD automation
tenants/                  application desired state
policies/                 OPA policy
tests/                    rendered-contract checks
~~~

## Validation boundary

CI renders and validates only `dev` and `smoke`. A successful render proves
the desired state can be assembled; it does not prove a cluster, DNS record,
certificate, provider call, or telemetry backend is live.
