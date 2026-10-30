#!/usr/bin/env python3
"""Regression tests for evaluating every document in a rendered manifest."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate_opa_manifests.py"
POLICIES = REPO_ROOT / "policies"


class OpaMultiDocumentValidationTests(unittest.TestCase):
    def run_validator(
        self, manifest: str, *, opa_output: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_file = Path(temp_dir) / "manifest.yaml"
            manifest_file.write_text(textwrap.dedent(manifest).lstrip(), encoding="utf-8")
            env = os.environ.copy()
            if opa_output is not None:
                opa_bin = Path(temp_dir) / "opa"
                opa_bin.write_text(
                    f"#!/usr/bin/env python3\nprint({opa_output!r})\n",
                    encoding="utf-8",
                )
                opa_bin.chmod(0o755)
                env["OPA_BIN"] = str(opa_bin)
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(manifest_file), str(POLICIES)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

    def test_accepts_valid_resources_in_every_document(self) -> None:
        result = self.run_validator(
            """
            apiVersion: v1
            kind: Namespace
            metadata:
              name: valid-first
            ---
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: valid-second
              namespace: default
              labels:
                app.kubernetes.io/name: valid-second
            spec:
              selector:
                matchLabels:
                  app: valid-second
              template:
                metadata:
                  labels:
                    app: valid-second
                spec:
                  containers:
                    - name: app
                      image: nginx:1.27
                      resources:
                        limits:
                          cpu: 100m
                          memory: 64Mi
            """
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 Kubernetes resources passed OPA validation", result.stdout)

    def test_rejects_violation_in_second_document(self) -> None:
        result = self.run_validator(
            """
            apiVersion: v1
            kind: Namespace
            metadata:
              name: valid-first
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: invalid-second
              namespace: default
            spec:
              selector:
                matchLabels:
                  app: invalid-second
              template:
                metadata:
                  labels:
                    app: invalid-second
                spec:
                  containers:
                    - name: app
                      image: nginx:1.27
                      resources:
                        limits:
                          cpu: 100m
                          memory: 64Mi
            """
        )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("document 2", result.stderr)
        self.assertIn(
            "[Deployment/invalid-second] Missing required label: app.kubernetes.io/name",
            result.stderr,
        )

    def test_rejects_empty_resource_stream(self) -> None:
        for manifest in ("", "---\n---\n"):
            with self.subTest(manifest=manifest):
                result = self.run_validator(manifest)

                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("no Kubernetes resources", result.stderr)

    def test_rejects_empty_or_invalid_kubernetes_objects(self) -> None:
        invalid_documents = (
            "{}\n",
            "[]\n",
            "apiVersion: v1\nmetadata:\n  name: missing-kind\n",
            "apiVersion: v1\nkind: ConfigMap\nmetadata: {}\n",
        )
        for manifest in invalid_documents:
            with self.subTest(manifest=manifest):
                result = self.run_validator(manifest)

                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("not a valid Kubernetes resource object", result.stderr)

    def test_rejects_missing_or_invalid_opa_result(self) -> None:
        valid_manifest = """
            apiVersion: v1
            kind: Namespace
            metadata:
              name: valid
        """
        for opa_output in ('{"result": []}', '{"result": [null]}', "not-json"):
            with self.subTest(opa_output=opa_output):
                result = self.run_validator(valid_manifest, opa_output=opa_output)

                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("OPA failed for document 1", result.stderr)


if __name__ == "__main__":
    unittest.main()
