#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-composition-v1.json"
MIGRATION = "protocol/migrations/p08-object-composition-v0-to-v1.md"
POLICY = "implementation/p08/P08-06_OBJECT_COMPOSITION_POLICY.md"
REPORT = "implementation/p08/P08-06_OBJECT_COMPOSITION_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-06-object-composition-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "implementation/p08/P08-05_OBJECT_APPEARANCE_POLICY.md",
    "implementation/p08/P08-05_OBJECT_APPEARANCE_REPORT.md",
    "protocol/private/p08-object-appearance-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b13dcc56b5938d524084179b6c31e1c51bbc0fbd716146f47fcb89fa73cdb8d0",
    "crates/domain-ir/src/object_composition.rs": "d3389af14835039ca9c39dc65f453906704ae456d67720772db810b2f8ca8045",
    "crates/domain-ir/tests/object_composition.rs": "5ed744a6bc3c330765aa18d6fcddf1a99d5773b909a64f4d1c1c1e67db5322ab",
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod object_composition;", "ObjectCompositionBuilder"),
    "crates/domain-ir/src/object_composition.rs": (
        'OBJECT_COMPOSITION_SCHEMA_VERSION: &str = "hwpx-agent.object-composition/v1"',
        "pub enum ObjectCompositionOperation",
        "fn apply_group",
        "fn apply_ungroup",
        "fn apply_z_order",
        "fn apply_align",
        "fn apply_distribute",
        "fn apply_create_connector",
        "fn apply_update_connector",
        "validate_connector",
        "reject_duplicate_json_keys",
        "private_plan_tampering_is_rejected",
        "finish_non_exhaustive",
    ),
    "crates/domain-ir/tests/object_composition.rs": (
        "group_and_ungroup_round_trip_members_identity_content_geometry_and_order",
        "every_z_order_move_is_exact_and_keeps_non_order_state",
        "six_alignment_modes_are_deterministic_and_preserve_content",
        "horizontal_and_vertical_distribution_use_balanced_integer_gaps",
        "connector_create_update_and_closed_group_preserve_exact_subject_edges",
        "invalid_topology_selection_and_cross_parent_edges_fail_closed",
        "graph_json_coordinate_and_collection_boundaries_are_fail_closed",
    ),
}
OFFICIAL = {
    "repository": "https://github.com/hancom-io/owpml-model",
    "commit": "1453388472c703a4b299a0834f425cdac16644b9",
    "scope": "static_composition_vocabulary_and_types_not_runtime_or_render_oracle",
}
CAPABILITIES = [
    "obj.group", "obj.ungroup", "obj.z_order", "obj.align", "obj.distribute", "obj.connector",
]
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "duplicate_zero_or_colliding_logical_native_and_instance_identity_rejected",
    "dangling_cyclic_excess_depth_or_non_group_parent_rejected",
    "sibling_z_order_must_be_unique_contiguous_and_zero_based",
    "group_requires_two_children_and_exact_direct_child_union_bounds",
    "group_selection_must_be_distinct_existing_siblings_with_fresh_group_identity",
    "ungroup_splices_children_into_exact_group_slot_and_rejects_dangling_edges",
    "z_order_edge_noop_rejected",
    "align_and_distribute_require_distinct_movable_siblings",
    "distribution_keeps_first_last_and_balances_integer_remainder_deterministically",
    "connector_bounds_are_derived_from_all_points",
    "attached_connector_subject_must_exist_be_nonconnector_share_parent_and_contain_endpoint",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "target_state_and_plan_tampering_rejected_by_exact_recomputation",
    "identity_content_resource_coordinates_and_digests_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "direct_hwpx": False,
    "resource_integrity": False,
    "semantic_reopen": False,
    "actual_target_hwpx": False,
    "actual_hangul": False,
    "save_reopen": False,
    "object_bounds": False,
    "render_diff": False,
    "direct_automation_differential": False,
    "p08_06_complete": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "pure_object_graph": "pass",
    "graph_invariant_tests": "pass",
    "direct_hwpx": "not_run",
    "actual_hangul": False,
    "render_diff": False,
    "p08_06": "pure_object_graph_component_pass_direct_hwpx_not_run_task_incomplete",
    "p08_06_complete": False,
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
    if contract.get("schema_version") != "hwpx-agent.object-composition-contract/v1":
        errors.append("schema_version")
    if contract.get("state_schema_version") != "hwpx-agent.object-composition/v1":
        errors.append("state_schema_version")
    if contract.get("profile_id") != "hwpx-agent.object-composition.pure-graph/v1":
        errors.append("profile_id")
    if contract.get("task") != "P08-06":
        errors.append("task")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_canonicalization")
    if contract.get("source_qualification") != QUALIFICATION:
        errors.append("source_qualification")
    if (contract.get("migration"), contract.get("policy"), contract.get("report")) != (
        MIGRATION, POLICY, REPORT,
    ):
        errors.append("document_paths")
    if contract.get("implementation_files") != list(MARKERS):
        errors.append("implementation_files")
    if contract.get("official_model_source") != OFFICIAL:
        errors.append("official_model_source")
    admitted = contract.get("admitted_profile")
    if not isinstance(admitted, dict) or admitted.get("capabilities") != CAPABILITIES:
        errors.append("admitted_capabilities")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    if contract.get("not_claimed") != NOT_CLAIMED:
        errors.append("not_claimed")
    if contract.get("gate_decision") != GATE:
        errors.append("gate_decision")
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
        value.get("schema_version") != "hwpx-agent.object-composition-source-qualification/v1"
        or value.get("task") != "P08-06"
        or value.get("recorded_date") != "2026-09-12"
        or value.get("profile_id") != "hwpx-agent.object-composition.pure-graph/v1"
    ):
        errors.append("qualification_identity")
    if value.get("implementation_sources") != IMPLEMENTATION_SHA256:
        errors.append("qualification_sources")
    official = value.get("official_sources")
    if (
        not isinstance(official, dict)
        or official.get("hancom_owpml_commit") != OFFICIAL["commit"]
        or official.get("evidence_scope") != "static_vocabulary_and_field_types_only"
    ):
        errors.append("qualification_official")
    component = value.get("component_execution")
    if (
        not isinstance(component, dict)
        or component.get("state") != "pass"
        or component.get("rust_tests_passed") != 10
        or component.get("six_capability_rows_modelled") != "pass"
    ):
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run", "direct_hwpx": None, "resource_integrity": None,
        "semantic_reopen": None, "actual_target_hwpx": None, "hangul_open": None,
        "save_reopen": None, "object_bounds": None, "render_diff": None,
        "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "pure_object_graph_component_pass": True,
        "graph_invariant_tests": True,
        "complete_noncomposition_state_binding": True,
        **NOT_CLAIMED,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "no defaultable"),
        POLICY: (
            "pure_object_graph_component_pass / successor_static_hwpx_integration_pass",
            "Half-HWPUNIT centers",
            "p08_06_complete=false",
        ),
        REPORT: ("10/10 PASS", "P08-11", "No full-package output"),
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
        "schema_version": "hwpx-agent.p08-object-composition-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-06",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "pure_object_graph": "pass" if not unique else "not_proven",
        "graph_invariant_tests": "pass" if not unique else "not_proven",
        "direct_hwpx": "not_run",
        "actual_hangul": False,
        "render_diff": False,
        "p08_06_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_OBJECT_COMPOSITION_CONTRACT_PASS "
        f"source_locks={value['source_locks']} implementation_files={value['implementation_files']} "
        "graph_invariant_tests=pass direct_hwpx=not_run render_diff=false p08_06_complete=false"
    )
