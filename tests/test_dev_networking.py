"""Check the public dev entrypoints produced by Kustomize, not source strings."""

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def render(path):
    result = subprocess.run(
        ["kubectl", "kustomize", str(ROOT / path)],
        check=True, capture_output=True, text=True,
    )
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc]


class DevNetworkingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = render("clusters/dev")
        cls.apps = {
            doc["metadata"]["name"]: doc
            for doc in cls.documents if doc["kind"] == "Application"
        }

    def values(self, name):
        self.assertTrue(name in self.apps, f"Missing dev Application: {name}")
        return yaml.safe_load(self.apps[name]["spec"]["source"]["helm"]["values"])

    def test_network_controllers_are_connected_to_dev(self):
        for name in ("ingress-nginx", "cert-manager", "external-dns"):
            with self.subTest(name=name):
                self.assertTrue(name in self.apps, f"Missing dev Application: {name}")
                spec = self.apps[name]["spec"]
                self.assertEqual(spec["destination"]["name"], "in-cluster")
                self.assertNotIn(spec["source"]["targetRevision"], ("main", "HEAD"))
        controller = self.values("ingress-nginx")["controller"]
        self.assertEqual(controller["service"]["type"], "LoadBalancer")
        self.assertEqual(controller["replicaCount"], 1)
        self.assertFalse(controller["allowSnippetAnnotations"])

    def test_only_three_requested_hosts_have_tls_and_dns(self):
        ingresses = [doc for doc in self.documents if doc["kind"] == "Ingress"]
        expected = {
            "argo.syncjob.ru": ("argocd", "argocd-server", 80),
            "grafana.syncjob.ru": ("observability", "grafana", 80),
            "chat-dev.syncjob.ru": ("chat-api", "chat-api", 80),
        }
        actual = {}
        for ingress in ingresses:
            spec = ingress["spec"]
            annotations = ingress["metadata"]["annotations"]
            self.assertEqual(spec["ingressClassName"], "nginx")
            self.assertEqual(annotations["cert-manager.io/cluster-issuer"], "letsencrypt-dns")
            self.assertEqual(annotations["external-dns.alpha.kubernetes.io/enabled"], "true")
            self.assertEqual(annotations["nginx.ingress.kubernetes.io/ssl-redirect"], "true")
            self.assertNotEqual(annotations.get("nginx.ingress.kubernetes.io/backend-protocol"), "HTTPS")
            for rule in spec["rules"]:
                host = rule["host"]
                self.assertNotIn(host, actual, "Duplicate host ownership")
                backend = rule["http"]["paths"][0]["backend"]["service"]
                actual[host] = (ingress["metadata"]["namespace"], backend["name"], backend["port"]["number"])
                self.assertTrue(any(host in entry["hosts"] and entry.get("secretName") for entry in spec["tls"]))
        self.assertEqual(actual, expected)
        # The root owns the public Ingress, so the app chart must not duplicate it.
        self.assertFalse(self.values("chat-api")["ingress"]["enabled"])

    def test_dns_is_scoped_and_preserves_unrelated_records(self):
        values = self.values("external-dns")
        self.assertEqual(values["provider"]["name"], "cloudflare")
        self.assertEqual(values["sources"], ["ingress"])
        self.assertEqual(values["domainFilters"], ["syncjob.ru"])
        self.assertIn("--annotation-filter=external-dns.alpha.kubernetes.io/enabled=true", values["extraArgs"])
        self.assertEqual(values["policy"], "upsert-only")
        self.assertEqual(values["registry"], "txt")
        self.assertEqual(values["txtOwnerId"], "app-poly-gitops-dev")
        token = next(env for env in values["env"] if env["name"] == "CF_API_TOKEN")
        self.assertNotIn("value", token)
        self.assertEqual(token["valueFrom"]["secretKeyRef"], {"name": "cloudflare-token", "key": "CF_API_TOKEN"})

    def test_issuer_is_installed_with_its_operator_not_in_root(self):
        self.assertFalse(any(doc["kind"] in {"Certificate", "ClusterIssuer", "SealedSecret"} for doc in self.documents))
        values = self.values("cert-manager")
        self.assertTrue(values["crds"]["enabled"])
        issuer, = [yaml.safe_load(obj) if isinstance(obj, str) else obj for obj in values["extraObjects"]]
        self.assertEqual(issuer["kind"], "ClusterIssuer")
        self.assertEqual(issuer["metadata"]["name"], "letsencrypt-dns")
        self.assertGreater(int(issuer["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"]), 0)
        solver, = issuer["spec"]["acme"]["solvers"]
        self.assertEqual(solver["selector"]["dnsZones"], ["syncjob.ru"])
        self.assertEqual(solver["dns01"]["cloudflare"]["apiTokenSecretRef"], {"name": "cloudflare-token", "key": "CF_API_TOKEN"})

    def test_public_services_do_not_use_open_default_credentials(self):
        grafana = self.values("grafana")
        self.assertNotIn("adminPassword", grafana)
        self.assertEqual(grafana["admin"]["existingSecret"], "grafana-admin")
        self.assertEqual(grafana["grafana.ini"]["server"]["root_url"], "https://grafana.syncjob.ru")
        self.assertFalse(grafana["grafana.ini"]["auth.anonymous"]["enabled"])
        ingress = next(doc for doc in self.documents if doc["kind"] == "Ingress" and doc["metadata"]["name"] == "chat-api")
        annotations = ingress["metadata"]["annotations"]
        self.assertEqual(annotations["nginx.ingress.kubernetes.io/auth-type"], "basic")
        self.assertEqual(annotations["nginx.ingress.kubernetes.io/auth-secret"], "chat-api-basic-auth")

    def test_smoke_still_has_no_public_networking(self):
        smoke = render("clusters/smoke")
        self.assertFalse(any(doc["kind"] == "Ingress" for doc in smoke))
        self.assertFalse(any(doc["kind"] == "Application" and doc["metadata"]["name"] in {"ingress-nginx", "cert-manager", "external-dns"} for doc in smoke))

    def test_pinned_controller_and_grafana_charts_render_correctly(self):
        rendered = {}
        for name in ("ingress-nginx", "cert-manager", "external-dns", "grafana"):
            with self.subTest(chart=name):
                self.assertTrue(name in self.apps, f"Missing dev Application: {name}")
                app = self.apps[name]["spec"]
                source = app["source"]
                with tempfile.TemporaryDirectory() as tmp:
                    values_path = Path(tmp) / "values.yaml"
                    values_path.write_text(source["helm"]["values"])
                    result = subprocess.run(
                        ["helm", "template", name, source["chart"], "--repo", source["repoURL"],
                         "--version", source["targetRevision"], "--namespace", app["destination"]["namespace"],
                         "--values", str(values_path)],
                        check=True, capture_output=True, text=True,
                    )
                rendered[name] = [doc for doc in yaml.safe_load_all(result.stdout) if doc]

        dns_deployment = next(doc for doc in rendered["external-dns"] if doc["kind"] == "Deployment")
        container, = dns_deployment["spec"]["template"]["spec"]["containers"]
        for flag in ("--source=ingress", "--provider=cloudflare", "--domain-filter=syncjob.ru",
                     "--policy=upsert-only", "--registry=txt", "--txt-owner-id=app-poly-gitops-dev",
                     "--annotation-filter=external-dns.alpha.kubernetes.io/enabled=true"):
            self.assertIn(flag, container["args"])
        token = next(env for env in container["env"] if env["name"] == "CF_API_TOKEN")
        self.assertEqual(token["valueFrom"]["secretKeyRef"]["name"], "cloudflare-token")
        issuer, = [doc for doc in rendered["cert-manager"] if doc["kind"] == "ClusterIssuer"]
        self.assertEqual(issuer["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"], "10")
        self.assertTrue(any(doc["kind"] == "CustomResourceDefinition" for doc in rendered["cert-manager"]))
        loadbalancer, = [doc for doc in rendered["ingress-nginx"] if doc["kind"] == "Service" and doc["spec"]["type"] == "LoadBalancer"]
        self.assertEqual({port["port"] for port in loadbalancer["spec"]["ports"]}, {80, 443})
        self.assertFalse(any(doc["kind"] == "Secret" and "admin-password" in doc.get("data", {}) for doc in rendered["grafana"]))

    def test_grafana_repeated_render_keeps_credentials_and_pod_template_stable(self):
        self.assertEqual(self.values("grafana").get("admin", {}).get("existingSecret"), "grafana-admin")
        source = self.apps["grafana"]["spec"]["source"]
        manifests = []
        for _ in range(2):
            result = subprocess.run(
                ["helm", "template", "grafana", "grafana", "--repo", source["repoURL"],
                 "--version", source["targetRevision"], "--namespace", "observability", "--values", "-"],
                input=source["helm"]["values"], check=True, capture_output=True, text=True,
            )
            manifests.append([doc for doc in yaml.safe_load_all(result.stdout) if doc])
        deployments = [next(doc for doc in docs if doc["kind"] == "Deployment") for docs in manifests]
        self.assertEqual(deployments[0]["spec"]["template"], deployments[1]["spec"]["template"])
        container, = deployments[0]["spec"]["template"]["spec"]["containers"]
        password = next(env for env in container["env"] if env["name"] == "GF_SECURITY_ADMIN_PASSWORD")
        self.assertEqual(password["valueFrom"]["secretKeyRef"], {"name": "grafana-admin", "key": "admin-password"})


if __name__ == "__main__":
    unittest.main()
