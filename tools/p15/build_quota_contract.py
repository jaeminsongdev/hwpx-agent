from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-quota-contract-v1.json"
POLICY_PATH = ROOT / "protocol/mcp/p15-quota-policy-v1.json"
ERROR_V1_PATH = ROOT / "protocol/mcp/p15-public-error-catalog-v1.json"
ERROR_V2_PATH = ROOT / "protocol/mcp/p15-public-error-catalog-v2.json"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/02_architecture/01_system_architecture.md",
    "docs/02_architecture/04_deployment_topology.md",
    "docs/06_mcp_api/04_error_model.md",
    "specs/error-envelope.schema.json",
    "specs/work-breakdown-structure.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "protocol/mcp/p15-public-error-catalog-v1.json",
    "protocol/mcp/p15-public-error-catalog-v2.json",
    "protocol/mcp/p15-quota-policy-v1.json",
    "implementation/p15/p15-error-mapping-contract-v1.json",
    "implementation/p15/P15-07_QUOTA_POLICY.md",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/error_catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/quota.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/src/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "crates/mcp-control-plane/tests/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/error_mapping.rs",
    "crates/mcp-control-plane/tests/quota_service.rs",
    "tools/p15/build_error_mapping_contract.py",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/build_quota_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/tests/test_error_mapping_contract.py",
    "tools/p15/tests/test_quota_contract.py",
]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def sha256_file(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def build_contract(root: Path = ROOT) -> dict[str, Any]:
    policy = load_json(root / POLICY_PATH.relative_to(ROOT))
    error_v2 = load_json(root / ERROR_V2_PATH.relative_to(ROOT))
    return {
        "buckets": policy["buckets"],
        "error_catalog_additions": ["QUOTA_EXCEEDED", "QUOTA_UNAVAILABLE"],
        "error_catalog_v1_sha256": sha256_file(root / ERROR_V1_PATH.relative_to(ROOT)),
        "error_catalog_v2_sha256": sha256_file(root / ERROR_V2_PATH.relative_to(ROOT)),
        "handler_sequence_preserved": True,
        "job_classes": policy["job_classes"],
        "limits": {
            "bucket_entries": policy["state_limits"]["bucket_entries"],
            "replay_entries": policy["state_limits"]["replay_entries"],
            "replay_ttl_seconds": policy["replay_ttl_seconds"],
            "window_seconds": policy["window_seconds"],
        },
        "meta_keys": ["hwpx/quotaPolicySha256", "hwpx/retryAfterSeconds"],
        "p15_06_audited_source_commit": (
            "f36a07e988558b4481c50955a0f76bd69c516d9d"
        ),
        "p15_06_contract_sha256": sha256_file(
            root / "implementation/p15/p15-error-mapping-contract-v1.json"
        ),
        "public_envelope_version": "hwpx-agent.error/v2",
        "quota_policy_sha256": sha256_file(root / POLICY_PATH.relative_to(ROOT)),
        "required_behaviors": [
            "authentication_schema_and_policy_before_quota",
            "quota_before_exactly_one_dispatch",
            "atomic_all_dimension_charge_or_no_charge",
            "tenant_user_capability_and_job_class_isolation",
            "integer_token_bucket_with_bounded_retry_guidance",
            "async_idempotency_replay_without_recharge",
            "idempotency_payload_conflict_fails_closed",
            "bounded_state_and_clock_regression_fail_closed",
            "additive_public_error_catalog_supersession",
            "no_quota_identity_counter_or_fingerprint_leakage",
        ],
        "rust_quota_tests": 8,
        "rust_regression_tests": 45,
        "runtime_error_codes": [
            entry["error_code"] for entry in error_v2["errors"]
        ],
        "schema_version": "hwpx-agent.p15-quota-contract/v1",
        "scope": "current_pc_hancom_2020_local_quota_reference",
        "source_locks": [
            {"path": relative, "sha256": sha256_file(root / relative)}
            for relative in SOURCE_PATHS
        ],
        "stages": [
            "admission",
            "authenticate",
            "parse",
            "input_validation",
            "policy",
            "quota",
            "dispatch",
            "output_validation",
        ],
        "target_profile": "hancom-hangul-2020-secondary",
        "tool_catalog_sha256": sha256_file(
            root / "protocol/mcp/p15-public-tools-v1.json"
        ),
    }


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    expected = canonical_bytes(build_contract())
    if arguments.write:
        write_atomic(CONTRACT_PATH, expected)
        print(json.dumps({"state": "written", "sources": len(SOURCE_PATHS)}))
        return 0
    actual = CONTRACT_PATH.read_bytes() if CONTRACT_PATH.is_file() else b""
    errors = [] if actual == expected else ["quota contract drift"]
    print(
        json.dumps(
            {
                "errors": errors,
                "sources": len(SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
