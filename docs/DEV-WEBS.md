# Development web entrypoints

`clusters/dev` declares the following public entrypoints. They exist only after
the profile is deployed and DNS/TLS reconciliation succeeds; this repository
does not claim that they are currently live.

| Address | Service | Access boundary |
| --- | --- | --- |
| `https://argo.syncjob.ru` | Argo CD | Argo CD account |
| `https://grafana.syncjob.ru` | Grafana | `grafana-admin` Secret |
| `https://chat-dev.syncjob.ru/docs` | FastAPI documentation | HTTP basic auth |

The standalone
[`app-poly-gitops-ui`](https://github.com/justgithubaccount/app-poly-gitops-ui)
is not deployed by this profile. FastAPI has no application-level user
isolation, so the basic-auth Ingress must not be removed from a public dev
deployment.

## Reconciliation model

ingress-nginx creates one LoadBalancer Service. external-dns watches only
Ingresses explicitly opted in by annotation, filters to `syncjob.ru`, and uses
upsert-only policy with TXT owner `app-poly-gitops-dev`. It does not manage
unrelated records such as `self.syncjob.ru`.

cert-manager installs its CRDs and webhook before the `letsencrypt-dns`
ClusterIssuer. Ingress-shim then issues separate certificates in `argocd`,
`observability`, and `chat-api`. Argo CD runs in insecure HTTP mode behind
the Ingress, so its backend service port is 80.

The pinned ingress-nginx controller is retired upstream. It is retained to
reproduce the current lab profile, not as a recommendation for a new permanent
deployment. See the
[upstream announcement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/).

## Required Secrets

Create fresh Secrets for a new cluster. A GitHub Actions secret or local
environment variable is not automatically available to Kubernetes, and a
SealedSecret from a deleted controller cannot be decrypted by a new controller.

### Cloudflare DNS

Create `cloudflare-token` with key `CF_API_TOKEN` in both namespaces. Scope
the token to zone `syncjob.ru` with **Zone:DNS:Edit** and
**Zone:Zone:Read**.

~~~bash
read -rsp 'Cloudflare API token: ' CLOUDFLARE_TOKEN
printf '\n'
for namespace in external-dns cert-manager; do
  kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
  printf 'CF_API_TOKEN=%s\n' "$CLOUDFLARE_TOKEN" |
    kubectl -n "$namespace" create secret generic cloudflare-token \
      --from-env-file=/dev/stdin --dry-run=client -o yaml | kubectl apply -f -
done
unset CLOUDFLARE_TOKEN
~~~

### FastAPI basic authentication

`htpasswd` prompts for the password and writes only the hash into the Secret:

~~~bash
kubectl create namespace chat-api --dry-run=client -o yaml | kubectl apply -f -
htpasswd -nB operator |
  kubectl -n chat-api create secret generic chat-api-basic-auth \
    --from-file=auth=/dev/stdin --dry-run=client -o yaml | kubectl apply -f -
~~~

Without this Secret, external FastAPI access fails closed. In-cluster and
port-forward checks do not pass through this boundary.

### Grafana administrator

Create the credential once, before Grafana starts. This command intentionally
fails instead of replacing an existing Secret:

~~~bash
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -
openssl rand -base64 36 | tr -d '\n' |
  kubectl -n observability create secret generic grafana-admin \
    --from-literal=admin-user=admin --from-file=admin-password=/dev/stdin
~~~

Retrieve the generated password privately when needed:

~~~bash
kubectl -n observability get secret grafana-admin \
  -o jsonpath='{.data.admin-password}' | base64 -d
~~~

Changing Helm values is not proof that an existing Grafana password rotated.

## Verification

After an explicitly authorized deployment:

~~~bash
kubectl -n ingress-nginx get service ingress-nginx-controller
kubectl -n external-dns logs deployment/external-dns --tail=50
kubectl get clusterissuer letsencrypt-dns
kubectl get ingress,certificate --all-namespaces
curl -I https://argo.syncjob.ru
curl -I https://grafana.syncjob.ru
curl -u operator https://chat-dev.syncjob.ru/health
~~~

Keep Cloudflare SSL/TLS mode at **Full (strict)** after origin certificates are
Ready. Investigate a 526 response instead of weakening verification. Confirm
that deleted records owned by this profile are recreated and unrelated records
remain unchanged.

## Offline validation

~~~bash
python3 -m venv /tmp/app-poly-networking-tests
/tmp/app-poly-networking-tests/bin/python -m pip install 'PyYAML==6.0.2'
/tmp/app-poly-networking-tests/bin/python tests/test_dev_networking.py
bash tests/test_dev_contract.sh
~~~

These checks render desired state only. They do not create a LoadBalancer, write
Cloudflare records, issue certificates, or prove a live endpoint.
