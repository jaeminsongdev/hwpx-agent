#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "tools" / "p10" / "schemas"


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)


def validate_document(document: Any, schema_name: str) -> None:
    schema = load_json(SCHEMA_ROOT / schema_name)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "$"
        raise ValueError(f"schema rejection at {location}: {first.message}")


def validate_policy(path: Path) -> dict[str, Any]:
    document = load_json(path)
    validate_document(document, "worker-isolation-policy-v1.schema.json")
    target = document["target"]
    if target["host_baseline_sha256"] == target["executable_sha256"]:
        raise ValueError("host baseline and executable digests must be distinct")
    return document


def validate_audit(path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    document = load_json(path)
    validate_document(document, "worker-isolation-audit-v1.schema.json")
    observation = document["live_observation"]
    if document["policy_sha256"] != observation["policy_manifest_sha256"]:
        raise ValueError("audit policy digest binding mismatch")
    if observation["host_baseline_sha256"] != policy["target"]["host_baseline_sha256"]:
        raise ValueError("audit host baseline binding mismatch")
    if (
        observation["host_isolation_identity_sha256"]
        != policy["target"]["host_isolation_identity_sha256"]
    ):
        raise ValueError("audit host isolation identity binding mismatch")
    if observation["target_profile_id"] != policy["target"]["profile_id"]:
        raise ValueError("audit target profile binding mismatch")
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--audit", type=Path)
    arguments = parser.parse_args()
    policy = validate_policy(arguments.policy)
    if arguments.audit is not None:
        validate_audit(arguments.audit, policy)
    print(
        json.dumps(
            {
                "schema_version": "hwpx-agent.p10-08-isolation-validation/v1",
                "state": "pass",
                "policy_valid": True,
                "audit_valid": arguments.audit is not None,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
