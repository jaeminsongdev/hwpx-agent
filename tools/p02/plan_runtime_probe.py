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

from tools.p02.extract_help import (
    ExtractionError,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)

REGISTRY_SCHEMA = (
    REPOSITORY_ROOT
    / "protocol"
    / "json-schema"
    / "automation-binding-registry-v1.schema.json"
)
REQUEST_SCHEMA = Path(__file__).with_name("schemas") / "runtime-probe-request-v1.schema.json"
TARGET_PROFILE_SCHEMA = REPOSITORY_ROOT / "specs" / "target-profile.schema.json"
PRIVATE_OUTPUT_ROOT = REPOSITORY_ROOT / "implementation" / "p02" / "evidence"

EXPECTED_PROFILE_ID = "hancom-hangul-2020-secondary"
EXPECTED_PRODUCT = "Hancom Hangul 2020"
EXPECTED_BUILD = "11.0.0.9136"
EXPECTED_LOCALE = "ko-KR"
EXPECTED_ARCHITECTURE = "x86"
EXPECTED_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)
EXPECTED_PROG_ID = "HWPFrame.HwpObject.2"
EXECUTION_ALLOWLIST = ("edit.undo", "edit.redo")
DEFAULT_READ_ALLOWLIST = ("edit.go_to",)
CLIPBOARD_CAPABILITIES = {
    "edit.copy",
    "edit.cut",
    "edit.paste",
    "edit.paste_special",
}
MAX_REGISTRY_BYTES = 32 * 1024 * 1024
MAX_PROFILE_BYTES = 2 * 1024 * 1024
MAX_CONTRACT_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class ProbePlanConfig:
    registry: Path
    registry_sha256: str
    target_profile: Path
    profile_sha256: str
    contracts: Path
    contracts_sha256: str
    request_id: str
    fixture_id: str
    timeout_seconds: int
    output_root: Path
    output_relative: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_json(content: bytes, label: str) -> object:
    try:
        return json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"{label} is not valid UTF-8 JSON") from error


def validate_schema(value: object, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:20]
        )
        raise ExtractionError(f"{label} schema invalid: {details}")


