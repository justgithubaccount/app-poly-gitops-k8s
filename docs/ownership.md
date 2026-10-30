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

The source references below were checked against these `main` snapshots before
this documentation-only update:

- `app-poly-gitops-k8s@2033b80531de7294bb7cafe64c0488ca6b51146d`;
- `app-poly-gitops-infra@cb7c88f84e9f796e4725fc0a218fe68e3785a72e`.

The classification vocabulary is intentionally fail-closed:

- `VERIFIED_GIT_CONSUMER` means an exact Git consumer was found, not that
  reconciliation is live;
- `OPTIONAL` means an explicit reusable or manual entrypoint;
- `SCAFFOLD` is incomplete and must not be treated as deployable;
- `UNKNOWN_EXTERNAL` means static repository searches cannot rule out an
  out-of-band apply, another account, or a fork;
- `SAFE_TO_DELETE` requires both no Git consumer and evidence excluding live or
  external ownership. No remaining item in this ledger meets that bar.

| Git path / consumer | Source ref | API object -> watcher -> payload | Sync, prune, and finalizer consequence | Classification | Recommended action |
| --- | --- | --- | --- | --- | --- |
| Infra `Taskfile.yaml` -> `platform/core/cluster-bootstrap/app-of-apps.yaml` | Default `v1.5.0`; Taskfile rewrites the child source to a selected release tag or full SHA | `Application/dev-cluster` -> Argo CD application-controller -> `clusters/dev` root resources and child Applications | Automated prune/self-heal; root finalizer cascades deletion to root-owned objects | `VERIFIED_GIT_CONSUMER`; runtime `UNKNOWN` | Retain and keep the version rewrite contract tested in infra |
| Infra `bootstrap/argocd/gitops-smoke-root.yaml` | `v1.2.0` | `Application/gitops-smoke-root` -> application-controller -> `clusters/smoke` root | Automated prune/self-heal; finalizer cascades deletion | `VERIFIED_GIT_CONSUMER`; runtime `UNKNOWN` | Retain; the retained-dev workflow deliberately reuses this object |
| Infra retained-dev workflow | Operator-selected release/commit | patches `Application/gitops-smoke-root` -> application-controller -> switches payload to `clusters/dev` | Same object changes payload ownership; a second root would create prune/field collisions | `VERIFIED_GIT_CONSUMER`; runtime `UNKNOWN` | Retain compatibility; do not create a second dev root |
| `clusters/dev/bootstrap.yaml` | Floating `main` | `Application/root-app-dev` -> application-controller -> `clusters/dev` | Automated prune/self-heal and finalizer; activation beside `dev-cluster` duplicates ownership | `OPTIONAL` + `UNKNOWN_EXTERNAL` | Keep until the operator deprecates the public manual entrypoint with a prune-safe handoff |
| `clusters/{tst,stg,prd}/bootstrap.yaml` | Floating `main` | `Application/root-app-{env}` -> application-controller -> incomplete environment roots | Automated prune/self-heal and finalizer can create or delete partial platform payloads | `SCAFFOLD` + `UNKNOWN_EXTERNAL` | Keep out of CI/deployment; do not advertise as production-ready |
| `platform/core/cluster-bootstrap/root-app.yaml` | Floating `main` | `Application/root-app` -> application-controller -> recursively reads its own directory and creates `dev-cluster` | Self-management plus prune can remove its child root; no finalizer on `root-app`, but `dev-cluster` has one | `OPTIONAL` + `UNKNOWN_EXTERNAL`; structurally unsafe | `BLOCKED_FOR_OPERATOR`: remove only after proving it was never applied or arranging a prune-safe handoff |
| `platform/gitops/appsets/infrastructure-apps.yaml` | Floating `main` | `ApplicationSet/infrastructure-apps` -> applicationset-controller -> platform child Applications -> application-controller -> charts/manifests | Generated Applications prune payloads; names collide with environment-root children, so dual activation creates competing specs | `OPTIONAL` + `UNKNOWN_EXTERNAL` | Do not activate beside an environment root; retain pending an explicit ownership migration |
| `platform/gitops/appsets/observability-apps.yaml` | Floating `main` | `ApplicationSet/observability-apps` -> applicationset-controller -> `loki`, `grafana`, `vector-gateway` Applications -> payloads | Generated Applications prune the same payload identities used by dev | `OPTIONAL` + `UNKNOWN_EXTERNAL` | Retain only as migration scaffold; activation requires ownership handoff |
| `platform/gitops/appsets/tenant-apps.yaml` | Floating `main`; Helm `v0.4.0` | two ApplicationSets -> applicationset-controller -> alternative FastAPI Applications -> Helm workloads | Generated Applications have resource finalizers and prune; distinct Application names can still own/delete the same workload objects | `SCAFFOLD` + `UNKNOWN_EXTERNAL` | Do not activate; operator must choose migration or removal after external-use confirmation |
| `platform/core/rbac/projects/*.yaml` | Repository file | `AppProject/platform` and `AppProject/tenants` -> Argo CD policy enforcement -> bounds dormant ApplicationSets | Removing a live project can invalidate dependent Applications without deleting their payload deterministically | `OPTIONAL` + `UNKNOWN_EXTERNAL` | Retain with the ApplicationSet migration surface; presence is not evidence of active RBAC |

