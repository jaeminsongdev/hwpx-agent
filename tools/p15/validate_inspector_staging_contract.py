from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-inspector-staging-contract-v1.json"
POLICY_PATH = ROOT / "protocol/mcp/p15-inspector-staging-policy-v1.json"
P15_08_CONTRACT_PATH = ROOT / "implementation/p15/p15-telemetry-contract-v1.json"
P15_08_REVISION = "9f9c6932518175906842a2cbb5915a0fb96d0d49"
P15_08_CONTRACT_SHA256 = (
    "9a0e32959a6129f316f609069e87e22f22fb68b11622935c7ca32c080f44e402"
)
P15_09_AUDITED_REVISION = "7ea2f84c244fe5bbd7926ba3f176dc5acafcf624"
P16_04_SUPERSEDING_VALIDATOR = "tools/p16/validate_widget_shell_successor.py"
CURRENT_SOURCE_HELPER = "tools/p17/frozen_current_source_v12.py"
P16_04_SUPERSEDED_PATHS = {
    "Cargo.toml",
    "Cargo.lock",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/validate_telemetry_contract.py",
    "tools/p15/validate_inspector_staging_contract.py",
    "tools/p15/tests/test_inspector_staging_contract.py",
}
EXPECTED_KEYS = {
    "driver_lifecycle",
    "evidence_schema_version",
    "inspector_version",
    "manual_exact_commit_evidence_required",
    "negative_probe_count",
    "node_sdk_version",
    "p15_08_audited_source_commit",
    "p15_08_contract_sha256",
    "production_deployment_qualified",
    "protocol_era",
    "required_behaviors",
    "rust_driver_tests",
    "schema_version",
    "scope",
    "source_locks",
    "target_profile",
    "tls_private_key_persisted",
    "tool_catalog_sha256",
    "tool_count",
    "transport",
}
EXPECTED_SOURCE_PATHS = [
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
EXPECTED_BEHAVIORS = [
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


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def bounded_file(root: Path, relative: str) -> Path:
    value = Path(relative)
    if not relative or "\\" in relative or value.is_absolute() or ".." in value.parts:
        raise ValueError("source path is not bounded")
    resolved_root = root.resolve(strict=True)
    candidate = root / value
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        raise ValueError("source path is linked")
    resolved = candidate.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise ValueError("source path escapes repository")
    if not 0 < resolved.stat().st_size <= 4_000_000:
        raise ValueError("source file shape is invalid")
    return resolved


def historical_predecessor_is_intact(root: Path, contract: dict[str, Any]) -> bool:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        return False
    for entry in locks:
        if not isinstance(entry, dict):
            return False
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            return False
        result = subprocess.run(
            ["git", "show", f"{P15_08_REVISION}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        normalized = result.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if result.returncode != 0 or hashlib.sha256(normalized).hexdigest() != expected:
            return False
    return True


def validate_p16_04_supersession(root: Path) -> list[str]:
    validator_path = root / P16_04_SUPERSEDING_VALIDATOR
    if not validator_path.is_file():
        return ["p16_04_supersession.validator_missing"]
    tools_path = str(validator_path.parent)
    inserted = tools_path not in sys.path
    try:
        if inserted:
            sys.path.insert(0, tools_path)
        specification = importlib.util.spec_from_file_location(
            "p16_widget_shell_superseding_validator", validator_path
        )
        if specification is None or specification.loader is None:
            return ["p16_04_supersession.validator_load"]
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        contract = json.loads(
            (root / "implementation/p16/p16-widget-shell-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        errors = module.validate(contract)
    except Exception:
        return ["p16_04_supersession.validation"]
    finally:
        if inserted:
            sys.path.remove(tools_path)
    if errors:
        return ["p16_04_supersession.contract"]
    return []


def validate_current_source_qualification(
    root: Path, locks: list[dict[str, Any]]
) -> dict[str, tuple[str, str]]:
    helper_path = Path(__file__).resolve().parents[1] / "p17/frozen_current_source_v12.py"
    try:
        specification = importlib.util.spec_from_file_location(
            "p17_frozen_current_source_v12_for_inspector", helper_path
        )
        if specification is None or specification.loader is None:
            return {}
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module.verified_replacements(root, locks)
    except Exception:
        return {}


def historical_p15_09_source_matches(
    root: Path, relative: str, expected: str
) -> bool:
    result = subprocess.run(
        ["git", "show", f"{P15_09_AUDITED_REVISION}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    normalized = result.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return (
        result.returncode == 0
        and hashlib.sha256(normalized).hexdigest() == expected
    )


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
        policy = load_json(root / POLICY_PATH.relative_to(ROOT))
        package = load_json(root / "web/mcp-staging/package.json")
    except Exception as error:
        return [f"load:{type(error).__name__}"]
    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    expected_scalars = {
        "schema_version": "hwpx-agent.p15-inspector-staging-contract/v1",
        "scope": "current_pc_hancom_2020_local_inspector_staging",
        "target_profile": "hancom-hangul-2020-secondary",
        "driver_lifecycle": "persistent_per_server_run",
        "evidence_schema_version": "hwpx-agent.p15-inspector-staging-receipt/v1",
        "inspector_version": "2.5.0",
        "node_sdk_version": "2.0.0",
        "protocol_era": "modern",
        "negative_probe_count": 8,
        "rust_driver_tests": 3,
        "tool_count": 18,
        "p15_08_audited_source_commit": P15_08_REVISION,
        "p15_08_contract_sha256": P15_08_CONTRACT_SHA256,
        "tool_catalog_sha256": "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(f"contract.{key}")
    if contract.get("required_behaviors") != EXPECTED_BEHAVIORS:
        errors.append("contract.behaviors")
    if contract.get("manual_exact_commit_evidence_required") is not True:
        errors.append("contract.manual_evidence")
    if contract.get("production_deployment_qualified") is not False:
        errors.append("contract.production_scope")
    if contract.get("tls_private_key_persisted") is not False:
        errors.append("contract.private_key")
    if contract.get("transport") != {
        "bind": "127.0.0.1",
        "endpoint": "/mcp",
        "scheme": "https",
    }:
        errors.append("contract.transport")

    predecessor_path = root / P15_08_CONTRACT_PATH.relative_to(ROOT)
    try:
        predecessor = load_json(predecessor_path)
        if sha256(predecessor_path) != P15_08_CONTRACT_SHA256:
            errors.append("predecessor.digest")
        if not historical_predecessor_is_intact(root, predecessor):
            errors.append("predecessor.historical_sources")
    except Exception:
        errors.append("predecessor.load")

    if policy.get("schema_version") != "hwpx-agent.p15-inspector-staging-policy/v1":
        errors.append("policy.schema")
    if policy.get("scope") != expected_scalars["scope"]:
        errors.append("policy.scope")
    if policy.get("target_profile") != expected_scalars["target_profile"]:
        errors.append("policy.target")
    if policy.get("tool_count") != 18:
        errors.append("policy.tools")
    if policy.get("runtime") != {
        "bind": "127.0.0.1",
        "driver_lifecycle": "persistent_per_server_run",
        "ephemeral_port": True,
        "host_validation": "localhost_allowlist",
        "origin_validation": "localhost_allowlist",
        "scheme": "https",
        "shutdown": "graceful_stdin_eof",
        "tls_certificate": "ephemeral_self_signed_p256_sha256",
    }:
        errors.append("policy.runtime")
    if policy.get("limits") != {
        "driver_concurrency": 4,
        "driver_request_bytes": 300_000,
        "driver_response_bytes": 1_048_576,
        "driver_timeout_milliseconds": 15_000,
        "http_body_bytes": 300_000,
        "http_connections": 32,
        "http_header_bytes": 16_384,
        "server_lifetime_seconds_maximum": 900,
    }:
        errors.append("policy.limits")
    evidence = policy.get("evidence")
    if not isinstance(evidence, dict) or any(
        evidence.get(key) is not False
        for key in [
            "arguments_persisted",
            "bearer_persisted",
            "certificate_persisted",
            "private_key_persisted",
            "result_payload_persisted",
        ]
    ):
        errors.append("policy.evidence")
    if evidence.get("temporary_bearer_configuration") != "deleted_before_receipt":
        errors.append("policy.temporary_bearer_configuration")
    if policy.get("negative_probes") != [
        "missing_auth",
        "invalid_auth",
        "wrong_path",
        "host_rebinding",
        "hostile_origin",
        "wrong_method",
        "oversized_body",
        "plaintext_http_rejected",
    ]:
        errors.append("policy.probes")
    if package.get("dependencies", {}).get("@modelcontextprotocol/node") != "2.0.0":
        errors.append("package.node_sdk")
    if package.get("dependencies", {}).get("@modelcontextprotocol/server") != "2.0.0":
        errors.append("package.server_sdk")
    if package.get("dependencies", {}).get("selfsigned") != "5.5.0":
        errors.append("package.tls")
    if package.get("devDependencies", {}).get("@modelcontextprotocol/inspector") != "2.5.0":
        errors.append("package.inspector")

    locks = contract.get("source_locks")
    current_source_replacements = (
        validate_current_source_qualification(root, locks)
        if isinstance(locks, list)
        else {}
    )
    p16_04_supersession_errors: list[str] | None = None
    if not isinstance(locks, list) or len(locks) != len(EXPECTED_SOURCE_PATHS):
        errors.append("contract.source_locks")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(locks):
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append(f"source_lock[{index}].shape")
                continue
            relative = entry.get("path")
            expected = entry.get("sha256")
            if (
                not isinstance(relative, str)
                or relative in seen
                or relative != EXPECTED_SOURCE_PATHS[index]
            ):
                errors.append(f"source_lock[{index}].path")
                continue
            seen.add(relative)
            try:
                source = bounded_file(root, relative)
            except Exception:
                errors.append(f"source_lock[{index}].bounded")
                continue
            if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                errors.append(f"source_lock[{index}].digest_shape")
            elif sha256(source) != expected:
                observed = sha256(source)
                if current_source_replacements.get(relative) == (expected, observed):
                    continue
                if p16_04_supersession_errors is None:
                    p16_04_supersession_errors = validate_p16_04_supersession(root)
                if (
                    relative not in P16_04_SUPERSEDED_PATHS
                    or p16_04_supersession_errors
                ):
                    errors.append(f"source_lock[{index}].digest")
                elif not historical_p15_09_source_matches(root, relative, expected):
                    errors.append(f"source_lock[{index}].historical_digest")

    server = (root / "web/mcp-staging/src/server.ts").read_text(encoding="utf-8")
    for token in [
        'server.listen(0, "127.0.0.1"',
        "localhostHostValidation()",
        "localhostOriginValidation()",
        'responseMode: "json"',
        'legacy: "stateless"',
        "class StagingDriver",
        "MAX_CONCURRENT_DRIVERS = 4",
        "privateKey.fill(0)",
        'process.stdin.once("end", requestShutdown)',
        "readBoundedJson(request)",
    ]:
        if token not in server:
            errors.append(f"server.token:{token}")
    for forbidden in [
        'listen(0, "0.0.0.0"',
        "rejectUnauthorized: false",
        "NODE_TLS_REJECT_UNAUTHORIZED",
        "shell: true",
        "console.log(authorizationHeader",
    ]:
        if forbidden in server:
            errors.append(f"server.forbidden:{forbidden}")

    driver = (root / "crates/mcp-staging-driver/src/main.rs").read_text(encoding="utf-8")
    for token in [
        "struct DriverState",
        "McpControlPlane::new",
        "authenticate_public_mcp",
        "read_bounded_line",
        "Zeroizing",
        "MAX_DRIVER_REQUEST_BYTES: usize = 300_000",
        '"driver_request_id"',
    ]:
        if token not in driver:
            errors.append(f"driver.token:{token}")
    production_driver = driver.split("#[cfg(test)]", maxsplit=1)[0]
    for forbidden in [".unwrap()", ".expect(", "unsafe {"]:
        if forbidden in production_driver:
            errors.append(f"driver.forbidden:{forbidden}")

    harness = (root / "tools/p15/run_inspector_staging.py").read_text(encoding="utf-8")
    for token in [
        '"--strict"',
        '"tools/list"',
        '"tools/call"',
        "TemporaryDirectory",
        '"DEVELOPMENT_PASS"',
        '"qualifying": tracked_clean',
        '"hangul_process_started": False',
        '"durable_secret_material_persisted": False',
        '"temporary_configuration_deleted_before_receipt"] = True',
    ]:
        if token not in harness:
            errors.append(f"harness.token:{token}")
    return errors


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "errors": errors,
                "negative_probes": 8,
                "schema_version": "hwpx-agent.p15-inspector-staging-validation/v1",
                "source_files": len(EXPECTED_SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
                "tools": 18,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
