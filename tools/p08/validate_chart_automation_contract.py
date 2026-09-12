#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-chart-automation-v1.json"
MIGRATION = "protocol/migrations/p08-chart-automation-v0-to-v1.md"
POLICY = "implementation/p08/P08-07_CHART_AUTOMATION_POLICY.md"
REPORT = "implementation/p08/P08-07_CHART_AUTOMATION_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-07-chart-automation-source-qualification.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/08_drawing_image_chart.md",
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "implementation/p08/P08-06_OBJECT_COMPOSITION_POLICY.md",
    "implementation/p08/P08-06_OBJECT_COMPOSITION_REPORT.md",
    "protocol/private/p08-object-composition-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "18d9b107659324f82ea3f232ca36eca82048ebd6705ea7d66df3b13369c3b653",
    "crates/domain-ir/src/chart_automation.rs": "e97cfeef233681b6c61ea1e94ab6b934de0393b8abcd1fbb0826e39f33525ee6",
    "crates/domain-ir/tests/chart_automation.rs": "62d4818fad158027e614bdbfd41741a604feb04da31ed8bdf37f493d11865fdb",
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod chart_automation;", "ChartAutomationBuilder"),
    "crates/domain-ir/src/chart_automation.rs": (
        'CHART_AUTOMATION_SCHEMA_VERSION: &str = "hwpx-agent.chart-automation/v1"',
        "pub struct ChartAutomationProfile",
        "pub struct ChartDocumentState",
        "pub enum ChartOperation",
        'Self::Insert { .. } => "obj.chart_insert"',
        'Self::SetType { .. } => "obj.chart_type"',
        'Self::ReplaceData { .. } => "obj.chart_data"',
        'Self::UpdateSeries { .. } => "obj.chart_series"',
        'Self::UpdateAxis { .. } => "obj.chart_axis"',
        'Self::SetLegend { .. } => "obj.chart_legend"',
        'Self::SetLabels { .. } => "obj.chart_labels"',
        'Self::SetTitle { .. } => "obj.chart_title"',
        'Self::SetStyle { .. } => "obj.chart_style"',
        "pub struct ChartAutomationObservationDraft",
        "sealed_plan_intact",
        "private_plan_tampering_is_rejected_by_the_seal",
        "reject_duplicate_json_keys",
        "<redacted>",
    ),
    "crates/domain-ir/tests/chart_automation.rs": (
        "profile_requires_exact_nine_capabilities_and_canonical_target_mappings",
        "complete_grid_labels_series_axes_and_opaque_state_are_bound",
        "insertion_requires_exact_fresh_identity_and_allocator_inventory_transition",
        "every_edit_capability_changes_only_its_complete_chart_component",
        "invalid_series_axis_and_presentation_states_fail_closed",
        "strict_json_rejects_duplicate_unknown_and_bounded_input",
        "request_plan_and_build_recheck_profile_state_flow_and_noop",
        "execution_observation_requires_one_complete_exact_readback_and_nonempty_export",
        "debug_redacts_target_identity_content_and_digest_material",
    ),
}
CAPABILITIES = [
    "obj.chart_axis", "obj.chart_data", "obj.chart_insert", "obj.chart_labels",
    "obj.chart_legend", "obj.chart_series", "obj.chart_style", "obj.chart_title",
    "obj.chart_type",
]
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_non_nfc_or_oversized_json_rejected",
    "target_profile_requires_exact_nine_sorted_capabilities_and_unique_opaque_bindings",
    "raw_action_names_and_unchecked_parameter_bags_are_not_public_contract_fields",
    "chart_logical_native_instance_data_resource_and_chart_part_identity_must_be_distinct",
    "insert_requires_fresh_identity_before_after_inventory_and_allocator_proof_binding",
    "data_grid_dimensions_labels_orientation_values_and_provenance_must_be_complete",
    "series_order_labels_axis_stack_line_marker_visibility_exclusion_and_style_must_be_complete",
    "category_and_primary_value_axes_are_mandatory_and_secondary_series_requires_secondary_axis",
    "legend_labels_title_type_style_geometry_composition_appearance_and_opaque_state_must_be_complete",
    "unsupported_target_type_or_style_and_every_noop_rejected",
    "profile_source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "target_state_binding_schema_and_private_plan_tampering_rejected_by_exact_recomputation",
    "execution_observation_requires_exactly_one_complete_open_save_reopen_readback_export_attempt",
    "synthetic_observation_never_proves_installed_target_provenance",
    "identity_text_values_bindings_and_digests_redacted_from_debug",
    "no_partial_result_or_fallback_after_failure",
]
NOT_CLAIMED = {
    "actual_target_profile": False,
    "direct_hwpx": False,
    "resource_integrity": False,
    "semantic_reopen": False,
    "actual_hangul": False,
    "save_reopen": False,
    "full_property_readback": False,
    "export": False,
    "render_diff": False,
    "direct_automation_differential": False,
    "p08_07_complete": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}
GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "exact_chart_state": "pass",
    "automation_contract": "pass",
    "actual_target_profile": "not_run",
    "actual_hangul": False,
    "render_diff": False,
    "p08_07": "exact_chart_automation_component_pass_installed_target_not_run_task_incomplete",
    "p08_07_complete": False,
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
    if contract.get("schema_version") != "hwpx-agent.chart-automation-contract/v1":
        errors.append("schema_version")
    if contract.get("state_schema_version") != "hwpx-agent.chart-automation/v1":
        errors.append("state_schema_version")
    if contract.get("profile_id") != "hwpx-agent.chart-automation.target-bound/v1":
        errors.append("profile_id")
    if contract.get("task") != "P08-07":
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
    official = contract.get("official_sources")
    if (
        not isinstance(official, dict)
        or official.get("owpml_commit") != "1453388472c703a4b299a0834f425cdac16644b9"
        or official.get("scope")
        != "static_chart_vocabulary_and_opaque_reference_architecture_not_runtime_or_render_oracle"
        or not isinstance(official.get("hancom_help"), list)
        or len(official["hancom_help"]) != 7
    ):
        errors.append("official_sources")
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
        value.get("schema_version") != "hwpx-agent.chart-automation-source-qualification/v1"
        or value.get("task") != "P08-07"
        or value.get("recorded_date") != "2026-09-12"
        or value.get("profile_id") != "hwpx-agent.chart-automation.target-bound/v1"
    ):
        errors.append("qualification_identity")
    if value.get("implementation_sources") != IMPLEMENTATION_SHA256:
        errors.append("qualification_sources")
    official = value.get("official_sources")
    if (
        not isinstance(official, dict)
        or official.get("hancom_owpml_commit") != "1453388472c703a4b299a0834f425cdac16644b9"
        or official.get("evidence_scope") != "static_vocabulary_and_architecture_only"
    ):
        errors.append("qualification_official")
    component = value.get("component_execution")
    if (
        not isinstance(component, dict)
        or component.get("state") != "pass"
        or component.get("rust_tests_passed") != 10
        or component.get("nine_capability_rows_modelled") != "pass"
    ):
        errors.append("qualification_component")
    if value.get("target_execution") != {
        "state": "not_run", "actual_target_profile": None, "direct_hwpx": None,
        "resource_integrity": None, "semantic_reopen": None, "actual_target_hwpx": None,
        "hangul_open": None, "save_reopen": None, "full_property_readback": None,
        "export": None, "render_diff": None, "direct_automation_differential": None,
    }:
        errors.append("qualification_target")
    if value.get("claims") != {
        "exact_chart_state_component_pass": True,
        "all_nine_chart_rows_modelled": True,
        "automation_plan_and_observation_contract": True,
        **NOT_CLAIMED,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no stored v0", "MUST NOT be", "no defaultable"),
        POLICY: (
            "exact_chart_automation_component_pass / installed_target_not_run / task_incomplete",
            "exactly these sorted capability mappings",
            "p08_07_complete=false",
        ),
        REPORT: ("10/10 PASS", "No chart HWPX part", "P08-08"),
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
        "schema_version": "hwpx-agent.p08-chart-automation-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P08-07",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "exact_chart_state": "pass" if not unique else "not_proven",
        "automation_contract": "pass" if not unique else "not_proven",
        "actual_target_profile": "not_run",
        "actual_hangul": False,
        "render_diff": False,
        "p08_07_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(
        "P08_CHART_AUTOMATION_CONTRACT_PASS "
        f"source_locks={value['source_locks']} implementation_files={value['implementation_files']} "
        "exact_chart_state=pass automation_contract=pass actual_target_profile=not_run "
        "render_diff=false p08_07_complete=false"
    )