def read_locked(path: Path, expected_sha256: str, maximum: int, label: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ExtractionError(f"{label} expected SHA-256 is invalid")
    content = read_regular_file(path, maximum)
    if sha256_bytes(content) != expected_sha256:
        raise ExtractionError(f"{label} SHA-256 mismatch")
    return content


def load_profile(content: bytes) -> dict:
    try:
        profile = yaml.safe_load(content.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise ExtractionError("target profile is not valid UTF-8 YAML") from error
    validate_schema(profile, TARGET_PROFILE_SCHEMA, "target profile")
    constraints = profile.get("constraints", {})
    expected = {
        "profile_id": EXPECTED_PROFILE_ID,
        "product": EXPECTED_PRODUCT,
        "major_release": "2020",
        "exact_build": EXPECTED_BUILD,
        "locale": EXPECTED_LOCALE,
        "license_state": "approved",
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise ExtractionError(f"target profile {key} mismatch")
    constraint_expectations = {
        "role": "primary_development",
        "installation_state": "installed_on_current_host",
        "executable_architecture": EXPECTED_ARCHITECTURE,
        "executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "runtime_probe_scope": "exact_identity_on_current_development_pc",
        "desktop_automation_release_state": (
            "allowed_for_bounded_personal_noncommercial_local_validation_only"
        ),
        "production_release_state": "disabled",
        "external_network": False,
    }
    for key, value in constraint_expectations.items():
        if constraints.get(key) != value:
            raise ExtractionError(f"target profile constraint {key} mismatch")
    return profile


def load_contracts(content: bytes) -> dict[str, dict]:
    value = parse_json(content, "capability contracts")
    if not isinstance(value, dict) or value.get("count") != 609:
        raise ExtractionError("capability contracts count mismatch")
    rows = value.get("contracts")
    if not isinstance(rows, list) or len(rows) != 609:
        raise ExtractionError("capability contracts rows mismatch")
    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ExtractionError("capability contract row is not an object")
        capability_id = row.get("capability_id")
        if not isinstance(capability_id, str) or capability_id in result:
            raise ExtractionError("capability contract ID missing or duplicate")
        if row.get("risk") not in {"low", "medium", "high", "critical"}:
            raise ExtractionError(f"capability contract risk invalid: {capability_id}")
        if row.get("mutability") not in {
            "read_only",
            "session_mutation",
            "artifact_mutation",
            "external_side_effect",
        }:
            raise ExtractionError(f"capability contract mutability invalid: {capability_id}")
        result[capability_id] = row
    return result


def classify_probe(binding: dict, contract: dict) -> tuple[str, str, str, bool]:
    capability_id = binding["capability_id"]
    if capability_id in EXECUTION_ALLOWLIST:
        expected_effect = "fixture_removed" if capability_id == "edit.undo" else "fixture_restored"
        return "safe_canary", "not_run", "safe_disposable_undo_redo_canary", False
    if capability_id in DEFAULT_READ_ALLOWLIST:
        if binding["invocation"]["parameter_set_state"] != "documented_candidate":
            raise ExtractionError("default-read allowlist candidate has no documented ParameterSet")
        return "not_run", "not_run", "safe_default_read_only", True
    if binding["scope_class"] in {"external_service", "security_control"}:
        return "blocked_by_risk", "blocked_by_risk", "external_or_security_scope", False
    if capability_id in CLIPBOARD_CAPABILITIES:
        return "blocked_by_risk", "blocked_by_risk", "clipboard_side_effect_risk", False
    if binding["scope_class"] == "workstation_ui":
        return "blocked_by_risk", "blocked_by_risk", "modal_or_workstation_state_risk", False
    if contract["risk"] in {"high", "critical"}:
        return "blocked_by_risk", "blocked_by_risk", "high_risk", False
    return "not_run", "not_run", "not_in_bounded_canary_allowlist", False


def build_request(
    config: ProbePlanConfig,
    registry: dict,
    contracts: dict[str, dict],
) -> dict:
    target = registry.get("target", {})
    expected_target = {
        "profile_id": EXPECTED_PROFILE_ID,
        "product": EXPECTED_PRODUCT,
        "major_release": "2020",
        "exact_build": EXPECTED_BUILD,
        "locale": EXPECTED_LOCALE,
        "architecture": EXPECTED_ARCHITECTURE,
        "profile_sha256": config.profile_sha256,
        "license_state": "approved",
        "routing_enabled": False,
    }
    for key, value in expected_target.items():
        if target.get(key) != value:
            raise ExtractionError(f"binding registry target {key} mismatch")
    if registry.get("restricted_derivative") is not True:
        raise ExtractionError("binding registry is not a restricted derivative")
    if registry.get("runtime_qualification") != {
        "state": "not_run",
        "probe_required": True,
        "qualified_binding_count": 0,
    }:
        raise ExtractionError("binding registry runtime qualification is not pristine")

    candidates = [
        binding
        for binding in registry.get("bindings", [])
        if binding.get("status") == "candidate_unverified"
    ]
    if len(candidates) != registry.get("coverage", {}).get("candidate_unverified_count"):
        raise ExtractionError("binding registry candidate coverage mismatch")
    if len(candidates) < 3:
        raise ExtractionError("binding registry has too few candidates for bounded canaries")

    probes: list[dict] = []
    for binding in sorted(candidates, key=lambda row: row["capability_id"]):
        capability_id = binding["capability_id"]
        contract = contracts.get(capability_id)
        if contract is None:
            raise ExtractionError(f"capability contract missing: {capability_id}")
        if contract.get("feature_id") != binding.get("feature_id"):
            raise ExtractionError(f"feature identity mismatch: {capability_id}")
        if contract.get("scope_class") != binding.get("scope_class"):
            raise ExtractionError(f"scope identity mismatch: {capability_id}")
        invocation = binding.get("invocation")
        if not isinstance(invocation, dict) or invocation.get("kind") != "action":
            raise ExtractionError(f"candidate invocation invalid: {capability_id}")
        execution_plan, disposition, reason, default_read = classify_probe(binding, contract)
        expected_effect = (
            "fixture_removed"
            if capability_id == "edit.undo"
            else "fixture_restored"
            if capability_id == "edit.redo"
            else "none"
        )
        probes.append(
            {
                "binding_key": binding["binding_key"],
                "feature_id": binding["feature_id"],
                "capability_id": capability_id,
                "scope_class": binding["scope_class"],
                "risk": contract["risk"],
                "mutability": contract["mutability"],
                "action_id": invocation["action_id"],
                "parameter_set_id": invocation["parameter_set_id"],
                "parameter_set_state": invocation["parameter_set_state"],
                "default_read_planned": default_read,
                "execution_plan": execution_plan,
                "planned_disposition": disposition,
                "reason_code": reason,
                "expected_effect": expected_effect,
            }
        )

    capability_ids = [probe["capability_id"] for probe in probes]
    if len(capability_ids) != len(set(capability_ids)):
        raise ExtractionError("probe candidate capability duplicate")
    if tuple(capability for capability in capability_ids if capability in EXECUTION_ALLOWLIST) != tuple(
        sorted(EXECUTION_ALLOWLIST)
    ):
        raise ExtractionError("safe execution allowlist is not fully represented")
    if tuple(capability for capability in capability_ids if capability in DEFAULT_READ_ALLOWLIST) != tuple(
        sorted(DEFAULT_READ_ALLOWLIST)
    ):
        raise ExtractionError("default-read allowlist is not fully represented")

    plans = Counter(probe["execution_plan"] for probe in probes)
    request = {
        "schema_version": "hwpx-agent.runtime-probe-request/v1",
        "request_id": config.request_id,
        "restricted_derivative": True,
        "registry_sha256": config.registry_sha256,
        "profile_sha256": config.profile_sha256,
        "contracts_sha256": config.contracts_sha256,
        "target": {
            "profile_id": EXPECTED_PROFILE_ID,
            "product": EXPECTED_PRODUCT,
            "major_release": "2020",
            "exact_build": EXPECTED_BUILD,
            "locale": EXPECTED_LOCALE,
            "architecture": EXPECTED_ARCHITECTURE,
            "prog_id": EXPECTED_PROG_ID,
            "registry_view": "Registry32",
            "client_apartment_state": "STA",
            "expected_executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        },
        "fixture": {
            "fixture_id": config.fixture_id,
            "kind": "generated_disposable_hwpx",
            "source_document_open_allowed": False,
            "publication": "private_no_overwrite",
        },
        "policy": {
            "timeout_seconds": config.timeout_seconds,
            "preexisting_hwp_process_policy": "refuse",
            "unexpected_window_policy": "unverified_and_stop",
            "cleanup_policy": "exact_session_identity_only",
            "raw_output_policy": "private_request_only_hash_public_receipt",
            "execution_allowlist": list(EXECUTION_ALLOWLIST),
            "default_read_allowlist": list(DEFAULT_READ_ALLOWLIST),
        },
        "probes": probes,
        "coverage": {
            "candidate_count": len(probes),
            "safe_canary_count": plans["safe_canary"],
            "default_read_count": sum(probe["default_read_planned"] for probe in probes),
            "blocked_by_risk_count": plans["blocked_by_risk"],
            "planned_not_run_count": plans["not_run"],
        },
    }
    validate_schema(request, REQUEST_SCHEMA, "runtime probe request")
    return request


def serialize(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def run(config: ProbePlanConfig) -> dict:
    registry_content = read_locked(
        config.registry, config.registry_sha256, MAX_REGISTRY_BYTES, "binding registry"
    )
    profile_content = read_locked(
        config.target_profile, config.profile_sha256, MAX_PROFILE_BYTES, "target profile"
    )
    contracts_content = read_locked(
        config.contracts, config.contracts_sha256, MAX_CONTRACT_BYTES, "capability contracts"
    )
    registry = parse_json(registry_content, "binding registry")
    validate_schema(registry, REGISTRY_SCHEMA, "binding registry")
    load_profile(profile_content)
    contracts = load_contracts(contracts_content)
    request = build_request(config, registry, contracts)
    for path, original, maximum, label in (
        (config.registry, registry_content, MAX_REGISTRY_BYTES, "binding registry"),
        (config.target_profile, profile_content, MAX_PROFILE_BYTES, "target profile"),
        (config.contracts, contracts_content, MAX_CONTRACT_BYTES, "capability contracts"),
    ):
        if read_regular_file(path, maximum) != original:
            raise ExtractionError(f"{label} changed during probe planning")

    if config.output_root.resolve() != PRIVATE_OUTPUT_ROOT.resolve():
        raise ExtractionError("runtime probe request may publish only under private P02 evidence")
    output = resolve_output(config.output_root, config.output_relative)
    payload = serialize(request)
    publish_no_overwrite(output, payload)
    return {
        "schema_version": "hwpx-agent.runtime-probe-plan-receipt/v1",
        "request_id": config.request_id,
        "target_profile_id": EXPECTED_PROFILE_ID,
        "exact_build": EXPECTED_BUILD,
        "registry_sha256": config.registry_sha256,
        "profile_sha256": config.profile_sha256,
        "contracts_sha256": config.contracts_sha256,
        "request_sha256": sha256_bytes(payload),
        "candidate_count": request["coverage"]["candidate_count"],
        "safe_canary_count": request["coverage"]["safe_canary_count"],
        "default_read_count": request["coverage"]["default_read_count"],
        "blocked_by_risk_count": request["coverage"]["blocked_by_risk_count"],
        "planned_not_run_count": request["coverage"]["planned_not_run_count"],
        "raw_identifiers_in_receipt": False,
        "runtime_execution_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-sha256", required=True)
    parser.add_argument("--target-profile", type=Path, required=True)
    parser.add_argument("--profile-sha256", required=True)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--contracts-sha256", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{32}", arguments.request_id):
        parser.error("--request-id must be 32 lowercase hexadecimal characters")
    if not re.fullmatch(r"[0-9a-f]{32}", arguments.fixture_id):
        parser.error("--fixture-id must be 32 lowercase hexadecimal characters")
    if not 30 <= arguments.timeout_seconds <= 300:
        parser.error("--timeout-seconds must be between 30 and 300")
    try:
        receipt = run(
            ProbePlanConfig(
                registry=arguments.registry,
                registry_sha256=arguments.registry_sha256,
                target_profile=arguments.target_profile,
                profile_sha256=arguments.profile_sha256,
                contracts=arguments.contracts,
                contracts_sha256=arguments.contracts_sha256,
                request_id=arguments.request_id,
                fixture_id=arguments.fixture_id,
                timeout_seconds=arguments.timeout_seconds,
                output_root=arguments.output_root,
                output_relative=arguments.output_relative,
            )
        )
    except (ExtractionError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.runtime-probe-plan-receipt/v1",
                    "state": "failed",
                    "error": str(error),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
