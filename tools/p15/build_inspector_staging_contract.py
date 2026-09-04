from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-inspector-staging-contract-v1.json"
POLICY_PATH = ROOT / "protocol/mcp/p15-inspector-staging-policy-v1.json"
P15_08_CONTRACT_PATH = ROOT / "implementation/p15/p15-telemetry-contract-v1.json"
P15_08_REVISION = "9f9c6932518175906842a2cbb5915a0fb96d0d49"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "tsconfig.base.json",
    "deny.toml",
    "security/dependency-policy.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "protocol/mcp/p15-public-error-catalog-v2.json",
    "protocol/mcp/p15-quota-policy-v1.json",
    "protocol/mcp/p15-telemetry-policy-v1.json",
    "protocol/mcp/p15-inspector-staging-policy-v1.json",
    "implementation/p15/p15-telemetry-contract-v1.json",
    "implementation/p15/P15-09_INSPECTOR_STAGING.md",
    "crates/mcp-staging-driver/Cargo.toml",
    "crates/mcp-staging-driver/src/main.rs",
    "web/mcp-staging/package.json",
    "web/mcp-staging/tsconfig.json",
    "web/mcp-staging/src/server.ts",
    "web/mcp-staging/src/server.test.ts",
    "tools/p15/run_inspector_staging.py",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/build_telemetry_contract.py",
    "tools/p15/validate_telemetry_contract.py",
    "tools/p15/build_inspector_staging_contract.py",
    "tools/p15/validate_inspector_staging_contract.py",
    "tools/p15/tests/test_inspector_staging.py",
    "tools/p15/tests/test_inspector_staging_contract.py",
]

REQUIRED_BEHAVIORS = [
    "loopback_only_ephemeral_https_mcp_endpoint",
    "official_sdk_current_and_legacy_streamable_http_factory",
    "host_and_origin_rebinding_guards_before_routing",
    "rust_authentication_before_mcp_body_parsing",
    "persistent_rust_control_plane_across_http_exchanges",
    "bounded_correlated_ndjson_driver_transport",
    "exact_eighteen_tool_schema_annotation_and_metadata_discovery",
    "all_eighteen_tool_calls_through_existing_control_plane",
    "ephemeral_runtime_secrets_with_no_durable_secret_evidence",
    "graceful_node_and_rust_shutdown_before_receipt_publication",
    "hash_only_secret_free_git_ignored_receipt",
    "dirty_checkout_cannot_produce_qualifying_pass",
    "no_hangul_process_document_artifact_or_external_effect",
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
    package = load_json(root / "web/mcp-staging/package.json")
    return {
        "driver_lifecycle": policy["runtime"]["driver_lifecycle"],
        "evidence_schema_version": "hwpx-agent.p15-inspector-staging-receipt/v1",
        "inspector_version": package["devDependencies"]["@modelcontextprotocol/inspector"],
        "manual_exact_commit_evidence_required": True,
        "negative_probe_count": len(policy["negative_probes"]),
        "node_sdk_version": package["dependencies"]["@modelcontextprotocol/server"],
        "p15_08_audited_source_commit": P15_08_REVISION,
        "p15_08_contract_sha256": sha256_file(
            root / P15_08_CONTRACT_PATH.relative_to(ROOT)
        ),
        "production_deployment_qualified": False,
        "protocol_era": policy["protocol"]["inspector_protocol_era"],
        "required_behaviors": REQUIRED_BEHAVIORS,
        "rust_driver_tests": 3,
        "schema_version": "hwpx-agent.p15-inspector-staging-contract/v1",
        "scope": policy["scope"],
        "source_locks": [
            {"path": relative, "sha256": sha256_file(root / relative)}
            for relative in SOURCE_PATHS
        ],
        "target_profile": policy["target_profile"],
        "tls_private_key_persisted": False,
        "tool_catalog_sha256": sha256_file(
            root / "protocol/mcp/p15-public-tools-v1.json"
        ),
        "tool_count": policy["tool_count"],
        "transport": {
            "bind": policy["runtime"]["bind"],
            "endpoint": policy["protocol"]["endpoint"],
            "scheme": policy["runtime"]["scheme"],
        },
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
    errors = [] if actual == expected else ["Inspector staging contract drift"]
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
