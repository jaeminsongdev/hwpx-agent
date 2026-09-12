#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-geometry-v1.json"
MIGRATION = "protocol/migrations/p08-object-geometry-v0-to-v1.md"
POLICY = "implementation/p08/P08-03_OBJECT_GEOMETRY_POLICY.md"
REPORT = "implementation/p08/P08-03_OBJECT_GEOMETRY_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-03-object-geometry-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "implementation/p08/P08-02_IMAGE_HWPX_POLICY.md",
    "implementation/p08/P08-02_IMAGE_HWPX_REPORT.md",
    "protocol/private/p08-image-hwpx-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b13dcc56b5938d524084179b6c31e1c51bbc0fbd716146f47fcb89fa73cdb8d0",
    "crates/domain-ir/src/object_geometry.rs": "b8d42a0fd02c6a831d1e675761556192b713c59d90fae59e95a367cf3a1b12e1",
    "crates/domain-ir/tests/object_geometry.rs": "5a88b76187bedf9939193de2db85dd105c6924d2946008c4a2d2fcbebf6f1f10",
    "crates/hwpx-package/src/lib.rs": "593bed705c2686f1da8e4143fb797fac63e3017437d5ac0ce36fdbf809906244",
    "crates/hwpx-package/src/object_geometry_hwpx.rs": "88bbd23bb63cd95e18fdc96c06d9c7029c6cae89ae5917233801036a57fc4a69",
    "crates/hwpx-package/tests/object_geometry_hwpx.rs": "9a72cd328b5923d36f7d8d73ce089a94463899ba4a9fbc5b0340ea4aa3d3980e",
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod object_geometry;", "ObjectGeometryBuilder"),
    "crates/domain-ir/src/object_geometry.rs": (
        'OBJECT_GEOMETRY_SCHEMA_VERSION: &str = "hwpx-agent.object-geometry/v1"',
        "pub struct ObjectGeometryStateDraft",
        "pub enum ObjectGeometryOperation",
        "pub struct ObjectGeometryRequestDraft",
        "pub struct ObjectGeometryBuilder",
        "SourceStateDrift",
        "DocumentFlowDrift",
        "PlanTampered",
        'Self::SetLocked { .. } => "obj.object_protect"',
        "NoOp",
        "reject_duplicate_json_keys",
        "finish_non_exhaustive",
    ),
    "crates/domain-ir/tests/object_geometry.rs": (
        "plans_and_builds_all_seven_exact_geometry_capabilities",
        "object_protect_rejects_noop_without_building_a_plan",
        "request_and_build_both_reject_state_and_flow_drift",
        "round_trips_all_admitted_object_kinds_and_preserves_complete_state",
    ),
    "crates/hwpx-package/src/lib.rs": ("mod object_geometry_hwpx;", "ObjectGeometryHwpxLowerer"),
    "crates/hwpx-package/src/object_geometry_hwpx.rs": (
        'OBJECT_GEOMETRY_HWPX_PROFILE_ID: &str',
        "pub struct ObjectGeometryHwpxReader",
        "pub struct ObjectGeometryHwpxBuilder",
        "pub struct ObjectGeometryHwpxLowerer",
        "source_section_sha256",
        "source_object_sha256",
        "fixed_millionths",
        "finish_non_exhaustive",
    ),
    "crates/hwpx-package/tests/object_geometry_hwpx.rs": (
        "reads_all_reviewed_run_level_common_component_kinds",
        "lowers_object_protect_for_all_common_kinds_with_one_exact_attribute_edit",
        "lowers_page_position_and_preserves_other_object_and_opaque_payload",
        "lowers_size_with_complete_component_and_exact_fixed_point_transform",
        "request_and_build_reject_section_object_state_and_flow_drift",
        "page_and_paragraph_anchor_fixtures_are_distinct_and_exact",
    ),
}
OFFICIAL = {
    "repository": "https://github.com/hancom-io/owpml-model",
    "commit": "1453388472c703a4b299a0834f425cdac16644b9",
    "scope": "static_common_shape_vocabulary_inheritance_and_types_not_runtime_oracle",
}
ADMITTED = {
    "object_selection": "one_existing_direct_run_child_by_bounded_document_order",
    "object_kinds": [
        "pic", "rect", "ellipse", "line", "arc", "polygon", "curve", "connectLine",
        "container", "ole", "video", "textart",
    ],
    "operations": ["obj.object_protect", "obj.position", "obj.size", "obj.anchor", "obj.wrap", "obj.rotate", "obj.flip"],
    "state": "complete_reviewed_common_object_and_component_geometry_fields",
    "matrix": "all_three_six_coefficient_matrices_as_signed_fixed_millionths",
    "binding": "canonical_state_and_flow_then_exact_section_and_object_sha256_at_request_and_build",
    "preservation": "changed_common_attribute_value_spans_only_with_semantic_readback",
}
WORKFLOW = {
    "inspect": "strictly_read_one_run_level_common_component_and_exact_section_object_digests",
    "admit": "bind_complete_state_operation_and_before_after_document_flow",
    "plan": "recheck_domain_state_flow_then_bind_section_object_and_domain_plan",
    "lower": "recheck_plan_section_object_state_flow_and_replace_changed_common_attribute_values",
    "verify": "strict_target_state_readback_noop_identity_and_opaque_sibling_byte_preservation",
}
LIMITS = {
    "json_input_bytes": 262_144,
    "json_serialized_bytes": 262_144,
    "extent_hwpunit": 100_000_000,
    "matrix_coefficient_millionths": 1_000_000_000_000,
    "section_bytes": 33_554_432,
    "elements": 1_000_000,
    "objects": 65_536,
    "output_bytes": 33_554_432,
    "matrix_text_bytes": 64,
}
FAILURE_POLICY = [
    "zero_negative_over_ceiling_or_inconsistent_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_state_and_request_json_rejected",
    "zero_native_identity_zero_extent_or_out_of_bound_transform_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "section_and_selected_object_byte_drift_rejected_at_final_build",
    "nested_only_unknown_missing_or_duplicate_common_component_structure_rejected",
    "noncanonical_boolean_integer_enum_and_more_than_six_decimal_matrix_rejected",
    "rotation_and_flip_require_complete_caller_supplied_target_transform",
    "object_identity_kind_zorder_and_numbering_cannot_change_and_lock_changes_only_for_obj_object_protect",
    "only_changed_common_attribute_value_spans_may_change",
    "semantic_target_readback_must_equal_planned_complete_state",
    "unchanged_lexemes_opaque_payload_siblings_text_namespaces_and_formatting_preserved",
    "identity_geometry_paths_and_digests_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "nested_group_member_addressing": False,
    "graph_or_chart_geometry": False,
    "aspect_lock_semantics": False,
    "full_package_hwpx": False,
    "exact_current_2020_serialization": False,
    "actual_hangul": False,
    "save_reopen": False,
    "render": False,
    "direct_automation_differential": False,
    "p08_03_complete": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "common_geometry": "pass",
    "full_package_hwpx": "not_run",
    "actual_hangul": False,
    "render": False,
    "p08_03": "common_component_pass_target_not_run_task_incomplete",
    "p08_03_complete": False,
    "p08": "in_progress",
    "product_complete": False,
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


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)
    exact = {
        "schema_version": "hwpx-agent.object-geometry-contract/v1",
        "state_schema_version": "hwpx-agent.object-geometry/v1",
        "profile_id": "hwpx-agent.object-geometry-hwpx.hwpml-2011-common-component/v1",
        "task": "P08-03",
        "scope": "bounded_complete_common_geometry_and_transform_state_with_exact_section_object_state_and_flow_bound_preserving_lowering",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": list(MARKERS),
        "official_model_source": OFFICIAL,
        "admitted_profile": ADMITTED,
        "workflow": WORKFLOW,
        "default_limits": LIMITS,
        "failure_policy": FAILURE_POLICY,
        "not_claimed": NOT_CLAIMED,
        "gate_decision": GATE,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {*exact, "source_locks"}:
        errors.append("contract_keys")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, expected = item.get("path"), item.get("sha256")
        if (
            not isinstance(relative, str)
            or relative in declared
            or not isinstance(expected, str)
            or not DIGEST.fullmatch(expected)
        ):
            errors.append("source_lock_identity")
            continue
        declared[relative] = expected
        try:
            if canonical_digest(file(root, relative)) != expected:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path")
    if set(declared) != SOURCES:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if raw_digest(path) != expected:
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
    expected_keys = {
        "schema_version", "task", "recorded_date", "profile_id", "official_sources",
        "implementation_sources", "component_execution", "target_execution", "claims",
    }
    if set(value) != expected_keys:
        errors.append("qualification_keys")
    if (
        value.get("schema_version") != "hwpx-agent.object-geometry-source-qualification/v1"
        or value.get("task") != "P08-03"
        or value.get("recorded_date") != "2026-09-12"
        or value.get("profile_id")
        != "hwpx-agent.object-geometry-hwpx.hwpml-2011-common-component/v1"
    ):
        errors.append("qualification_identity")
    if value.get("implementation_sources") != IMPLEMENTATION_SHA256:
        errors.append("qualification_sources")
    official = value.get("official_sources")
    if (
        not isinstance(official, dict)
        or official.get("evidence_scope") != "static_vocabulary_inheritance_and_type_model_only"
        or official.get("hancom_owpml_commit") != OFFICIAL["commit"]
    ):
        errors.append("qualification_official_sources")
    expected_component = {
        "state": "pass", "rust_tests_passed": 19, "domain_tests_passed": 7,
        "hwpx_section_tests_passed": 12, "seven_catalog_operations": "pass",
        "twelve_common_component_kinds": "pass", "complete_geometry_and_transform_state": "pass",
        "request_and_build_state_flow_binding": "pass", "section_and_object_byte_binding": "pass",
        "changed_attribute_only_lowering": "pass", "opaque_payload_and_sibling_preservation": "pass",
        "fixed_millionth_matrix_exactness": "pass", "tamper_drift_and_malformed_rejection": "pass",
        "bounded_json_and_redacted_debug": "pass",
    }
    if value.get("component_execution") != expected_component:
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run", "full_package_hwpx": None, "hangul_open": None,
        "save_reopen": None, "render": None, "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "common_component_pass": True, "seven_geometry_operations": True,
        "full_package_hwpx": False, "exact_current_2020_serialization": False,
        "actual_hangul": False, "save_reopen": False, "render": False,
        "p08_03_complete": False, "p08_complete": False, "production_ready": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "no defaultable fields"),
        POLICY: (
            "common_component_pass / target_not_run / task_incomplete",
            "all 18 coefficients",
            "p08_03_complete=false",
        ),
        REPORT: ("19/19 PASS", "synthetic section XML", "P08-14"),
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
        "schema_version": "hwpx-agent.p08-object-geometry-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-03",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "common_geometry": "pass" if not unique else "not_proven",
        "full_package_hwpx": "not_run",
        "actual_hangul": False,
        "render": False,
        "p08_03_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_OBJECT_GEOMETRY_CONTRACT_PASS "
        f"source_locks={value['source_locks']} implementation_files={value['implementation_files']} "
        "full_package_hwpx=not_run p08_03_complete=false"
    )
