#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator, FormatChecker
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import ExtractionError, read_regular_file

REGISTRY_SCHEMA = REPOSITORY_ROOT / "protocol/json-schema/automation-binding-registry-v1.schema.json"
SCHEMA_ROOT = Path(__file__).with_name("schemas")
REQUEST_SCHEMA = SCHEMA_ROOT / "runtime-probe-request-v1.schema.json"
TRACE_SCHEMA = SCHEMA_ROOT / "runtime-probe-trace-v1.schema.json"
RECEIPT_SCHEMA = SCHEMA_ROOT / "runtime-probe-receipt-v1.schema.json"
PROFILE_SCHEMA = REPOSITORY_ROOT / "specs/target-profile.schema.json"

EXPECTED_PROFILE_ID = "hancom-hangul-2020-secondary"
EXPECTED_BUILD = "11.0.0.9136"
EXPECTED_LOCALE = "ko-KR"
EXPECTED_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)
SAFE_CANARIES = {"edit.undo", "edit.redo"}
DEFAULT_READ_CAPABILITY = "edit.go_to"
CLIPBOARD_CAPABILITIES = {
    "edit.copy",
    "edit.cut",
    "edit.paste",
    "edit.paste_special",
}


@dataclass(frozen=True)
class ProbeVerificationConfig:
    registry: Path
    registry_sha256: str
    target_profile: Path
    profile_sha256: str
    contracts: Path
    contracts_sha256: str
    request: Path
    trace: Path
    receipt: Path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_locked(path: Path, expected: str | None, maximum: int, label: str) -> bytes:
    content = read_regular_file(path, maximum)
    if expected is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha256_bytes(content) != expected:
            raise ExtractionError(f"{label} SHA-256 mismatch")
    return content


def parse_json(content: bytes, label: str) -> dict:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ExtractionError(f"{label} root is not an object")
    return value


