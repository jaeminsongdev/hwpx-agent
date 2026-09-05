from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-quota-contract-v1.json"
POLICY_PATH = ROOT / "protocol/mcp/p15-quota-policy-v1.json"
ERROR_V1_PATH = ROOT / "protocol/mcp/p15-public-error-catalog-v1.json"
ERROR_V2_PATH = ROOT / "protocol/mcp/p15-public-error-catalog-v2.json"
P15_06_REVISION = "f36a07e988558b4481c50955a0f76bd69c516d9d"
P15_06_CONTRACT_SHA256 = "ae33d499350ca53f55534744036fc5830e4748efe943482b90c9e063bf54bd8b"
P15_08_SUPERSEDING_VALIDATOR = "tools/p15/validate_telemetry_contract.py"
P16_SOURCE_QUALIFICATION = "tools/p16/p15_source_qualification.py"
P15_07_AUDITED_REVISION = "e15921a59d45056c46b8ae94b6f6af778746c534"
P15_08_SUPERSEDED_PATHS = {
    "Cargo.lock",
    "Cargo.toml",
    "security/dependency-policy.json",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/build_quota_contract.py",
    "tools/p15/validate_quota_contract.py",
}

EXPECTED_KEYS = {
    "buckets",
    "error_catalog_additions",
    "error_catalog_v1_sha256",
    "error_catalog_v2_sha256",
    "handler_sequence_preserved",
    "job_classes",
    "limits",
    "meta_keys",
    "p15_06_audited_source_commit",
    "p15_06_contract_sha256",
    "public_envelope_version",
    "quota_policy_sha256",
    "required_behaviors",
    "runtime_error_codes",
    "rust_quota_tests",
    "rust_regression_tests",
    "schema_version",
    "scope",
    "source_locks",
    "stages",
    "target_profile",
    "tool_catalog_sha256",
}
EXPECTED_BEHAVIORS = [
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
]
EXPECTED_STAGES = [
    "admission",
    "authenticate",
    "parse",
    "input_validation",
    "policy",
    "quota",
    "dispatch",
    "output_validation",
]
EXPECTED_POLICY = {
    "buckets": {
        "capability": {"capacity": 30, "refill_tokens_per_window": 30},
        "tenant": {"capacity": 120, "refill_tokens_per_window": 120},
        "user": {"capacity": 60, "refill_tokens_per_window": 60},
    },
    "job_classes": [
        {
            "capacity": 8,
            "job_class": "standard",
            "refill_tokens_per_window": 8,
            "tools": [
                "document_create",
                "document_edit",
                "document_transform",
                "document_validate",
            ],
        },
        {
            "capacity": 2,
            "job_class": "render",
            "refill_tokens_per_window": 2,
            "tools": ["document_export", "document_render"],
        },
    ],
    "replay_ttl_seconds": 900,
    "schema_version": "hwpx-agent.quota-policy/v1",
    "state_limits": {"bucket_entries": 65_536, "replay_entries": 65_536},
    "window_seconds": 60,
}
EXPECTED_ERROR_CODES = [
    "AUTHENTICATION_FAILED",
    "AUTHENTICATION_UNAVAILABLE",
    "POLICY_DENIED",
    "POLICY_UNAVAILABLE",
    "QUOTA_EXCEEDED",
    "QUOTA_UNAVAILABLE",
    "REQUEST_CONFLICT",
    "RESOURCE_NOT_FOUND",
    "SERVICE_REJECTED",
    "SERVICE_UNAVAILABLE",
    "TOOL_ARGUMENTS_MALFORMED",
    "TOOL_INPUT_SCHEMA_INVALID",
    "TOOL_OUTPUT_SCHEMA_INVALID",
    "TOOL_REQUEST_TOO_LARGE",
    "TOOL_RESULT_CORRELATION_MISMATCH",
    "TOOL_UNKNOWN",
]
EXPECTED_SOURCE_PATHS = [
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


def safe_sha256(path: Path, errors: list[str], label: str) -> str:
    try:
        return sha256(path)
    except Exception:
        errors.append(label)
        return ""


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


def historical_p15_06_is_intact(root: Path, contract: dict[str, Any]) -> bool:
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
            ["git", "show", f"{P15_06_REVISION}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0 or hashlib.sha256(result.stdout).hexdigest() != expected:
            return False
    return True


def validate_p15_08_supersession(root: Path) -> list[str]:
    validator_path = root / P15_08_SUPERSEDING_VALIDATOR
    specification = importlib.util.spec_from_file_location(
        "p15_telemetry_superseding_validator", validator_path
    )
    if specification is None or specification.loader is None:
        return ["p15_08_supersession.validator_load"]
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
        errors = module.validate(root)
    except Exception:
        return ["p15_08_supersession.validation"]
    if errors:
        return ["p15_08_supersession.contract"]
    return []


def validate_p16_source_qualification(root: Path) -> dict[str, tuple[str, str]]:
    path = (Path(__file__).resolve().parents[1] / "p16/p15_source_qualification.py").resolve()
    name = "_hwpx_agent_p16_p15_source_qualification"
    module = sys.modules.get(name)
    if module is None or Path(str(getattr(module, "__file__", ""))).resolve() != path:
        sys.modules.pop(name, None)
        specification = importlib.util.spec_from_file_location(name, path)
        if specification is None or specification.loader is None:
            return {}
        module = importlib.util.module_from_spec(specification)
        sys.modules[name] = module
        try:
            specification.loader.exec_module(module)
        except Exception:
            sys.modules.pop(name, None)
            return {}
    try:
        return module.verified_quota_replacements(root)
    except Exception:
        return {}


def historical_p15_07_source_matches(root: Path, relative: str, expected: str) -> bool:
    result = subprocess.run(
        ["git", "show", f"{P15_07_AUDITED_REVISION}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    content = result.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return result.returncode == 0 and hashlib.sha256(content).hexdigest() == expected


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    p15_08_supersession_errors = validate_p15_08_supersession(root)
    p16_source_replacements = validate_p16_source_qualification(root)
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
    except Exception as error:
        return [f"contract.load:{type(error).__name__}"]
    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    if contract.get("schema_version") != "hwpx-agent.p15-quota-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_local_quota_reference":
        errors.append("contract.scope")
    if contract.get("target_profile") != "hancom-hangul-2020-secondary":
        errors.append("contract.target_profile")
    if contract.get("p15_06_audited_source_commit") != P15_06_REVISION:
        errors.append("contract.predecessor")
    if contract.get("p15_06_contract_sha256") != P15_06_CONTRACT_SHA256:
        errors.append("contract.predecessor_digest")
    predecessor_path = root / "implementation/p15/p15-error-mapping-contract-v1.json"
    try:
        predecessor = load_json(predecessor_path)
    except Exception:
        predecessor = {}
        errors.append("predecessor.load")
    if safe_sha256(predecessor_path, errors, "predecessor.digest_read") != P15_06_CONTRACT_SHA256:
        errors.append("predecessor.digest")
    if predecessor and not historical_p15_06_is_intact(root, predecessor):
        errors.append("predecessor.historical_sources")
    if contract.get("required_behaviors") != EXPECTED_BEHAVIORS:
        errors.append("contract.behaviors")
    if contract.get("stages") != EXPECTED_STAGES:
        errors.append("contract.stages")
    if contract.get("handler_sequence_preserved") is not True:
        errors.append("contract.handler_sequence")
    if contract.get("public_envelope_version") != "hwpx-agent.error/v2":
        errors.append("contract.envelope_version")
    if contract.get("rust_quota_tests") != 8 or contract.get("rust_regression_tests") != 45:
        errors.append("contract.rust_tests")
    if contract.get("meta_keys") != [
        "hwpx/quotaPolicySha256",
        "hwpx/retryAfterSeconds",
    ]:
        errors.append("contract.meta_keys")

    try:
        policy = load_json(root / POLICY_PATH.relative_to(ROOT))
    except Exception as error:
        policy = {}
        errors.append(f"policy.load:{type(error).__name__}")
    if policy != EXPECTED_POLICY:
        errors.append("policy.content")
    policy_hash = safe_sha256(
        root / POLICY_PATH.relative_to(ROOT), errors, "policy.digest_read"
    )
    if contract.get("quota_policy_sha256") != policy_hash:
        errors.append("contract.policy_digest")
    if contract.get("buckets") != EXPECTED_POLICY["buckets"]:
        errors.append("contract.buckets")
    if contract.get("job_classes") != EXPECTED_POLICY["job_classes"]:
        errors.append("contract.job_classes")
    if contract.get("limits") != {
        "bucket_entries": 65_536,
        "replay_entries": 65_536,
        "replay_ttl_seconds": 900,
        "window_seconds": 60,
    }:
        errors.append("contract.limits")

    try:
        error_v1 = load_json(root / ERROR_V1_PATH.relative_to(ROOT))
        error_v2 = load_json(root / ERROR_V2_PATH.relative_to(ROOT))
    except Exception as error:
        error_v1 = {}
        error_v2 = {}
        errors.append(f"error_catalog.load:{type(error).__name__}")
    v1_hash = safe_sha256(
        root / ERROR_V1_PATH.relative_to(ROOT), errors, "error_v1.digest_read"
    )
    v2_hash = safe_sha256(
        root / ERROR_V2_PATH.relative_to(ROOT), errors, "error_v2.digest_read"
    )
    if contract.get("error_catalog_v1_sha256") != v1_hash:
        errors.append("contract.error_v1_digest")
    if contract.get("error_catalog_v2_sha256") != v2_hash:
        errors.append("contract.error_v2_digest")
    if error_v1.get("schema_version") != "hwpx-agent.public-error-catalog/v1":
        errors.append("error_v1.schema")
    if error_v2.get("schema_version") != "hwpx-agent.public-error-catalog/v2":
        errors.append("error_v2.schema")
    entries_v1 = error_v1.get("errors")
    entries_v2 = error_v2.get("errors")
    if not isinstance(entries_v1, list) or len(entries_v1) != 14:
        entries_v1 = []
        errors.append("error_v1.entries")
    if not isinstance(entries_v2, list) or len(entries_v2) != 16:
        entries_v2 = []
        errors.append("error_v2.entries")
    codes_v2 = [entry.get("error_code") for entry in entries_v2 if isinstance(entry, dict)]
    if codes_v2 != EXPECTED_ERROR_CODES or contract.get("runtime_error_codes") != codes_v2:
        errors.append("error_v2.codes")
    if contract.get("error_catalog_additions") != ["QUOTA_EXCEEDED", "QUOTA_UNAVAILABLE"]:
        errors.append("contract.error_additions")
    by_code_v1 = {
        entry.get("error_code"): entry for entry in entries_v1 if isinstance(entry, dict)
    }
    by_code_v2 = {
        entry.get("error_code"): entry for entry in entries_v2 if isinstance(entry, dict)
    }
    for code, old in by_code_v1.items():
        current = by_code_v2.get(code)
        if not isinstance(current, dict):
            errors.append(f"error_v2.missing:{code}")
            continue
        expected = dict(old)
        if code == "REQUEST_CONFLICT":
            expected["allowed_stages"] = ["quota", "dispatch"]
        if current != expected:
            errors.append(f"error_v2.non_additive:{code}")
    expected_quota = {
        "QUOTA_EXCEEDED": ("storage", True, "retry_later"),
        "QUOTA_UNAVAILABLE": ("backend", True, "retry_later"),
    }
    for code, (category, retryable, recovery) in expected_quota.items():
        entry = by_code_v2.get(code, {})
        if (
            entry.get("allowed_stages") != ["quota"]
            or entry.get("category") != category
            or entry.get("retryable") is not retryable
            or entry.get("recovery_action") != recovery
        ):
            errors.append(f"error_v2.quota_mapping:{code}")

    schema_path = root / "specs/error-envelope.schema.json"
    try:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        schema_validator = Draft202012Validator(schema)
    except Exception as error:
        schema_validator = None
        errors.append(f"envelope_schema.load:{type(error).__name__}")
    if schema_validator is not None:
        for index, entry in enumerate(entries_v2):
            if not isinstance(entry, dict):
                continue
            envelope = {
                "schema_version": "hwpx-agent.error/v2",
                "request_id": "req_quota001",
                "error_code": entry.get("error_code"),
                "category": entry.get("category"),
                "safe_message": entry.get("safe_message"),
                "retryable": entry.get("retryable"),
                "stage": entry.get("allowed_stages", [None])[0],
                "details": {},
                "recovery": [{"action": entry.get("recovery_action")}],
            }
            if list(schema_validator.iter_errors(envelope)):
                errors.append(f"envelope_schema.catalog[{index}]")

    if contract.get("tool_catalog_sha256") != (
        "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
    ):
        errors.append("contract.tool_catalog_digest")
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
                if p16_source_replacements.get(relative) == (expected, observed):
                    continue
                if relative not in P15_08_SUPERSEDED_PATHS or p15_08_supersession_errors:
                    errors.append(f"source_lock[{index}].digest")
                elif not historical_p15_07_source_matches(root, relative, expected):
                    errors.append(f"source_lock[{index}].historical_digest")

    quota_source = (root / "crates/mcp-control-plane/src/quota.rs").read_text(encoding="utf-8")
    for token in [
        "pub trait QuotaService",
        "pub struct InMemoryQuotaService",
        "BucketKey::Tenant",
        "BucketKey::User",
        "BucketKey::Capability",
        "BucketKey::JobClass",
        "retry_after_seconds",
        "IdempotencyConflict",
        ".checked_sub(self.last_refill_unix_seconds)",
        "state.buckets.len().saturating_add(missing)",
    ]:
        if token not in quota_source:
            errors.append(f"quota.token:{token}")
    if QUOTA_POLICY_DIGEST_TOKEN(policy_hash) not in quota_source:
        errors.append("quota.policy_digest")
    handler = (root / "crates/mcp-control-plane/src/handler.rs").read_text(encoding="utf-8")
    sequence = [
        "authenticate_public_mcp(",
        "parse_unique_value(",
        "input_is_valid(",
        ".policy.authorize(",
        ".admit(&context, tool, &arguments, now_unix_seconds)",
        ".gateway.dispatch(",
        "output_is_valid(",
        "correlation.matches(",
    ]
    positions = [handler.find(token) for token in sequence]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("handler.execution_order")
    if handler.count("self.gateway.dispatch(call)") != 1:
        errors.append("handler.dispatch_count")
    for token in [
        '"hwpx/quotaPolicySha256"',
        '"hwpx/retryAfterSeconds"',
        "map_quota_error(error)",
        "error_with_retry_after",
    ]:
        if token not in handler:
            errors.append(f"handler.token:{token}")
    error_source = (root / "crates/mcp-control-plane/src/error_catalog.rs").read_text(
        encoding="utf-8"
    )
    for token in [
        "QuotaExceeded",
        "QuotaUnavailable",
        "PublicErrorStage::Quota",
        "pub const fn map_quota_error(",
    ]:
        if token not in error_source:
            errors.append(f"error_mapping.token:{token}")
    tests = (root / "crates/mcp-control-plane/tests/quota_service.rs").read_text(
        encoding="utf-8"
    )
    if tests.count("#[test]") != 8:
        errors.append("rust_tests.count")
    for token in [
        "render_job_class_enforces_burst_and_exact_retry_guidance",
        "capability_burst_is_bounded_without_cross_tenant_or_user_starvation",
        "idempotent_replay_is_not_recharged_and_payload_reuse_conflicts",
        "concurrent_burst_has_exactly_two_render_winners",
        "handler_returns_bounded_retry_metadata_without_dispatch",
    ]:
        if token not in tests:
            errors.append(f"rust_tests.token:{token}")
    for forbidden in ["unsafe {", "std::process", "Command::", "HAction", "raw_xml"]:
        if forbidden in quota_source or forbidden in handler:
            errors.append(f"rust.forbidden:{forbidden}")
    return errors


def QUOTA_POLICY_DIGEST_TOKEN(value: str) -> str:
    return f'pub const QUOTA_POLICY_SHA256: &str =\n    "{value}";'


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "error_codes": len(EXPECTED_ERROR_CODES),
                "errors": errors,
                "job_classes": 2,
                "rust_quota_tests": 8,
                "schema_version": "hwpx-agent.p15-quota-validation/v1",
                "source_files": len(EXPECTED_SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