GitHub default-branch search and direct inspection covered the seven
`app-poly-gitops` repositories plus archived `app-mono-gitops`. No additional
consumer of `root-app.yaml`, the ApplicationSets, or environment bootstrap
files was found. This cannot disprove an out-of-band `kubectl apply`, an Argo CD
object created from another account, or a fork, so their external status remains
`UNKNOWN_EXTERNAL`; none is `SAFE_TO_DELETE`.

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

| Path / object | Git owner -> API object -> watcher -> dependents | Classification | Prune/deletion consequence |
| --- | --- | --- | --- |
| `platform/core/namespaces/open-webui.yaml` | `clusters/dev` -> `Namespace/open-webui` -> root Application/namespace controller -> any namespaced objects, including objects created out of band | `VERIFIED_GIT_CONSUMER`; workload use `UNKNOWN_EXTERNAL` | Root prune of the Namespace can cascade-delete every namespaced object; not `SAFE_TO_DELETE` without a live inventory |
| `platform/infrastructure/ai-platform/open-webui/base` | `tst/stg/prd` scaffolds and dormant infrastructure ApplicationSet -> `Application/open-webui` -> application-controller -> Helm Deployment/Service/PVC | `SCAFFOLD` + `OPTIONAL` + `UNKNOWN_EXTERNAL` | Automated prune can delete workload and persistent data; do not activate beside another owner |
| Sealed Secrets, Reflector, External Secrets, and Longhorn bases | `tst/stg/prd` scaffolds and dormant infrastructure ApplicationSet -> child Applications -> application-controller -> operators/CRDs and dependents | `SCAFFOLD` + `OPTIONAL` + `UNKNOWN_EXTERNAL` | Pruning an operator before its custom resources are migrated can orphan or delete dependent state |
| CNPG and PGO operator bases | no dev/smoke or ApplicationSet reference -> child Application if manually applied -> application-controller -> operator CRDs/controllers | `OPTIONAL` + `UNKNOWN_EXTERNAL` | No static consumer is insufficient for deletion; live CR/controller inventory is required |
| `cnpg-cluster.yaml`, `postgres-cluster.yaml`, and dev SealedSecret files | no supported-root inclusion -> custom resources/SealedSecrets if manually applied -> respective operators/controllers -> databases/Secrets | `OPTIONAL` + `UNKNOWN_EXTERNAL` | Applying both database CRs creates competing database choices; deletion may remove data or credentials |
| Image Updater | `clusters/dev` -> `Application/argocd-image-updater` -> application-controller -> image-updater controller -> annotated FastAPI Application/Git write-back | `VERIFIED_GIT_CONSUMER`; live credentials and writes `UNKNOWN` | Removing the Application with prune removes the controller; it does not prove prior Git write-back state |
| Dify directory | documentation and empty Kustomization only; no API object or watcher | `SCAFFOLD` | The former comment-only manifest was already removed; no deployable Dify object exists |

Static inspection therefore identifies no additional `SAFE_TO_DELETE` object.
The exact missing evidence is an Argo inventory (Applications, ApplicationSets,
AppProjects, owners/finalizers and managed-resource lists), plus a Namespace/CR
inventory for `open-webui`, database CRs, SealedSecrets and optional operators.

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
