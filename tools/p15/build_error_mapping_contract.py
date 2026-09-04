from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-error-mapping-contract-v1.json"
ERROR_CATALOG_PATH = ROOT / "protocol/mcp/p15-public-error-catalog-v1.json"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/06_mcp_api/04_error_model.md",
    "docs/09_roadmap/P15_remote_mcp_control_plane.md",
    "specs/error-envelope.schema.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "protocol/mcp/p15-public-error-catalog-v1.json",
    "implementation/p15/p15-handler-contract-v1.json",
    "implementation/p15/p15-async-job-contract-v1.json",
    "implementation/p15/p15-artifact-delivery-contract-v1.json",
    "implementation/p15/P15-06_ERROR_MAPPING_POLICY.md",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/error_catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/src/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "crates/mcp-control-plane/tests/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/error_mapping.rs",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/build_artifact_delivery_contract.py",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/build_error_mapping_contract.py",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/tests/test_artifact_delivery_contract.py",
    "tools/p15/tests/test_error_mapping_contract.py",
]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_catalog(root: Path) -> dict[str, Any]:
    value = json.loads((root / ERROR_CATALOG_PATH.relative_to(ROOT)).read_text("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("error catalog root must be an object")
    return value


def build_contract(root: Path = ROOT) -> dict[str, Any]:
    catalog = load_catalog(root)
    errors = catalog["errors"]
    return {
        "error_catalog_sha256": sha256_file(
            root / ERROR_CATALOG_PATH.relative_to(ROOT)
        ),
        "error_codes": [entry["error_code"] for entry in errors],
        "error_envelope_schema_sha256": sha256_file(
            root / "specs/error-envelope.schema.json"
        ),
        "handler_sequence_preserved": True,
        "p15_05_implementation_commit": (
            "dde79ff3fa86953c7f3e6e8e2402479eddee813e"
        ),
        "public_envelope_version": "hwpx-agent.error/v2",
        "required_behaviors": [
            "digest_pinned_closed_error_catalog",
            "authentication_before_argument_parse",
            "server_correlation_before_validated_input",
            "validated_public_request_id_after_input_validation",
            "authentication_oracle_collapsed",
            "typed_auth_policy_gateway_job_artifact_mapping",
            "single_bounded_recovery_action",
            "empty_public_details",
            "no_secret_path_token_tenant_or_backend_leakage",
        ],
        "rust_error_mapping_tests": 5,
        "rust_handler_regression_tests": 16,
        "schema_version": "hwpx-agent.p15-error-mapping-contract/v1",
        "scope": "current_pc_hancom_2020_local_public_error_reference",
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
    errors = [] if actual == expected else ["error mapping contract drift"]
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
