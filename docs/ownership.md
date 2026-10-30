# GitOps ownership and reconciliation

This document records the Git-declared control graph. It does not assert that a
cluster exists or that any Argo CD application is currently healthy.

## Control graph

~~~text
app-poly-gitops-infra
  -> installs Argo CD
  -> creates exactly one root Application
     -> reads one reviewed clusters/<environment> root
        -> root owns raw Namespace/Ingress resources and child Application CRs
           -> each child Application owns its Helm/Kustomize payload
              -> Kubernetes controllers reconcile workload resources
~~~

Root ownership of an `Application` object is not ownership of that
Application's payload. Applying more than one root/controller can create field
ownership conflicts or allow one controller to prune resources expected by
another.

## Verified consumers and possible entrypoints

The source references below were checked against these repository revisions:

- `app-poly-gitops-k8s@8f4f31226fd591ad027750fd65e66385db58cb55`;
- `app-poly-gitops-infra@cb7c88f84e9f796e4725fc0a218fe68e3785a72e`.

`VERIFIED` means a Git consumer was found, not that reconciliation is live.
`OPTIONAL` means an explicit manual entrypoint. `SCAFFOLD` is incomplete and
must not be treated as deployable. Runtime and unobserved external use remain
`UNKNOWN`.

| Git path / consumer | Source ref | API object and reconciler | Downstream ownership | Status | External-consumer risk | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| Infra `Taskfile.yaml` -> `platform/core/cluster-bootstrap/app-of-apps.yaml` | Default `v1.5.0`; Taskfile rewrites the child source to the selected tag or full SHA | `Application/dev-cluster`, Argo CD application-controller | `clusters/dev` root | `VERIFIED` Git consumer; runtime `UNKNOWN` | Low for the file; it is the documented manual bootstrap | Retain and keep the version rewrite contract tested in infra |
| Infra `bootstrap/argocd/gitops-smoke-root.yaml` | `v1.2.0` | `Application/gitops-smoke-root` | `clusters/smoke` root | `VERIFIED` smoke bootstrap; runtime `UNKNOWN` | Low | Retain; the retained-dev workflow deliberately repoints this same object |
| Infra retained-dev workflow | Operator-selected release/commit | Patches `Application/gitops-smoke-root` | Switches the root path to `clusters/dev` | `VERIFIED` Git consumer; runtime `UNKNOWN` | Medium: changing object name/path breaks retained runs | Retain compatibility; do not create a second dev root |
| `clusters/dev/bootstrap.yaml` | Floating `main` | `Application/root-app-dev` | `clusters/dev` | `OPTIONAL`; no consumer found in the seven related repositories | `UNKNOWN`: a person may apply it manually | Keep until the operator decides whether to deprecate the public manual entrypoint |
| `clusters/{tst,stg,prd}/bootstrap.yaml` | Floating `main` | `Application/root-app-{env}` | Incomplete environment roots | `SCAFFOLD` | `UNKNOWN` | Keep out of CI/deployment; do not advertise as production-ready |
| `platform/core/cluster-bootstrap/root-app.yaml` | Floating `main` | `Application/root-app` recursively reads its own directory | Can manage itself and create `Application/dev-cluster` | `OPTIONAL`, but structurally unsafe; no related-repo consumer found | High/`UNKNOWN`: deletion may break an undocumented manual consumer | `BLOCKED`: deprecate/remove only after confirming it has never been applied or arranging a prune-safe handoff |
| `platform/gitops/appsets/infrastructure-apps.yaml` | Floating `main` | `ApplicationSet/infrastructure-apps` | Creates platform child Applications, several with the same names as `clusters/dev` children | `OPTIONAL`; not reachable from dev/smoke or infra bootstrap | High: simultaneous activation writes the same `Application` objects with different specs | Do not apply beside an environment root; retain pending an explicit controller migration |
| `platform/gitops/appsets/observability-apps.yaml` | Floating `main` | `ApplicationSet/observability-apps` | Creates `loki`, `grafana`, and `vector-gateway` Applications | `OPTIONAL`; not reachable from dev/smoke | High: collides with dev child Application identities | Retain only as migration scaffold; activation requires ownership handoff |
| `platform/gitops/appsets/tenant-apps.yaml` | Floating `main`; Helm `v0.4.0` | `ApplicationSet/tenant-apps-dev` and `ApplicationSet/tenant-apps` | Alternative FastAPI releases | `SCAFFOLD`; not reachable from supported roots and older than the active chart pin | High: separate Application names can still manage the same workload objects and prune them | Do not activate; operator must choose migration or removal after external-use confirmation |
| `platform/core/rbac/projects/*.yaml` | Repository file | `AppProject/platform` and `AppProject/tenants` | Permissions for the dormant ApplicationSets | `OPTIONAL`; not reachable from supported roots | Medium/`UNKNOWN` | Retain with the ApplicationSet migration surface; not evidence of active RBAC |

