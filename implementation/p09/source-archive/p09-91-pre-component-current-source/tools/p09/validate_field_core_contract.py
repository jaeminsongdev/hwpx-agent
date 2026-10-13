#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-field-core-v1.json"
MIGRATION = "protocol/migrations/p09-field-engine-v0-to-v1.md"
POLICY = "implementation/p09/P09-01_FIELD_CORE_POLICY.md"
REPORT = "implementation/p09/P09-01_FIELD_CORE_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-01-field-core-source-qualification.v1.json"
BASE_COMMIT = "cd8acc540f351fb2259656c552fc848aff3c3812"

SOURCE_SHA256 = {
    "docs/04_feature_catalog/10_ref.md": "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4",
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29",
    "docs/09_roadmap/P09_fields_forms_notes_references.md": "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55",
    "docs/03_document_model/09_fields_controls_references.md": "3068742808467f298d289c7401980c617981d748dfa73422bab8f7174ef10a20",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/field_engine.rs": "c9c77c27f741cb985de6da734a14fdf28917d89500d25a73a8cce2d7e2ad5da5",
    "crates/domain-ir/tests/field_engine.rs": "15a3f49dab9aed32f087ec7aceb1c3d38617681f01162ce4415fe4b77338abb1",
}
CAPABILITIES = {
    "REF-001": "ref.field_insert",
    "REF-002": "ref.field_user",
    "REF-003": "ref.field_click_here",
    "REF-004": "ref.field_date_time",
    "REF-005": "ref.field_filename",
    "REF-006": "ref.field_page_number",
    "REF-007": "ref.field_section_number",
    "REF-008": "ref.field_object_number",
    "REF-009": "ref.field_update",
    "REF-010": "ref.field_lock",
}
STATE_BINDING = {
    "field_inventory": "ordered_complete_logical_native_pair_anchor_definition_result_policy_cache_lock_evaluation_style_payload_and_opaque_state",
    "document_state": "non_field_content_style_reference_resource_and_opaque_document_digests",
    "result_source": "explicit_cached_observation_and_evaluation_context_without_ambient_clock_filename_or_numbering_reads",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_the_named_insert_result_or_lock_transition_may_change_state",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "invalid_identity_anchor_name_text_locale_timezone_result_policy_or_digest_rejected",
    "logical_native_pair_and_anchor_collisions_rejected",
    "invalid_insertion_index_or_missing_target_rejected",
    "numeric_and_text_result_kind_mismatch_rejected",
    "locked_or_frozen_field_update_rejected",
    "no_op_transition_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_and_build",
    "plan_binding_tamper_rejected",
    "unrelated_field_and_document_state_change_rejected",
    "names_parameters_prompts_results_identities_anchors_digests_and_opaque_values_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
CLAIMS = {
    "unit_model_implemented": True,
    "ten_capabilities_unit_passed": True,
    "complete_bound_state_preserved": True,
    "request_and_build_drift_rejected": True,
    "direct_hwpx": False,
    "actual_hwpx": False,
    "actual_hangul": False,
    "field_readback": False,
    "semantic_reopen": False,
    "reference_update": False,
    "save_reopen": False,
    "render": False,
    "automation": False,
    "differential": False,
    "p09_01_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod field_engine;",
        "FieldEngineBuilder",
        "FieldDocumentState",
    ),
    "crates/domain-ir/src/field_engine.rs": (
        'FIELD_ENGINE_SCHEMA_VERSION: &str = "hwpx-agent.field-engine/v1"',
        "pub enum FieldDefinition",
        "pub enum FieldOperation",
        "pub struct FieldEngineBuilder",
        "fn reject_duplicate_json_keys(",
        "<redacted>",
    ),
    "crates/domain-ir/tests/field_engine.rs": (
        "inserts_all_eight_field_kinds_with_distinct_capability_ids",
        "updates_cached_result_with_explicit_context_and_preserves_every_unrelated_binding",
        "request_plan_and_build_recheck_exact_state_and_document_flow",
        "strict_json_rejects_duplicate_unknown_and_oversized_input",
    ),
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load(root: Path, relative: str) -> Any:
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard)


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)

    expected_root = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "model", "implementation_files", "state_binding",
        "failure_policy", "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_root:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.field-core-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P09-01" or contract.get("scope") != (
        "complete_typed_component_models_for_ref_001_through_ref_010"
    ):
        errors.append("identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if (
        contract.get("source_qualification"), contract.get("migration"),
        contract.get("policy"), contract.get("report"),
    ) != (QUALIFICATION, MIGRATION, POLICY, REPORT):
        errors.append("document_paths")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capability_mapping")
    if contract.get("model") != "hwpx-agent.field-engine/v1":
        errors.append("model")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("state_binding") != STATE_BINDING:
        errors.append("state_binding")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    expected_boundary = {**CLAIMS, "focused_rust_tests": "9/9 PASS", "direct_stage": "unit_passed"}
    if contract.get("evidence_boundary") != expected_boundary:
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_01": "typed_component_pass_direct_hwpx_and_target_evidence_not_run",
        "p09_01_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")

    source_count = validate_locks(root, contract.get("source_locks"), SOURCE_SHA256, errors, "source")
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_locks(
    root: Path,
    value: Any,
    expected: dict[str, str],
    errors: list[str],
    prefix: str,
) -> int:
    if not isinstance(value, list):
        errors.append(f"{prefix}_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append(f"{prefix}_lock_shape")
            continue
        relative, digest = item.get("path"), item.get("sha256")
        if (
            not isinstance(relative, str) or relative in declared
            or not isinstance(digest, str) or not DIGEST.fullmatch(digest)
        ):
            errors.append(f"{prefix}_lock_identity")
            continue
        declared[relative] = digest
        try:
            if canonical_digest(file(root, relative)) != digest:
                errors.append(f"{prefix}_lock_digest")
        except (OSError, ValueError):
            errors.append(f"{prefix}_lock_path")
    if declared != expected:
        errors.append(f"{prefix}_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if canonical_digest(path) != expected:
                errors.append("implementation_digest")
            text = path.read_text(encoding="utf-8")
            if any(marker not in text for marker in MARKERS[relative]):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(IMPLEMENTATION_SHA256)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "task", "base_commit", "scope", "source_sha256",
        "implementation_sha256", "tests", "claims",
    }:
        errors.append("qualification_shape")
    if value.get("schema_version") != "hwpx-agent.p09-field-core-source-qualification/v1":
        errors.append("qualification_schema")
    if value.get("task") != "P09-01" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    if value.get("scope") != "ten_ref_001_through_ref_010_typed_field_component_models_only":
        errors.append("qualification_scope")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "public_field_engine": "8/8 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "9/9 PASS",
        "test_kind": "typed_component_state",
        "network_used": False,
        "licensed_application_used": False,
    }:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "no migration switch"),
        POLICY: ("ten_capabilities_unit_passed=true", "direct_hwpx=false", "Reasoning level: `max`"),
        REPORT: ("total 9/9 PASS", "field_readback=false", "product_complete=false"),
    }
    for relative, markers in expected.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-field-core-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P09-01",
        "capabilities": 10,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_01_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    result_value = validate()
    print(json.dumps(result_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if result_value["state"] == "pass" else 1)
