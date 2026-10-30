# Golden install

This guide describes a clean installation of the current `dev` or `smoke`
desired state. It does not assert that a cluster is running, and none of the
commands in this document are part of repository validation.

## Choose the profile

- Use `clusters/smoke` for a disposable FastAPI, CrewAI, and Jaeger acceptance
  run.
- Use `clusters/dev` for the complete application profile with public
  entrypoints, Loki, Grafana, and Vector.
- Do not use `tst`, `stg`, or `prd` as installation targets; their
  environment contracts are incomplete.

## Provision and bootstrap

[`app-poly-gitops-infra`](https://github.com/justgithubaccount/app-poly-gitops-infra)
owns Terraform and Argo CD bootstrap.

The recommended disposable path is its **Timeweb smoke and debug** workflow. It
creates one cost-bounded cluster, reconciles `clusters/smoke`, runs application
checks, and destroys the cluster by default. Selecting `keep_cluster=true`
retains encrypted Terraform state and kubeconfig for one day; cleanup then
requires the **Timeweb cleanup** workflow with the provisioning run ID.

The **Timeweb retained dev deploy** workflow can resize a retained smoke cluster
and switch its root to `clusters/dev`. It does not destroy the cluster. This is
an explicit deployment operation and needs the additional dev Secrets below.

For a manual local bootstrap, use the infra repository:

~~~bash
cp .env.example .env
task plan
task up
~~~

`task up` applies Terraform, installs Argo CD, and applies the root application.
Review the Terraform plan and account cost before running it. The default local
state is intended for a single disposable workflow; configure the documented S3
backend example for a persistent environment.

## Runtime secrets

Repository or Actions secrets do not automatically become Kubernetes Secrets.
Create fresh values for every new cluster and never reuse SealedSecrets encrypted
for a deleted controller.

The smoke workflow creates the FastAPI and CrewAI LLM Secrets from its
`OPENAI_API_KEY` repository secret. A manual install needs:

- `chat-api/chat-openrouter` with key `OPENROUTER_API_KEY`;
- `crewai-system/crewai-llm` with key `openai-api-key`.

The dev public entrypoints additionally require:

- `external-dns/cloudflare-token` with key `CF_API_TOKEN`;
- `cert-manager/cloudflare-token` with key `CF_API_TOKEN`;
- `chat-api/chat-api-basic-auth` with key `auth`;
- `observability/grafana-admin` with keys `admin-user` and
  `admin-password`.

[DEV-WEBS.md](DEV-WEBS.md) contains safe creation commands and Cloudflare scope
requirements.

## Reconcile the root

Argo CD must point to one versioned or reviewed repository revision:

~~~yaml
spec:
  source:
    repoURL: https://github.com/justgithubaccount/app-poly-gitops-k8s.git
    targetRevision: <reviewed-tag-or-commit>
    path: clusters/dev
~~~

The infrastructure smoke workflow uses `bootstrap/argocd/gitops-smoke-root.yaml`
and the smoke path. Do not treat `main` as an immutable release.

## Verify

After an explicitly authorized deployment:

~~~bash
kubectl -n argocd get applications
kubectl get pods --all-namespaces
kubectl -n chat-api get deployment,service
kubectl -n crewai-system get deployment,service
~~~

For dev networking:

~~~bash
kubectl -n ingress-nginx get service ingress-nginx-controller
kubectl -n external-dns logs deployment/external-dns --tail=50
kubectl get clusterissuer letsencrypt-dns
kubectl get ingress,certificate --all-namespaces
~~~

A rendered manifest is not evidence that DNS, TLS, provider access, or telemetry
is live. Verify the public endpoints and trace/log correlation separately.

## Operational notes

- Argo CD runs in insecure HTTP mode behind the Ingress. Its backend service port
  is 80; do not set the NGINX backend protocol to HTTPS.
- Cloudflare should use **Full (strict)** after origin certificates are Ready.
  Do not weaken TLS validation to bypass a 526 response.
- External DNS is `upsert-only` and owns only annotated `syncjob.ru` records
  with its configured TXT owner ID.
- The pinned ingress-nginx controller is retired upstream. It is retained for the
  lab profile; migrate before treating this as a long-lived public platform.

## Cleanup

Use the same state that created the cluster:

~~~bash
task destroy
~~~

For a retained Actions run, use the **Timeweb cleanup** workflow and its exact
provisioning run ID. Confirm an empty Terraform state after destroy. Deleting Git
branches or Argo CD applications is not a substitute for cloud cleanup.
