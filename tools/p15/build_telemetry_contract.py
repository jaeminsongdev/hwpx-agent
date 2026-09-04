from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-telemetry-contract-v1.json"
POLICY_PATH = ROOT / "protocol/mcp/p15-telemetry-policy-v1.json"
P15_07_CONTRACT_PATH = ROOT / "implementation/p15/p15-quota-contract-v1.json"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/02_architecture/08_observability.md",
    "docs/09_roadmap/P15_remote_mcp_control_plane.md",
    "docs/10_operations/05_observability_incidents.md",
    "specs/work-breakdown-structure.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "protocol/mcp/p15-public-error-catalog-v2.json",
    "protocol/mcp/p15-quota-policy-v1.json",
    "protocol/mcp/p15-telemetry-policy-v1.json",
    "implementation/p15/p15-quota-contract-v1.json",
    "implementation/p15/P15-08_TELEMETRY.md",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/error_catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/quota.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/telemetry.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/src/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "crates/mcp-control-plane/tests/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/error_mapping.rs",
    "crates/mcp-control-plane/tests/quota_service.rs",
    "crates/mcp-control-plane/tests/telemetry.rs",
    "tools/p15/build_quota_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/build_telemetry_contract.py",
    "tools/p15/validate_telemetry_contract.py",
    "tools/p15/tests/test_quota_contract.py",
    "tools/p15/tests/test_telemetry_contract.py",
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
    return {
        "correlation_fields": policy["correlation_fields"],
        "dashboard_dimensions": policy["dashboard_dimensions"],
        "dashboard_schema_version": "hwpx-agent.telemetry-dashboard/v1",
        "handler_sequence_preserved": True,
        "identifier_protection": "process_salted_sha256",
        "limits": {
            "capability_routes_per_trace": policy[
                "max_capability_routes_per_trace"
            ],
            "traces": policy["trace_capacity"],
        },
        "p15_07_audited_source_commit": (
            "e15921a59d45056c46b8ae94b6f6af778746c534"
        ),
        "p15_07_contract_sha256": sha256_file(
            root / P15_07_CONTRACT_PATH.relative_to(ROOT)
        ),
        "public_meta_keys": ["hwpx/telemetryPolicySha256"],
        "public_trace_id_exposed": False,
        "required_behaviors": [
            "one_complete_trace_per_public_result",
            "fixed_six_stage_hierarchy_with_explicit_not_applicable",
            "whole_trace_fifo_eviction_at_bounded_capacity",
            "tool_latency_and_status_by_closed_tenant_class",
            "job_backend_capability_and_validation_sli",
            "process_salted_identifier_and_capability_digests",
            "no_body_credential_path_identity_or_backend_error_retention",
            "telemetry_does_not_reorder_or_duplicate_gateway_dispatch",
            "invalid_gateway_output_is_not_copied_into_telemetry",
            "deterministic_dashboard_from_retained_complete_traces",
        ],
        "rust_regression_tests": 53,
        "rust_telemetry_tests": 8,
        "schema_version": "hwpx-agent.p15-telemetry-contract/v1",
        "scope": "current_pc_hancom_2020_local_telemetry_reference",
        "source_locks": [
            {"path": relative, "sha256": sha256_file(root / relative)}
            for relative in SOURCE_PATHS
        ],
        "target_profile": "hancom-hangul-2020-secondary",
        "tenant_classes": policy["tenant_classes"],
        "telemetry_policy_sha256": sha256_file(
            root / POLICY_PATH.relative_to(ROOT)
        ),
        "tool_catalog_sha256": sha256_file(
            root / "protocol/mcp/p15-public-tools-v1.json"
        ),
        "trace_schema_version": "hwpx-agent.telemetry-trace/v1",
        "trace_stages": policy["trace_stages"],
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
    errors = [] if actual == expected else ["telemetry contract drift"]
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
