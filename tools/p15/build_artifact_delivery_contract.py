from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-artifact-delivery-contract-v1.json"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/06_mcp_api/01_tool_surface.md",
    "docs/06_mcp_api/02_tool_contracts.md",
    "docs/06_mcp_api/06_jobs_artifacts.md",
    "docs/12_implementation_guides/09_project_jobs_storage.md",
    "protocol/mcp/p15-public-tools-v1.json",
    "implementation/p14/postgres/p14-artifact-service-v1.json",
    "implementation/p15/p15-auth-tenant-v1.json",
    "implementation/p15/p15-public-tool-schema-contract-v1.json",
    "implementation/p15/p15-handler-contract-v1.json",
    "implementation/p15/p15-async-job-contract-v1.json",
    "implementation/p15/P15-05_ARTIFACT_DELIVERY_POLICY.md",
    "crates/artifact-service/Cargo.toml",
    "crates/artifact-service/src/lib.rs",
    "crates/artifact-service/src/crypto.rs",
    "crates/artifact-service/src/service.rs",
    "crates/artifact-service/src/signed_url.rs",
    "crates/artifact-service/src/store.rs",
    "crates/artifact-service/src/types.rs",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/src/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "crates/mcp-control-plane/tests/artifact_delivery.rs",
    "tools/p15/build_async_job_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/build_artifact_delivery_contract.py",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/tests/test_async_job_contract.py",
    "tools/p15/tests/test_artifact_delivery_contract.py",
]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_contract(root: Path = ROOT) -> dict[str, Any]:
    return {
        "artifact_tool": "artifact_get",
        "catalog_sha256": sha256_file(root / CATALOG_PATH.relative_to(ROOT)),
        "client_delivery_meta_key": "hwpx/artifactDelivery",
        "content_attachment_type": "resource_link",
        "limits": {
            "bindings": 65_536,
            "default_ttl_seconds": 120,
            "max_range_bytes": 67_108_864,
            "max_ttl_seconds": 900,
            "max_url_bytes": 2_048,
            "min_ttl_seconds": 30,
        },
        "p15_04_audited_source_commit": (
            "4c6224f6001c5daadaaaec907c0bba86db7c6c0f"
        ),
        "required_behaviors": [
            "frozen_artifact_get_schema",
            "tenant_project_artifact_binding",
            "artifact_acl_rechecked",
            "binding_generation_revokes_old_url",
            "signed_url_only_in_client_meta",
            "subject_project_content_and_expiry_signed",
            "single_bounded_byte_range",
            "current_acl_state_and_digest_rechecked_at_redemption",
            "model_visible_content_has_no_token_or_bytes",
        ],
        "rust_artifact_delivery_tests": 13,
        "schema_version": "hwpx-agent.p15-artifact-delivery-contract/v1",
        "scope": "current_pc_hancom_2020_local_artifact_delivery_reference",
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
    errors = [] if actual == expected else ["artifact delivery contract drift"]
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
