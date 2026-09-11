#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-basic-shape-v1.json"
MIGRATION = "protocol/migrations/p08-basic-shape-v0-to-v1.md"
POLICY = "implementation/p08/P08-04_BASIC_SHAPE_POLICY.md"
REPORT = "implementation/p08/P08-04_BASIC_SHAPE_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-04-basic-shape-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "implementation/p08/P08-03_OBJECT_GEOMETRY_POLICY.md",
    "implementation/p08/P08-03_OBJECT_GEOMETRY_REPORT.md",
    "protocol/private/p08-object-geometry-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "2fa923b282022ede228749723eb65a9e5e427396741e1d720e94f14cb9ba125e",
    "crates/domain-ir/src/basic_shape.rs": "59414d6a3b20f105239e2b497d370e00385254a6775e0b9c37141ff36de65288",
    "crates/domain-ir/tests/basic_shape.rs": "40a582bcbae8939a46ce1cc661aaa46174e04bec814ced94b1aebb8775ec55a1",
    "crates/hwpx-package/src/lib.rs": "7041f5a9443ec4a473112b2ff3b22fa474bbfe0efe78f2b59a1bd6ac3090bc90",
    "crates/hwpx-package/src/id_index.rs": "5ec151bb7ea37af66a67608f01ab3676eac9a0b23e2d8c3870aa97c1b53adbb0",
    "crates/hwpx-package/src/basic_shape_hwpx.rs": "fda813b813cb569b8ab23e6cc8297729e93a853de32337448a962b424a60417b",
    "crates/hwpx-package/tests/basic_shape_hwpx.rs": "f68b7533e57288b8d7d7da22a0bf847de412488aa072627ceb6d5f9e5841da3f",
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod basic_shape;", "BasicShapeBuilder"),
    "crates/domain-ir/src/basic_shape.rs": (
        'BASIC_SHAPE_SCHEMA_VERSION: &str = "hwpx-agent.basic-shape/v1"',
        "pub enum BasicShape",
        "pub struct BasicShapeRequestDraft",
        "pub struct BasicShapeBuilder",
        "validate_for_geometry",
        "reject_duplicate_json_keys",
        "finish_non_exhaustive",
    ),
    "crates/domain-ir/tests/basic_shape.rs": (
        "plans_and_builds_all_five_semantic_shape_families",
        "kind_flow_and_native_identity_drift_fail_closed",
        "invalid_rectangle_ellipse_polygon_curve_and_text_fail_closed",
        "strict_json_rejects_duplicate_unknown_and_oversized_input",
    ),
    "crates/hwpx-package/src/lib.rs": ("mod basic_shape_hwpx;", "BasicShapeHwpxLowerer"),
    "crates/hwpx-package/src/id_index.rs": (
        "Hwpml2011ShapeV6",
        "hwpml-2011-shape-static/v6",
        "SHAPE_DECLARATION_RULES",
    ),
    "crates/hwpx-package/src/basic_shape_hwpx.rs": (
        'BASIC_SHAPE_HWPX_PROFILE_ID: &str',
        "pub struct BasicShapeHwpxBuilder",
        "pub struct BasicShapeHwpxReader",
        "pub struct BasicShapeHwpxLowerer",
        "IdRuleProfile::hwpml_2011_shape_v6()",
        "validate_collisions",
        "restored != bound.bytes",
        "finish_non_exhaustive",
    ),
    "crates/hwpx-package/tests/basic_shape_hwpx.rs": (
        "every_basic_shape_family_lowers_and_full_package_reopens",
        "textbox_escaped_payload_and_debug_are_exact_and_redacted",
        "object_instance_paragraph_and_sublist_collisions_fail_closed",
        "plan_rechecks_exact_source_and_document_flow",
    ),
}
OFFICIAL = {
    "repository": "https://github.com/hancom-io/owpml-model",
    "commit": "1453388472c703a4b299a0834f425cdac16644b9",
    "scope": "static_basic_shape_drawing_text_vocabulary_and_types_not_runtime_oracle",
}
ADMITTED = {
    "capabilities": ["obj.shape_insert", "obj.textbox_insert"],
    "shape_families": ["line", "rectangle", "ellipse", "text_box", "freeform"],
    "serialized_forms": ["line", "rect", "ellipse", "rect_draw_text", "polygon", "curve"],
    "geometry": "complete_p08_03_common_geometry_state",
    "shape_payload": "complete_reviewed_static_shape_specific_state",
    "text_box": "complete_draw_text_margin_sublist_paragraph_run_text_state",
    "binding": "domain_state_and_flow_then_exact_package_anchor_and_all_native_id_sets_at_plan_and_build",
    "preservation": "one_inserted_run_level_object_with_byte_exact_source_restoration_and_strict_readback",
}
WORKFLOW = {
    "admit": "validate_complete_geometry_shape_topology_text_ids_and_before_after_document_flow",
    "inspect": "bind_package_section_paragraph_empty_run_and_package_wide_object_instance_paragraph_sublist_id_sets",
    "plan": "rebuild_domain_result_and bind_exact_source_and_domain_plan_digests",
    "lower": "reinspect_every_binding_insert_one_native_static_shape_and_add_no_resource",
    "verify": "strict_common_and_specific_readback_count_deltas_byte_restoration_and_synthetic_package_reopen",
}
LIMITS = {
    "json_input_bytes": 524_288,
    "json_serialized_bytes": 524_288,
    "points": 16_384,
    "segments": 16_384,
    "text_bytes": 262_144,
    "name_bytes": 4_096,
    "coordinate_magnitude_hwpunit": 1_000_000_000,
    "section_bytes": 33_554_432,
    "elements": 1_000_000,
    "objects": 65_536,
    "fragment_bytes": 4_194_304,
}
FAILURE_POLICY = [
    "zero_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "geometry_kind_and_distinct_nonzero_native_identity_required",
    "line_endpoints_rectangle_area_ellipse_axes_polygon_area_and_curve_segments_validated",
    "textbox_xml_text_name_sublist_paragraph_and_reference_state_validated",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "package_section_paragraph_run_and_all_native_id_set_drift_rejected_at_final_build",
    "package_wide_object_instance_paragraph_and_sublist_collisions_rejected",
    "only_one_exact_empty_run_anchor_is_admitted",
    "native_namespaces_attribute_sets_child_order_boolean_integer_and_enum_lexemes_are_exact",
    "full_common_geometry_and_shape_payload_readback_must_equal_plan",
    "inserted_span_removal_must_reconstruct_exact_source_section",
    "no_relationship_resource_or_second_part_may_be_added_or_changed",
    "request_native_identity_path_digest_text_name_and_payload_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "appearance_line_fill_shadow": False,
    "grouped_or_nested_shapes": False,
    "connector_arc_container_ole_video_textart": False,
    "actual_target_hwpx": False,
    "exact_current_2020_serialization": False,
    "actual_hangul": False,
    "save_reopen": False,
    "render": False,
    "direct_automation_differential": False,
    "p08_04_complete": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "static_shape": "pass",
    "synthetic_full_package_reopen": "pass",
    "actual_target_hwpx": "not_run",
    "actual_hangul": False,
    "render": False,
    "p08_04": "static_shape_component_pass_target_not_run_task_incomplete",
    "p08_04_complete": False,
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
        "schema_version": "hwpx-agent.basic-shape-contract/v1",
        "state_schema_version": "hwpx-agent.basic-shape/v1",
        "profile_id": "hwpx-agent.basic-shape-hwpx.hwpml-2011-static/v1",
        "task": "P08-04",
        "scope": "bounded_complete_basic_shape_and_textbox_state_with_exact_package_anchor_id_sets_and_flow_bound_preserving_lowering",
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
    if set(value) != {
        "schema_version", "task", "recorded_date", "profile_id", "official_sources",
        "implementation_sources", "component_execution", "target_execution", "claims",
    }:
        errors.append("qualification_keys")
    if (
        value.get("schema_version") != "hwpx-agent.basic-shape-source-qualification/v1"
        or value.get("task") != "P08-04"
        or value.get("recorded_date") != "2026-09-12"
        or value.get("profile_id") != "hwpx-agent.basic-shape-hwpx.hwpml-2011-static/v1"
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
    if value.get("component_execution") != {
        "state": "pass", "rust_tests_passed": 13, "domain_tests_passed": 6,
        "hwpx_package_tests_passed": 7,
        "five_shape_families_and_six_serialized_forms": "pass",
        "complete_common_geometry_and_shape_payload": "pass",
        "request_and_build_state_flow_binding": "pass",
        "package_anchor_and_all_native_id_set_binding": "pass",
        "one_spine_part_preserving_lowering": "pass",
        "strict_shape_and_common_geometry_readback": "pass",
        "byte_exact_source_restoration": "pass", "synthetic_full_package_reopen": "pass",
        "tamper_drift_collision_and_malformed_rejection": "pass",
        "bounded_json_and_redacted_debug": "pass",
    }:
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run", "actual_target_hwpx": None, "hangul_open": None,
        "save_reopen": None, "render": None, "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "static_shape_component_pass": True, "shape_insert_and_textbox_insert": True,
        "synthetic_full_package_reopen": True, "actual_target_hwpx": False,
        "exact_current_2020_serialization": False, "actual_hangul": False,
        "save_reopen": False, "render": False, "p08_04_complete": False,
        "p08_complete": False, "production_ready": False, "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no stored v0", "MUST NOT be", "no defaultable fields"),
        POLICY: (
            "static_shape_component_pass / target_not_run / task_incomplete",
            "synthetic_full_package_reopen=true",
            "p08_04_complete=false",
        ),
        REPORT: ("13/13 PASS", "none was created, opened, edited, saved or", "P08-05"),
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
        "schema_version": "hwpx-agent.p08-basic-shape-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-04",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "static_shape": "pass" if not unique else "not_proven",
        "synthetic_full_package_reopen": "pass" if not unique else "not_proven",
        "actual_target_hwpx": "not_run",
        "actual_hangul": False,
        "render": False,
        "p08_04_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_BASIC_SHAPE_CONTRACT_PASS "
        f"source_locks={value['source_locks']} implementation_files={value['implementation_files']} "
        "synthetic_full_package_reopen=pass actual_target_hwpx=not_run p08_04_complete=false"
    )
