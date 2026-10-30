#!/usr/bin/env python3
"""Evaluate OPA policies against every resource in a YAML document stream."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def evaluate_resource(resource: dict[str, Any], policies: Path) -> list[str]:
    opa = os.environ.get("OPA_BIN", "opa")
    result = subprocess.run(
        [
            opa,
            "eval",
            "--format=json",
            "--data",
            str(policies),
            "--stdin-input",
            "data.kubernetes.deny",
        ],
        input=json.dumps(resource),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "OPA evaluation failed")

    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("OPA returned an invalid result")

    results = payload.get("result")
    if not isinstance(results, list) or len(results) != 1:
        raise RuntimeError("OPA returned a missing or invalid result")

    result_entry = results[0]
    if not isinstance(result_entry, dict):
        raise RuntimeError("OPA returned a missing or invalid result")

    expressions = result_entry.get("expressions")
    if not isinstance(expressions, list) or len(expressions) != 1:
        raise RuntimeError("OPA returned a missing or invalid expression")

    expression = expressions[0]
    if not isinstance(expression, dict):
        raise RuntimeError("OPA returned a missing or invalid expression")

    messages = expression.get("value")
    if not isinstance(messages, list) or not all(isinstance(message, str) for message in messages):
        raise RuntimeError("OPA returned an invalid policy result")
    return sorted(messages)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("policies", type=Path)
    args = parser.parse_args()

    try:
        with args.manifest.open(encoding="utf-8") as manifest_file:
            documents = list(yaml.safe_load_all(manifest_file))
    except (OSError, yaml.YAMLError) as error:
        print(f"Unable to read manifest: {error}", file=sys.stderr)
        return 2

    resources = [
        (index, document)
        for index, document in enumerate(documents, 1)
        if document is not None
    ]
    if not resources:
        print("manifest contains no Kubernetes resources", file=sys.stderr)
        return 2

    violations: list[str] = []

    for document_number, resource in resources:
        metadata = resource.get("metadata") if isinstance(resource, dict) else None
        if (
            not isinstance(resource, dict)
            or not resource
            or not isinstance(resource.get("apiVersion"), str)
            or not resource["apiVersion"]
            or not isinstance(resource.get("kind"), str)
            or not resource["kind"]
            or not isinstance(metadata, dict)
            or not isinstance(metadata.get("name"), str)
            or not metadata["name"]
        ):
            print(
                f"document {document_number} is not a valid Kubernetes resource object",
                file=sys.stderr,
            )
            return 2
        try:
            messages = evaluate_resource(resource, args.policies)
        except (FileNotFoundError, json.JSONDecodeError, RuntimeError) as error:
            print(f"OPA failed for document {document_number}: {error}", file=sys.stderr)
            return 2
        violations.extend(f"document {document_number}: {message}" for message in messages)

    if violations:
        print("OPA policy violations found:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print(f"{len(resources)} Kubernetes resources passed OPA validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
