#!/usr/bin/env python3
"""Fail closed when manifest validators become moving, unverified downloads."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yaml"


class ValidationToolPinTests(unittest.TestCase):
    def test_opa_and_kubeconform_are_versioned_and_checksum_verified(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("OPA_VERSION: '1.22.0'", workflow)
        self.assertIn("KUBECONFORM_VERSION: '0.8.0'", workflow)
        self.assertNotIn("downloads/latest", workflow)
        self.assertNotIn("releases/latest", workflow)
        self.assertEqual(workflow.count("sha256sum --check opa_linux_amd64.sha256"), 2)
        self.assertIn(
            "grep ' kubeconform-linux-amd64.tar.gz$' CHECKSUMS | sha256sum --check -",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
