#!/usr/bin/env python3
"""Rendered ownership contracts for the CI-supported GitOps roots."""

from __future__ import annotations

import subprocess
import unittest
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def render(path: str) -> list[dict]:
    result = subprocess.run(
        ["kubectl", "kustomize", str(ROOT / path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [document for document in yaml.safe_load_all(result.stdout) if document]


def identity(resource: dict) -> tuple[str, str, str, str]:
    metadata = resource["metadata"]
    return (
        resource["apiVersion"],
        resource["kind"],
        metadata.get("namespace", "<cluster>"),
        metadata["name"],
    )


class GitOpsOwnershipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.roots = {
            environment: render(f"clusters/{environment}")
            for environment in ("dev", "smoke")
        }

    def test_supported_roots_have_one_git_owner_per_api_object(self) -> None:
        for environment, resources in self.roots.items():
            with self.subTest(environment=environment):
                identities = [identity(resource) for resource in resources]
                duplicates = [
                    item for item, count in Counter(identities).items() if count > 1
                ]
                self.assertEqual(duplicates, [])

    def test_supported_roots_do_not_activate_alternative_controllers(self) -> None:
        for environment, resources in self.roots.items():
            with self.subTest(environment=environment):
                kinds = {resource["kind"] for resource in resources}
                self.assertNotIn("ApplicationSet", kinds)
                self.assertNotIn("AppProject", kinds)

    def test_supported_root_inventory_is_explicit(self) -> None:
        dev_apps = {
            resource["metadata"]["name"]
            for resource in self.roots["dev"]
            if resource["kind"] == "Application"
        }
        smoke_apps = {
            resource["metadata"]["name"]
            for resource in self.roots["smoke"]
            if resource["kind"] == "Application"
        }

        self.assertEqual(
            dev_apps,
            {
                "argocd-image-updater",
                "cert-manager",
                "chat-api",
                "crewai",
                "external-dns",
                "grafana",
                "ingress-nginx",
                "loki",
                "vector-gateway",
            },
        )
        self.assertEqual(smoke_apps, {"chat-api", "crewai"})

    def test_application_manifests_are_not_comment_only_placeholders(self) -> None:
        application_files = sorted(ROOT.glob("platform/**/base/application.yaml"))
        application_files.extend(sorted(ROOT.glob("tenants/**/base/application.yaml")))

        empty = []
        for path in application_files:
            documents = [
                document
                for document in yaml.safe_load_all(path.read_text(encoding="utf-8"))
                if document is not None
            ]
            if not documents:
                empty.append(str(path.relative_to(ROOT)))

        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()
