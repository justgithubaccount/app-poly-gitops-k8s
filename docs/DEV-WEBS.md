# Public dev web entrypoints

`clusters/dev` enables these existing services, and no OpenWebUI or CrewAI ingress:

| Address | Service | Login |
| --- | --- | --- |
| `https://argo.syncjob.ru` | Argo CD | Argo CD account |
| `https://grafana.syncjob.ru` | Grafana | Stable `grafana-admin` Secret |
| `https://chat-dev.syncjob.ru/docs` | FastAPI API documentation | HTTP basic auth |

This is not the separate `app-poly-gitops-ui` frontend. That frontend is not
deployed by this configuration. FastAPI has no application-level user isolation;
the dev basic-auth boundary prevents exposing its paid LLM endpoint anonymously.

## What reconciles automatically

`ingress-nginx` creates one LoadBalancer service. Its external IP becomes the
target of the three Ingresses. `external-dns` watches only explicitly opted-in
Ingresses in `syncjob.ru` and upserts Cloudflare records with TXT ownership
`app-poly-gitops-dev`. It does not delete unrelated records, such as
`self.syncjob.ru`, or reconcile them from this repository.

`cert-manager` installs its CRDs and webhook before the `letsencrypt-dns`
ClusterIssuer (child-application sync wave 10). Ingress-shim issues separate
certificates in `argocd`, `observability` and `chat-api`; no wildcard secret
replication or reflector is required. Ingress traffic to Argo CD is HTTP on
service port 80, matching bootstrap `server.insecure=true`.

The pinned legacy ingress-nginx controller is retired upstream. This restores the
existing dev stack only; migrate to a maintained controller before treating it as
a permanent public deployment. See the [upstream retirement announcement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/).

## Required fresh secrets

DNS/TLS is automatic only after a running cluster has its credentials. Old
SealedSecrets from the deleted cluster are deliberately excluded. Neither a GitHub
Actions secret nor a local environment variable is automatically a Kubernetes
Secret. This change does not provision a cluster or write Cloudflare records.

Create `cloudflare-token` with key `CF_API_TOKEN` in **both** `external-dns` and
`cert-manager`. Scope the Cloudflare API token to zone `syncjob.ru`, permissions
**Zone:DNS:Edit** and **Zone:Zone:Read**. Run with the intended kubeconfig selected:

```bash
read -rsp 'Cloudflare API token: ' CLOUDFLARE_TOKEN
printf '\n'
for namespace in external-dns cert-manager; do
  kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
  printf 'CF_API_TOKEN=%s\n' "$CLOUDFLARE_TOKEN" |
    kubectl -n "$namespace" create secret generic cloudflare-token \
      --from-env-file=/dev/stdin --dry-run=client -o yaml | kubectl apply -f -
done
unset CLOUDFLARE_TOKEN
```

Create the FastAPI ingress password using `htpasswd` (it prompts for the password):

```bash
kubectl create namespace chat-api --dry-run=client -o yaml | kubectl apply -f -
htpasswd -nB operator |
  kubectl -n chat-api create secret generic chat-api-basic-auth \
    --from-file=auth=/dev/stdin --dry-run=client -o yaml | kubectl apply -f -
```

Without that secret, external FastAPI access fails closed. In-cluster calls and
port-forward-based smoke checks do not pass through this ingress auth boundary.
If ingress-nginx does not pick up a newly created auth secret immediately, inspect
the controller events and verify the Secret's `auth` key contains a valid htpasswd
entry. Do not disable authentication to make a smoke test pass.

Create the Grafana credential Secret **once**, before deploying Grafana. The
password is generated locally, piped directly into the Secret and never stored in
git. This command intentionally fails rather than replacing an existing Secret:

```bash
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -
openssl rand -base64 36 | tr -d '\n' |
  kubectl -n observability create secret generic grafana-admin \
    --from-literal=admin-user=admin --from-file=admin-password=/dev/stdin
```

Helm references this existing Secret, avoiding random password generation and
Deployment checksum changes on every Argo CD refresh. Retrieve the password
privately when needed:

```bash
kubectl -n observability get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d
```

For an existing Grafana instance, rotate any old default credentials explicitly;
changing Helm values is not proof that the stored Grafana password changed.
Keep Cloudflare SSL/TLS mode **Full (strict)** once origin certificates are Ready.
An origin certificate that is not ready may cause Cloudflare 526; never work around
it by weakening TLS verification.

## Verify after an explicitly authorized deploy

```bash
kubectl -n ingress-nginx get service ingress-nginx-controller
kubectl -n external-dns logs deployment/external-dns --tail=50
kubectl get clusterissuer letsencrypt-dns
kubectl get ingress,certificate -A
curl -I https://argo.syncjob.ru
curl -I https://grafana.syncjob.ru
curl -u operator https://chat-dev.syncjob.ru/health
```

Check that a deleted managed DNS record is recreated and `self.syncjob.ru` remains
unchanged. Do not infer working DNS/TLS from a successful manifest render. A public
LoadBalancer/IP may add provider charges; provisioning needs its own cost review.
No merge, release or deploy is part of preparing this configuration.

## Local validation

Requires `kubectl`, Helm 3, Python 3 and PyYAML. CI installs PyYAML in an isolated
virtual environment.

```bash
python3 tests/test_dev_networking.py
bash tests/test_dev_contract.sh
```

The networking tests render the dev and smoke roots and the four pinned Helm
charts, verifying routing, DNS flags, secret references, stable Grafana auth,
CRD/issuer ordering and continued smoke isolation without touching a cluster.
