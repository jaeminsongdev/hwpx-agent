from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-handler-contract-v1.json"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "implementation/p15/P15-03_HANDLER_POLICY.md",
    "implementation/p15/p15-auth-tenant-v1.json",
    "implementation/p15/p15-public-tool-schema-contract-v1.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "tools/p15/build_handler_contract.py",
    "tools/p15/validate_auth_tenant.py",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/tests/test_handler_contract.py",
    "deny.toml",
    "security/dependency-policy.json",
]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_contract(root: Path = ROOT) -> dict[str, Any]:
    return {
        "catalog_sha256": sha256_file(root / CATALOG_PATH.relative_to(ROOT)),
        "error_envelope_version": "hwpx-agent.tool-error/v1",
        "handler_sequence": [
            "transport_admission",
            "authenticate_public_user",
            "parse_unique_json",
            "validate_input_schema",
            "authorize_tenant_project_subject",
            "dispatch_exactly_once",
            "validate_output_schema",
            "validate_result_correlation",
            "return_bounded_mcp_result",
        ],
        "jsonschema_crate": {
            "default_features": False,
            "version": "0.53.0",
        },
        "limits": {
            "argument_json_bytes": 262_144,
            "policy_memberships": 16_384,
            "policy_projects": 4_096,
            "public_tools": 18,
        },
        "rust_contract_tests": 16,
        "schema_version": "hwpx-agent.p15-handler-contract/v1",
        "scope": "current_pc_hancom_2020_in_process_reference_handlers",
        "source_locks": [
            {"path": relative, "sha256": sha256_file(root / relative)}
            for relative in SOURCE_PATHS
        ],
        "target_profile": "hancom-hangul-2020-secondary",
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
    errors = [] if actual == expected else ["handler contract drift"]
    print(
        json.dumps(
            {"errors": errors, "sources": len(SOURCE_PATHS), "state": "pass" if not errors else "fail"},
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