GitHub default-branch search and direct inspection covered the seven
`app-poly-gitops` repositories plus archived `app-mono-gitops`. No additional
consumer of `root-app.yaml`, the ApplicationSets, or environment bootstrap
files was found. This cannot disprove an out-of-band `kubectl apply`, an Argo CD
object created from another account, or a fork, so their external status remains
`UNKNOWN`.

## Supported root ownership

### `clusters/dev`

The root render owns six Namespace objects, three public Ingress objects, and
nine child Application objects. The child Applications own these payloads:

| Child Application | Payload owner |
| --- | --- |
| `ingress-nginx`, `cert-manager`, `external-dns` | Pinned upstream Helm charts and dev values |
| `loki`, `grafana`, `vector-gateway` | Pinned observability charts and values |
| `argocd-image-updater` | Pinned Argo Helm chart |
| `chat-api` | `app-poly-gitops-helm@v0.4.1` with dev overrides |
| `crewai` | This repository at `v1.4.2`, dev runtime overlay |

The `open-webui` Namespace is part of the dev root, but no OpenWebUI workload or
Ingress is. Namespace deletion is not a cleanup operation: Argo pruning it can
delete namespaced data or externally managed resources. Keep it until runtime
contents and all external consumers are proven empty.

### `clusters/smoke`

The root owns one Namespace plus the Jaeger Deployment/Service directly, and
owns `Application/chat-api` and `Application/crewai`. Those child Applications
own their application payloads. Smoke intentionally has no public networking,
DNS controller, Loki, Grafana, Vector, or ApplicationSet.

## Optional and scaffolded components

- Security controllers, Longhorn, OpenWebUI, the database operators, and the
  base networking resources are referenced by incomplete `tst/stg/prd` roots or
  dormant ApplicationSets. They are reusable/optional, not proven dead.
- `cnpg-cluster.yaml`, `postgres-cluster.yaml`, and the dev SealedSecret files
  are not included by the dev overlay. They may still have manual/external
  consumers; changing or deleting them requires an explicit migration decision.
- Image Updater is present in dev, and the FastAPI Application carries update
  annotations. Actual Git write-back credentials and live controller behavior
  are `UNKNOWN` without runtime evidence.
- Dify remains a documentation-only `SCAFFOLD`. Its former comment-only
  `application.yaml` produced no Kubernetes object and was removed; no deployable
  Dify configuration was invented.

## Operator decisions still required

1. Confirm whether `Application/root-app` or any ApplicationSet has ever been
   applied. If yes, inventory its managed resources/finalizers before migration;
   if no, remove the unsafe alternative entrypoints in a no-release cleanup.
2. Inspect the live `open-webui` Namespace before deciding whether its desired
   Namespace object can be removed from dev.
3. Decide whether `tst/stg/prd` should become supported environments or remain
   non-deployable scaffolds. Do not complete them implicitly during cleanup.
4. Choose one future database operator before activating either dormant custom
   resource. Do not delete the alternative merely because dev currently uses
   SQLite.
