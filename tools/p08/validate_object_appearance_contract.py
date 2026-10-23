#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-appearance-v1.json"
MIGRATION = "protocol/migrations/p08-object-appearance-v0-to-v1.md"
POLICY = "implementation/p08/P08-05_OBJECT_APPEARANCE_POLICY.md"
REPORT = "implementation/p08/P08-05_OBJECT_APPEARANCE_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-05-object-appearance-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "implementation/p08/P08-04_BASIC_SHAPE_POLICY.md",
    "implementation/p08/P08-04_BASIC_SHAPE_REPORT.md",
    "protocol/private/p08-basic-shape-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/object_appearance.rs": "f8809b3587a901e1be40cc8e09d06d780c6ffd0189f01c6c52d675290abd5a81",
    "crates/domain-ir/tests/object_appearance.rs": "7ba9f137a76d952ededf3228cc9b76c6e4fdf98783f12546d7ded9debed9da81",
    "crates/hwpx-package/src/lib.rs": "a22f9f73f04e17ac3439022fcf6aaa0fb5f5ddb02d48257d10998bd01bdf2e12",
    "crates/hwpx-package/src/object_appearance_hwpx.rs": "cd19aae862cc95968e6f02ebe1ebc195f57bba44a82e0c09ac2b910aefce53c3",
    "crates/hwpx-package/tests/object_appearance_hwpx.rs": "b0fa7b333869963a48f0ded42c8a3b71ad0a5c4b83945669fa4a750300580c4e",
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod object_appearance;", "ObjectAppearanceBuilder"),
    "crates/domain-ir/src/object_appearance.rs": (
        'OBJECT_APPEARANCE_SCHEMA_VERSION: &str = "hwpx-agent.object-appearance/v1"',
        "pub enum FillAppearance",
        "pub struct PictureEffects",
        "pub enum AppearanceOperation",
        "pub struct ObjectAppearanceBuilder",
        "validate_operation_delta",
        "reject_duplicate_json_keys",
        "finish_non_exhaustive",
    ),
    "crates/domain-ir/tests/object_appearance.rs": (
        "plans_and_builds_line_solid_pattern_gradient_image_and_shape_shadow",
        "plans_and_builds_all_picture_effect_and_adjustment_operations",
        "transparency_requires_an_exact_single_alpha_delta",
        "strict_json_rejects_duplicate_unknown_and_flow_drift",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "mod object_appearance_hwpx;",
        "ObjectAppearanceHwpxLowerer",
    ),
    "crates/hwpx-package/src/object_appearance_hwpx.rs": (
        'OBJECT_APPEARANCE_HWPX_PROFILE_ID: &str',
        "pub struct ObjectAppearanceHwpxBuilder",
        "pub struct ObjectAppearanceHwpxReader",
        "pub struct ObjectAppearanceHwpxLowerer",
        "rewrite_appearance",
        "verify_outside_object_preserved",
        "tampered_private_plan_binding_is_rejected",
        "finish_non_exhaustive",
    ),
    "crates/hwpx-package/tests/object_appearance_hwpx.rs": (
        "lowers_every_shape_appearance_family_with_strict_readback",
        "lowers_all_picture_effects_line_and_color_adjustment",
        "lowers_transparency_from_an_existing_line_and_preserves_other_bytes",
        "rejects_duplicate_appearance_unknown_attributes_and_unsupported_effect_color",
    ),
}
OFFICIAL = {
    "repository": "https://github.com/hancom-io/owpml-model",
    "commit": "1453388472c703a4b299a0834f425cdac16644b9",
    "scope": "static_appearance_vocabulary_and_types_not_runtime_or_render_oracle",
}
CAPABILITIES = [
    "obj.line_style", "obj.fill_solid", "obj.fill_gradient", "obj.fill_pattern",
    "obj.fill_image", "obj.shadow", "obj.reflection", "obj.glow", "obj.soft_edge",
    "obj.transparency", "obj.color_adjust",
]
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "cross_family_shape_and_picture_state_rejected",
    "nonzero_native_identity_and_complete_source_target_state_required",
    "only_one_exact_operation_component_or_alpha_channel_may_change",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "section_object_identity_family_and_domain_plan_drift_rejected_at_final_build",
    "duplicate_unknown_unmodelled_or_noncanonical_native_appearance_rejected",
    "only_direct_run_basic_shapes_and_pictures_are_admitted",
    "strict_complete_appearance_readback_must_equal_target",
    "original_object_replacement_must_reconstruct_exact_source_section",
    "scheme_system_preset_effect_colors_rejected_instead_of_guessed",
    "image_fill_relationship_id_is_lexical_only_and_not_promoted_to_package_resource_integrity",
    "request_native_identity_relationship_id_values_and_digests_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "package_image_fill_resource_integrity": False,
    "grouped_or_nested_objects": False,
    "scheme_system_preset_effect_colors": False,
    "actual_target_hwpx": False,
    "exact_current_2020_serialization": False,
    "actual_hangul": False,
    "save_reopen": False,
    "visual_diff": False,
    "render": False,
    "direct_automation_differential": False,
    "p08_05_complete": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "static_appearance": "pass",
    "synthetic_section_roundtrip": "pass",
    "actual_target_hwpx": "not_run",
    "actual_hangul": False,
    "visual_diff": False,
    "render": False,
    "p08_05": "static_appearance_component_pass_visual_target_not_run_task_incomplete",
    "p08_05_complete": False,
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
    if contract.get("schema_version") != "hwpx-agent.object-appearance-contract/v1":
        errors.append("schema_version")
    if contract.get("state_schema_version") != "hwpx-agent.object-appearance/v1":
        errors.append("state_schema_version")
    if contract.get("profile_id") != "hwpx-agent.object-appearance-hwpx.hwpml-2011-static/v1":
        errors.append("profile_id")
    if contract.get("task") != "P08-05":
        errors.append("task")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_canonicalization")
    if contract.get("source_qualification") != QUALIFICATION:
        errors.append("source_qualification")
    if contract.get("migration") != MIGRATION or contract.get("policy") != POLICY or contract.get("report") != REPORT:
        errors.append("document_paths")
    if contract.get("implementation_files") != list(MARKERS):
        errors.append("implementation_files")
    if contract.get("official_model_source") != OFFICIAL:
        errors.append("official_model_source")
    admitted = contract.get("admitted_profile")
    if not isinstance(admitted, dict) or admitted.get("capabilities") != CAPABILITIES:
        errors.append("admitted_capabilities")
    if contract.get("not_claimed") != NOT_CLAIMED:
        errors.append("not_claimed")
    if contract.get("gate_decision") != GATE:
        errors.append("gate_decision")
    failure = contract.get("failure_policy")
    if failure != FAILURE_POLICY:
        errors.append("failure_policy")
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
        if not isinstance(relative, str) or relative in declared or not isinstance(expected, str) or not DIGEST.fullmatch(expected):
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
    if value.get("schema_version") != "hwpx-agent.object-appearance-source-qualification/v1" or value.get("task") != "P08-05" or value.get("recorded_date") != "2026-09-12":
        errors.append("qualification_identity")
    if value.get("implementation_sources") != IMPLEMENTATION_SHA256:
        errors.append("qualification_sources")
    official = value.get("official_sources")
    if not isinstance(official, dict) or official.get("hancom_owpml_commit") != OFFICIAL["commit"] or official.get("evidence_scope") != "static_vocabulary_inheritance_and_type_model_only":
        errors.append("qualification_official")
    component = value.get("component_execution")
    if not isinstance(component, dict) or component.get("state") != "pass" or component.get("rust_tests_passed") != 13 or component.get("eleven_capability_rows_modelled") != "pass":
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run", "actual_target_hwpx": None, "hangul_open": None,
        "save_reopen": None, "visual_diff": None, "render": None,
        "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "static_appearance_component_pass": True,
        "synthetic_section_roundtrip": True,
        "package_image_fill_resource_integrity": False,
        "actual_target_hwpx": False,
        "exact_current_2020_serialization": False,
        "actual_hangul": False,
        "save_reopen": False,
        "visual_diff": False,
        "render": False,
        "p08_05_complete": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no stored v0", "MUST NOT be", "no defaultable request fields"),
        POLICY: (
            "static_appearance_component_pass / visual_target_not_run / task_incomplete",
            "package_image_fill_resource_integrity=false",
            "p08_05_complete=false",
        ),
        REPORT: ("13/13 PASS", "No current output was created", "P08-06"),
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
        "schema_version": "hwpx-agent.p08-object-appearance-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-05",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "static_appearance": "pass" if not unique else "not_proven",
        "synthetic_section_roundtrip": "pass" if not unique else "not_proven",
        "actual_target_hwpx": "not_run",
        "actual_hangul": False,
        "visual_diff": False,
        "render": False,
        "p08_05_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_OBJECT_APPEARANCE_CONTRACT_PASS "
        f"source_locks={value['source_locks']} implementation_files={value['implementation_files']} "
        "synthetic_section_roundtrip=pass actual_target_hwpx=not_run visual_diff=false "
        "p08_05_complete=false"
    )
