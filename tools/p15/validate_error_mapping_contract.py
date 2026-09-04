from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-error-mapping-contract-v1.json"
ERROR_CATALOG_PATH = ROOT / "protocol/mcp/p15-public-error-catalog-v1.json"

EXPECTED_KEYS = {
    "error_catalog_sha256",
    "error_codes",
    "error_envelope_schema_sha256",
    "handler_sequence_preserved",
    "p15_05_implementation_commit",
    "public_envelope_version",
    "required_behaviors",
    "rust_error_mapping_tests",
    "rust_handler_regression_tests",
    "schema_version",
    "scope",
    "source_locks",
    "stages",
    "target_profile",
    "tool_catalog_sha256",
}
EXPECTED_STAGES = [
    "admission",
    "authenticate",
    "parse",
    "input_validation",
    "policy",
    "dispatch",
    "output_validation",
]
EXPECTED_BEHAVIORS = [
    "digest_pinned_closed_error_catalog",
    "authentication_before_argument_parse",
    "server_correlation_before_validated_input",
    "validated_public_request_id_after_input_validation",
    "authentication_oracle_collapsed",
    "typed_auth_policy_gateway_job_artifact_mapping",
    "single_bounded_recovery_action",
    "empty_public_details",
    "no_secret_path_token_tenant_or_backend_leakage",
]
EXPECTED_ERRORS = [
    ("AUTHENTICATION_FAILED", "security", ["authenticate"], False, "reauthenticate"),
    ("AUTHENTICATION_UNAVAILABLE", "security", ["authenticate"], True, "retry_later"),
    ("POLICY_DENIED", "security", ["policy"], False, "request_access"),
    ("POLICY_UNAVAILABLE", "security", ["policy"], True, "retry_later"),
    ("REQUEST_CONFLICT", "conflict", ["dispatch"], False, "refresh_resource"),
    ("RESOURCE_NOT_FOUND", "document", ["policy", "dispatch"], False, "refresh_resource"),
    ("SERVICE_REJECTED", "backend", ["dispatch"], False, "inspect_request"),
    ("SERVICE_UNAVAILABLE", "backend", ["dispatch"], True, "retry_later"),
    ("TOOL_ARGUMENTS_MALFORMED", "input", ["parse"], False, "fix_request"),
    ("TOOL_INPUT_SCHEMA_INVALID", "input", ["input_validation"], False, "fix_request"),
    ("TOOL_OUTPUT_SCHEMA_INVALID", "internal", ["output_validation"], False, "contact_support"),
    ("TOOL_REQUEST_TOO_LARGE", "input", ["admission"], False, "reduce_request"),
    (
        "TOOL_RESULT_CORRELATION_MISMATCH",
        "internal",
        ["output_validation"],
        False,
        "contact_support",
    ),
    ("TOOL_UNKNOWN", "input", ["admission"], False, "use_supported_tool"),
]
EXPECTED_SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/06_mcp_api/04_error_model.md",
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    if not 0 < resolved.stat().st_size <= 2_000_000:
        raise ValueError("source file shape is invalid")
    return resolved


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
    except Exception as error:
        return [f"contract.load:{type(error).__name__}"]
    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    if contract.get("schema_version") != "hwpx-agent.p15-error-mapping-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_local_public_error_reference":
        errors.append("contract.scope")
    if contract.get("target_profile") != "hancom-hangul-2020-secondary":
        errors.append("contract.target_profile")
    if contract.get("p15_05_implementation_commit") != (
        "dde79ff3fa86953c7f3e6e8e2402479eddee813e"
    ):
        errors.append("contract.predecessor")
    if contract.get("public_envelope_version") != "hwpx-agent.error/v2":
        errors.append("contract.envelope_version")
    if contract.get("handler_sequence_preserved") is not True:
        errors.append("contract.handler_sequence")
    if contract.get("required_behaviors") != EXPECTED_BEHAVIORS:
        errors.append("contract.behaviors")
    if contract.get("stages") != EXPECTED_STAGES:
        errors.append("contract.stages")
    if contract.get("rust_error_mapping_tests") != 5:
        errors.append("contract.mapping_tests")
    if contract.get("rust_handler_regression_tests") != 16:
        errors.append("contract.handler_tests")

    try:
        catalog = load_json(root / ERROR_CATALOG_PATH.relative_to(ROOT))
    except Exception as error:
        errors.append(f"catalog.load:{type(error).__name__}")
        catalog = {}
    try:
        catalog_hash = sha256(root / ERROR_CATALOG_PATH.relative_to(ROOT))
    except Exception:
        catalog_hash = ""
        errors.append("catalog.digest")
    if contract.get("error_catalog_sha256") != catalog_hash:
        errors.append("contract.error_catalog_sha256")
    if catalog.get("schema_version") != "hwpx-agent.public-error-catalog/v1" or set(
        catalog
    ) != {"schema_version", "errors"}:
        errors.append("catalog.root")
    entries = catalog.get("errors")
    if not isinstance(entries, list) or len(entries) != len(EXPECTED_ERRORS):
        errors.append("catalog.entries")
        entries = []
    observed_codes: list[Any] = []
    for index, expected in enumerate(EXPECTED_ERRORS):
        if index >= len(entries) or not isinstance(entries[index], dict):
            errors.append(f"catalog[{index}].shape")
            continue
        entry = entries[index]
        code, category, stages, retryable, recovery = expected
        if set(entry) != {
            "allowed_stages",
            "category",
            "error_code",
            "recovery_action",
            "retryable",
            "safe_message",
        }:
            errors.append(f"catalog[{index}].keys")
        observed_codes.append(entry.get("error_code"))
        if (
            entry.get("error_code") != code
            or entry.get("category") != category
            or entry.get("allowed_stages") != stages
            or entry.get("retryable") is not retryable
            or entry.get("recovery_action") != recovery
        ):
            errors.append(f"catalog[{index}].mapping")
        message = entry.get("safe_message")
        if (
            not isinstance(message, str)
            or not 0 < len(message.encode("utf-8")) <= 200
            or any(ord(character) < 0x20 or ord(character) > 0x7E for character in message)
        ):
            errors.append(f"catalog[{index}].safe_message")
    if (
        not all(isinstance(code, str) for code in observed_codes)
        or observed_codes != sorted(observed_codes)
        or contract.get("error_codes") != observed_codes
    ):
        errors.append("catalog.code_order")

    schema_path = root / "specs/error-envelope.schema.json"
    try:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        schema_validator = Draft202012Validator(schema)
    except Exception as error:
        errors.append(f"envelope_schema.load:{type(error).__name__}")
        schema_validator = None
    try:
        schema_hash = sha256(schema_path)
    except Exception:
        schema_hash = ""
    if contract.get("error_envelope_schema_sha256") != schema_hash:
        errors.append("contract.envelope_schema_sha256")
    if schema_validator is not None:
        for index, (code, category, stages, retryable, recovery) in enumerate(EXPECTED_ERRORS):
            if index >= len(entries):
                continue
            message = entries[index].get("safe_message")
            if not isinstance(message, str):
                continue
            envelope = {
                "schema_version": "hwpx-agent.error/v2",
                "request_id": "req_server_0123456789abcdef0123456789abcdef",
                "error_code": code,
                "category": category,
                "safe_message": message,
                "retryable": retryable,
                "stage": stages[0],
                "details": {},
                "recovery": [{"action": recovery}],
            }
            if list(schema_validator.iter_errors(envelope)):
                errors.append(f"envelope_schema.catalog[{index}]")
        if entries and isinstance(entries[0], dict):
            first = entries[0]
            message = first.get("safe_message")
            if isinstance(message, str):
                leaked = {
                    "schema_version": "hwpx-agent.error/v2",
                    "request_id": "req_server_0123456789abcdef0123456789abcdef",
                    "error_code": "AUTHENTICATION_FAILED",
                    "category": "security",
                    "safe_message": message,
                    "retryable": False,
                    "stage": "authenticate",
                    "details": {"local_path": "C:/private/token"},
                    "recovery": [{"action": "reauthenticate"}],
                }
                if not list(schema_validator.iter_errors(leaked)):
                    errors.append("envelope_schema.accepted_local_path")

    if contract.get("tool_catalog_sha256") != (
        "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
    ):
        errors.append("contract.tool_catalog_sha256")
    if sha256(root / "implementation/p15/p15-artifact-delivery-contract-v1.json") != (
        "df025b658d49991f80b392a8afa693c412ef14ad5e90c770356956405c7e42a5"
    ):
        errors.append("predecessor.artifact_contract")

    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != len(EXPECTED_SOURCE_PATHS):
        errors.append("contract.source_locks")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(locks):
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append(f"source_lock[{index}].shape")
                continue
            relative = entry.get("path")
            expected_hash = entry.get("sha256")
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
            if (
                not isinstance(expected_hash, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
            ):
                errors.append(f"source_lock[{index}].digest_shape")
            elif sha256(source) != expected_hash:
                errors.append(f"source_lock[{index}].digest")

    rust_catalog = (root / "crates/mcp-control-plane/src/error_catalog.rs").read_text(
        encoding="utf-8"
    )
    if f'pub const ERROR_CATALOG_SHA256: &str =\n    "{catalog_hash}";' not in rust_catalog:
        errors.append("rust.catalog_digest")
    for token in [
        "pub const fn map_auth_error(",
        "pub const fn map_policy_error(",
        "pub const fn map_gateway_error(",
        "pub fn map_async_job_error(",
        "pub fn map_artifact_delivery_error(",
    ]:
        if token not in rust_catalog:
            errors.append(f"rust.mapping:{token}")
    handler = (root / "crates/mcp-control-plane/src/handler.rs").read_text(encoding="utf-8")
    sequence = [
        "authenticate_public_mcp(",
        "parse_unique_value(",
        "input_is_valid(",
        ".policy.authorize(",
        ".gateway.dispatch(",
        "output_is_valid(",
        "correlation.matches(",
        "McpToolResult::success(",
    ]
    positions = [handler.find(token) for token in sequence]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("handler.execution_order")
    if handler.count("self.gateway.dispatch(call)") != 1:
        errors.append("handler.dispatch_count")
    for token in [
        '"schema_version": "hwpx-agent.error/v2"',
        '"hwpx/errorCatalogSha256"',
        '"details": {}',
        'format!("req_server_{}", Uuid::new_v4().simple())',
    ]:
        if token not in handler:
            errors.append(f"handler.token:{token}")
    if "internal_trace_id" in handler:
        errors.append("handler.internal_trace_exposure")
    for forbidden in ["unsafe {", "std::process", "Command::", "HAction", "raw_xml"]:
        if forbidden in rust_catalog or forbidden in handler:
            errors.append(f"rust.forbidden:{forbidden}")
    mapping_tests = (root / "crates/mcp-control-plane/tests/error_mapping.rs").read_text(
        encoding="utf-8"
    )
    handler_tests = (root / "crates/mcp-control-plane/tests/handler_contract.rs").read_text(
        encoding="utf-8"
    )
    if mapping_tests.count("#[test]") != 5:
        errors.append("rust.mapping_test_count")
    if handler_tests.count("#[test]") != 16:
        errors.append("rust.handler_test_count")
    return errors


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "error_codes": len(EXPECTED_ERRORS),
                "errors": errors,
                "rust_error_mapping_tests": 5,
                "schema_version": "hwpx-agent.p15-error-mapping-validation/v1",
                "source_files": len(EXPECTED_SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