def validate_schema(value: object, schema_path: Path, label: str) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    return [
        f"{label} schema {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def flatten_scalar_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_scalar_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_scalar_strings(child)]
    return []


def expected_plan(binding: dict, contract: dict) -> tuple[str, str, str, bool, str]:
    capability_id = binding["capability_id"]
    if capability_id == "edit.undo":
        return (
            "safe_canary",
            "not_run",
            "safe_disposable_undo_redo_canary",
            False,
            "fixture_removed",
        )
    if capability_id == "edit.redo":
        return (
            "safe_canary",
            "not_run",
            "safe_disposable_undo_redo_canary",
            False,
            "fixture_restored",
        )
    if capability_id == DEFAULT_READ_CAPABILITY:
        return "not_run", "not_run", "safe_default_read_only", True, "none"
    if binding["scope_class"] in {"external_service", "security_control"}:
        return "blocked_by_risk", "blocked_by_risk", "external_or_security_scope", False, "none"
    if capability_id in CLIPBOARD_CAPABILITIES:
        return "blocked_by_risk", "blocked_by_risk", "clipboard_side_effect_risk", False, "none"
    if binding["scope_class"] == "workstation_ui":
        return "blocked_by_risk", "blocked_by_risk", "modal_or_workstation_state_risk", False, "none"
    if contract["risk"] in {"high", "critical"}:
        return "blocked_by_risk", "blocked_by_risk", "high_risk", False, "none"
    return "not_run", "not_run", "not_in_bounded_canary_allowlist", False, "none"


def verify(config: ProbeVerificationConfig) -> dict:
    errors: list[str] = []
    registry_content = read_locked(config.registry, config.registry_sha256, 32 * 1024 * 1024, "registry")
    profile_content = read_locked(config.target_profile, config.profile_sha256, 2 * 1024 * 1024, "profile")
    contracts_content = read_locked(config.contracts, config.contracts_sha256, 32 * 1024 * 1024, "contracts")
    request_content = read_locked(config.request, None, 4 * 1024 * 1024, "request")
    trace_content = read_locked(config.trace, None, 4 * 1024 * 1024, "trace")
    receipt_content = read_locked(config.receipt, None, 2 * 1024 * 1024, "receipt")
    registry = parse_json(registry_content, "registry")
    contracts_root = parse_json(contracts_content, "contracts")
    request = parse_json(request_content, "request")
    trace = parse_json(trace_content, "trace")
    receipt = parse_json(receipt_content, "receipt")
    errors.extend(validate_schema(registry, REGISTRY_SCHEMA, "registry"))
    errors.extend(validate_schema(request, REQUEST_SCHEMA, "request"))
    errors.extend(validate_schema(trace, TRACE_SCHEMA, "trace"))
    errors.extend(validate_schema(receipt, RECEIPT_SCHEMA, "receipt"))
    try:
        profile = yaml.safe_load(profile_content.decode("utf-8"))
        errors.extend(validate_schema(profile, PROFILE_SCHEMA, "profile"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        profile = {}
        errors.append(f"profile parse: {type(error).__name__}")

    expected_profile = {
        "profile_id": EXPECTED_PROFILE_ID,
        "exact_build": EXPECTED_BUILD,
        "locale": EXPECTED_LOCALE,
        "license_state": "approved",
    }
    for key, value in expected_profile.items():
        if profile.get(key) != value:
            errors.append(f"profile {key} mismatch")
    constraints = profile.get("constraints", {}) if isinstance(profile, dict) else {}
    if constraints.get("executable_architecture") != "x86":
        errors.append("profile architecture mismatch")
    if constraints.get("executable_sha256") != EXPECTED_EXECUTABLE_SHA256:
        errors.append("profile executable SHA-256 mismatch")

    contracts_rows = contracts_root.get("contracts", [])
    contract_map = {
        row.get("capability_id"): row for row in contracts_rows if isinstance(row, dict)
    }
    if contracts_root.get("count") != 609 or len(contract_map) != 609:
        errors.append("capability contracts coverage mismatch")

    candidates = [
        binding
        for binding in registry.get("bindings", [])
        if binding.get("status") == "candidate_unverified"
    ]
    candidate_map = {binding.get("capability_id"): binding for binding in candidates}
    request_rows = request.get("probes", [])
    request_map = {probe.get("capability_id"): probe for probe in request_rows}
    trace_rows = trace.get("probe_results", [])
    trace_map = {result.get("capability_id"): result for result in trace_rows}
    if not (
        len(candidate_map)
        == len(candidates)
        == len(request_map)
        == len(request_rows)
        == len(trace_map)
        == len(trace_rows)
    ):
        errors.append("candidate/request/trace cardinality or uniqueness mismatch")
    if set(candidate_map) != set(request_map) or set(candidate_map) != set(trace_map):
        errors.append("candidate/request/trace capability set mismatch")

    for capability_id, binding in candidate_map.items():
        probe = request_map.get(capability_id, {})
        result = trace_map.get(capability_id, {})
        contract = contract_map.get(capability_id)
        if contract is None:
            errors.append(f"contract missing: {capability_id}")
            continue
        invocation = binding.get("invocation", {})
        identity_fields = {
            "binding_key": binding.get("binding_key"),
            "feature_id": binding.get("feature_id"),
            "capability_id": capability_id,
            "scope_class": binding.get("scope_class"),
            "risk": contract.get("risk"),
            "mutability": contract.get("mutability"),
            "action_id": invocation.get("action_id"),
            "parameter_set_id": invocation.get("parameter_set_id"),
            "parameter_set_state": invocation.get("parameter_set_state"),
        }
        for key, value in identity_fields.items():
            if probe.get(key) != value:
                errors.append(f"request projection mismatch: {capability_id}/{key}")
        plan, disposition, reason, default_read, effect = expected_plan(binding, contract)
        expected_request = {
            "execution_plan": plan,
            "planned_disposition": disposition,
            "reason_code": reason,
            "default_read_planned": default_read,
            "expected_effect": effect,
        }
        for key, value in expected_request.items():
            if probe.get(key) != value:
                errors.append(f"request policy mismatch: {capability_id}/{key}")
        for key in ("binding_key", "feature_id", "capability_id"):
            if result.get(key) != probe.get(key):
                errors.append(f"trace projection mismatch: {capability_id}/{key}")
        if result.get("planned_execution") != plan:
            errors.append(f"trace plan mismatch: {capability_id}")

        if capability_id in SAFE_CANARIES:
            if not (
                result.get("disposition") == "verified"
                and result.get("execute_state") == "pass"
                and result.get("expected_effect_observed") is True
                and result.get("pre_snapshot_sha256")
                and result.get("post_snapshot_sha256")
                and result.get("default_read_state") == "not_applicable"
                and result.get("error_type") is None
                and result.get("error_hresult") is None
                and result.get("error_message_sha256") is None
            ):
                errors.append(f"safe canary evidence incomplete: {capability_id}")
        elif capability_id == DEFAULT_READ_CAPABILITY:
            default_read_passed = (
                result.get("disposition") == "not_run"
                and result.get("default_read_state") == "pass"
                and bool(result.get("default_shape_sha256"))
                and result.get("error_type") is None
                and result.get("error_hresult") is None
                and result.get("error_message_sha256") is None
            )
            default_read_failed = (
                result.get("disposition") == "failed"
                and result.get("default_read_state") == "failed"
                and bool(result.get("error_type"))
                and isinstance(result.get("error_hresult"), int)
                and bool(result.get("error_message_sha256"))
            )
            if not (
                (default_read_passed or default_read_failed)
                and result.get("execute_state") == "not_run"
                and result.get("expected_effect_observed") is False
            ):
                errors.append("default-read evidence incomplete")
        elif disposition == "blocked_by_risk":
            if not (
                result.get("disposition") == "blocked_by_risk"
                and result.get("execute_state") == "not_run"
                and result.get("default_read_state") in {"not_run", "not_applicable"}
                and result.get("expected_effect_observed") is False
                and result.get("error_type") is None
                and result.get("error_hresult") is None
                and result.get("error_message_sha256") is None
            ):
                errors.append(f"risk block was not preserved: {capability_id}")
        else:
            if not (
                result.get("disposition") == "not_run"
                and result.get("execute_state") == "not_run"
                and result.get("default_read_state") in {"not_run", "not_applicable"}
                and result.get("expected_effect_observed") is False
                and result.get("error_type") is None
                and result.get("error_hresult") is None
                and result.get("error_message_sha256") is None
            ):
                errors.append(f"bounded not-run was not preserved: {capability_id}")

    request_sha = sha256_bytes(request_content)
    trace_sha = sha256_bytes(trace_content)
    correlations = {
        "request registry": request.get("registry_sha256") == config.registry_sha256,
        "request profile": request.get("profile_sha256") == config.profile_sha256,
        "request contracts": request.get("contracts_sha256") == config.contracts_sha256,
        "trace request": trace.get("request_sha256") == request_sha,
        "trace registry": trace.get("registry_sha256") == config.registry_sha256,
        "receipt request": receipt.get("request_sha256") == request_sha,
        "receipt trace": receipt.get("trace_sha256") == trace_sha,
        "receipt registry": receipt.get("registry_sha256") == config.registry_sha256,
        "receipt profile": receipt.get("profile_sha256") == config.profile_sha256,
    }
    errors.extend(f"correlation mismatch: {key}" for key, passed in correlations.items() if not passed)

    fixture = trace.get("fixture", {})
    if not (
        fixture.get("input_sha256")
        and fixture.get("bootstrap_default_shape_sha256")
        and isinstance(fixture.get("bootstrap_default_member_count"), int)
        and fixture.get("input_sha256") == fixture.get("redo_snapshot_sha256")
        and fixture.get("input_sha256") == fixture.get("reopen_snapshot_sha256")
        and fixture.get("undo_snapshot_sha256") != fixture.get("input_sha256")
        and fixture.get("output_hwpx_sha256")
        and fixture.get("reopen_exact_match") is True
    ):
        errors.append("fixture undo/redo/save-reopen semantic chain mismatch")
    if trace.get("state") != "pass" or trace.get("error_code") is not None:
        errors.append("trace is not a clean pass")
    required_pass_phases = {
        "com_create",
        "version_check",
        "document_add",
        "fixture_insert",
        "default_parameter_read",
        "undo_canary",
        "redo_canary",
        "hwpx_save",
        "document_close_before_reopen",
        "hwpx_reopen",
        "semantic_reopen",
        "document_close",
        "quit",
    }
    if any(trace.get("phases", {}).get(phase) != "pass" for phase in required_pass_phases):
        errors.append("one or more required trace phases did not pass")
    if trace.get("quit_invoked") is not True:
        errors.append("trace did not prove Quit")

    coverage = Counter(result.get("disposition") for result in trace_rows)
    expected_coverage = {
        "candidate_count": len(candidates),
        "verified": coverage["verified"],
        "failed": coverage["failed"],
        "blocked_by_risk": coverage["blocked_by_risk"],
        "not_run": coverage["not_run"],
    }
    if receipt.get("coverage") != expected_coverage:
        errors.append("receipt coverage mismatch")
    runtime = receipt.get("runtime", {})
    if not (
        receipt.get("state") == "pass"
        and receipt.get("error_code") is None
        and receipt.get("target", {}).get("identity_match") is True
        and runtime.get("timed_out") is False
        and runtime.get("child_exit_code") == 0
        and runtime.get("unexpected_window_observed") is False
        and runtime.get("cleanup_refused_count") == 0
        and runtime.get("cleanup_error_count") == 0
        and runtime.get("remaining_hwp_process_count") == 0
    ):
        errors.append("receipt runtime closure is not a clean pass")

    raw_values = {
        value
        for binding in candidates
        for value in (
            binding.get("invocation", {}).get("action_id"),
            binding.get("invocation", {}).get("parameter_set_id"),
        )
        if isinstance(value, str)
    }
    public_scalar_values = set(flatten_scalar_strings(trace) + flatten_scalar_strings(receipt))
    leaked = sorted(raw_values & public_scalar_values)
    if leaked:
        errors.append(f"trace/receipt contains {len(leaked)} raw automation identifier values")
    receipt_strings = flatten_scalar_strings(receipt)
    if any(re.search(r"(?i)(?:[a-z]:\\|/users/|/home/)", value) for value in receipt_strings):
        errors.append("receipt contains an absolute private path")
    privacy = receipt.get("privacy", {})
    if any(
        privacy.get(key) is not False
        for key in (
            "raw_identifiers_present",
            "default_values_present",
            "absolute_private_paths_present",
            "user_document_opened",
            "external_network_invoked",
            "registry_or_system_setting_changed",
            "computer_use_click_or_type_invoked",
        )
    ):
        errors.append("receipt privacy boundary mismatch")

    for path, original, maximum, label in (
        (config.registry, registry_content, 32 * 1024 * 1024, "registry"),
        (config.target_profile, profile_content, 2 * 1024 * 1024, "profile"),
        (config.contracts, contracts_content, 32 * 1024 * 1024, "contracts"),
        (config.request, request_content, 4 * 1024 * 1024, "request"),
        (config.trace, trace_content, 4 * 1024 * 1024, "trace"),
        (config.receipt, receipt_content, 2 * 1024 * 1024, "receipt"),
    ):
        if read_regular_file(path, maximum) != original:
            errors.append(f"{label} changed during verification")

    return {
        "schema_version": "hwpx-agent.runtime-probe-verification/v1",
        "state": "pass" if not errors else "failed",
        "target_profile_id": EXPECTED_PROFILE_ID,
        "exact_build": EXPECTED_BUILD,
        "registry_sha256": config.registry_sha256,
        "request_sha256": request_sha,
        "trace_sha256": trace_sha,
        "candidate_count": len(candidates),
        "verified_count": coverage["verified"],
        "failed_count": coverage["failed"],
        "blocked_by_risk_count": coverage["blocked_by_risk"],
        "not_run_count": coverage["not_run"],
        "raw_identifier_value_leak_count": len(leaked),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-sha256", required=True)
    parser.add_argument("--target-profile", type=Path, required=True)
    parser.add_argument("--profile-sha256", required=True)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--contracts-sha256", required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = verify(
            ProbeVerificationConfig(
                registry=arguments.registry,
                registry_sha256=arguments.registry_sha256,
                target_profile=arguments.target_profile,
                profile_sha256=arguments.profile_sha256,
                contracts=arguments.contracts,
                contracts_sha256=arguments.contracts_sha256,
                request=arguments.request,
                trace=arguments.trace,
                receipt=arguments.receipt,
            )
        )
    except (ExtractionError, OSError, ValueError) as error:
        result = {
            "schema_version": "hwpx-agent.runtime-probe-verification/v1",
            "state": "failed",
            "errors": [str(error)],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("state") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
