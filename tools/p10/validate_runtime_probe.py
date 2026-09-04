#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def validate_document(document: Any, schema_name: str) -> None:
    schema = load_json(SCHEMA_ROOT / schema_name)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(document), key=lambda error: list(error.absolute_path)
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "$"
        raise ValueError(f"schema rejection at {location}: {first.message}")


def _resolve_repository_file(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError("pinned path escaped the repository root") from error
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError(f"pinned file is missing or not plain: {relative_path}")
    return candidate


def _require_file_digest(relative_path: str, expected: str) -> None:
    observed = hashlib.sha256(_resolve_repository_file(relative_path).read_bytes()).hexdigest()
    if observed != expected:
        raise ValueError(f"pinned file digest mismatch: {relative_path}")


def validate_policy(path: Path, verify_files: bool = True) -> dict[str, Any]:
    document = load_json(path)
    validate_document(document, "runtime-probe-policy-v1.schema.json")
    capability_ids = [item["capability_id"] for item in document["pinned_evidence"]]
    if len(capability_ids) != len(set(capability_ids)):
        raise ValueError("pinned evidence capability IDs are not unique")

    security = document["security_module"]
    if security["state"] == "not_configured":
        if security["registration_name"] is not None or security["sha256"] is not None:
            raise ValueError("not-configured security module cannot carry a pin")
    elif not security["registration_name"] or not security["sha256"]:
        raise ValueError("pinned security module requires name and digest")

    if verify_files:
        registry = document["capability_registry"]
        _require_file_digest(registry["relative_path"], registry["sha256"])
        isolation_pin = document["isolation_policy"]
        _require_file_digest(isolation_pin["relative_path"], isolation_pin["sha256"])
        for evidence in document["pinned_evidence"]:
            _require_file_digest(evidence["relative_path"], evidence["sha256"])

        isolation = load_json(_resolve_repository_file(isolation_pin["relative_path"]))
        target = document["target"]
        isolation_target = isolation["target"]
        for key in (
            "profile_id",
            "product_build",
            "locale",
            "process_architecture",
            "executable_sha256",
            "host_baseline_sha256",
        ):
            if target[key] != isolation_target[key]:
                raise ValueError(f"runtime/isolation target binding mismatch: {key}")
        if registry["sha256"] != isolation_target["capability_registry_sha256"]:
            raise ValueError("runtime/isolation capability registry binding mismatch")
    return document


def validate_audit(
    path: Path, policy: dict[str, Any], expected_policy_sha256: str
) -> dict[str, Any]:
    document = load_json(path)
    validate_document(document, "runtime-probe-audit-v1.schema.json")
    if document["policy_sha256"] != expected_policy_sha256:
        raise ValueError("audit policy digest binding mismatch")
    observation = document["observation"]
    target = policy["target"]
    if observation["policy_sha256"] != expected_policy_sha256:
        raise ValueError("observation policy digest binding mismatch")
    if observation["isolation_policy_sha256"] != policy["isolation_policy"]["sha256"]:
        raise ValueError("observation isolation policy digest binding mismatch")
    for observation_key, policy_key in (
        ("target_profile_id", "profile_id"),
        ("product_build", "product_build"),
        ("process_architecture", "process_architecture"),
    ):
        if observation[observation_key] != target[policy_key]:
            raise ValueError(f"audit target binding mismatch: {observation_key}")
    if (
        observation["capability_registry_sha256"]
        != policy["capability_registry"]["sha256"]
    ):
        raise ValueError("audit capability registry binding mismatch")
    if (
        document["host_baseline_verification"]["baseline_digest_sha256"]
        != target["host_baseline_sha256"]
    ):
        raise ValueError("audit host baseline binding mismatch")
    if policy["security_module"]["state"] == "not_configured" and (
        observation["probe_health"] != "unroutable"
        or observation["security_module_state"] != "not_registered"
        or observation["acquire_lease_calls"] != 0
    ):
        raise ValueError("missing security module was promoted to a routable lease")
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--audit", type=Path)
    arguments = parser.parse_args()
    policy = validate_policy(arguments.policy)
    if arguments.audit is not None:
        validate_audit(
            arguments.audit,
            policy,
            hashlib.sha256(arguments.policy.read_bytes()).hexdigest(),
        )
    print(
        json.dumps(
            {
                "schema_version": "hwpx-agent.p10-10-runtime-probe-validation/v1",
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
