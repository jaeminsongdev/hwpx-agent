#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.p06.validate_table_geometry_contract import (
    add_error,
    bounded_file,
    canonical_sha256,
    reject_duplicate_keys,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-chart-v1.json"
MIGRATION = "protocol/migrations/p06-table-chart-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_CHART_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_CHART_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-006", "capability_id": "table.chart_from_table"},
]
EXPECTED_REFERENCES = [
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/chart/chart(createchart).htm",
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 33_554_432,
    "cells": 1_000_000,
    "label_bytes": 1_048_576,
    "identifier_bytes": 256,
    "serialized_bytes": 134_217_728,
    "decimal_scale": 18,
}
EXPECTED_SEMANTICS = {
    "state": "complete_exact_grid_master_cell_typed_display_value_source_digest_and_value_origin_snapshot",
    "selection": "inclusive_rectangular_cell_block_at_least_two_by_two_with_cursor_only_default_data_creation_rejected",
    "roles": "top_left_ignored_first_row_series_labels_first_column_category_labels_numeric_or_blank_body",
    "chart": "three_dimensional_vertical_bar_created_from_exact_selected_cell_block_context",
    "formulas": "formula_display_cache_values_retain_formula_and_cache_sha256_origin_without_claiming_target_readback",
    "preservation": "source_state_grid_table_identity_and_document_flow_sha256_bound_with_no_source_mutation_or_partial_plan",
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "chart_xml_lowering": False,
    "package_mutation_or_preservation": False,
    "semantic_reopen_or_linkage": False,
    "formula_cache_readback": False,
    "page_split_or_render": False,
    "hancom_2020_target_build": False,
    "automation_or_differential": False,
    "merged_cell_chart_semantics": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "actual_hwpx": False,
    "actual_hangul": False,
    "p06_09": "in_progress",
    "product_complete": False,
}
EXPECTED_KEYS = {
    "schema_version",
    "model_schema_version",
    "scope",
    "features",
    "official_references",
    "source_lock_canonicalization",
    "source_locks",
    "migration",
    "policy",
    "report",
    "implementation_files",
    "semantics",
    "binding",
    "default_limits",
    "failure_policy",
    "not_claimed",
    "gate_decision",
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod table_chart;",
        "TableChartBuilder",
        "TableChartSourceState",
        "TableChartRequest",
        "TABLE_CHART_FROM_TABLE_CAPABILITY_ID",
    ),
    "crates/domain-ir/src/table_chart.rs": (
        'TABLE_CHART_SCHEMA_VERSION: &str = "hwpx-agent.table-chart/v1"',
        'TABLE_CHART_FROM_TABLE_CAPABILITY_ID: &str = "table.chart_from_table"',
        "pub struct TableChartSourceState",
        "pub struct TableChartRequest",
        "pub struct TableChartPlan",
        "pub struct TableChartBuilder",
        "ThreeDimensionalVerticalBar",
        "ExactSelectedCellBlock",
        "fn validate_region",
        "pub enum TableChartError",
    ),
    "crates/domain-ir/tests/table_chart.rs": (
        "linked_cell_block_projects_default_chart_roles_and_preserves_source",
        "subregion_is_exact_and_does_not_admit_cursor_only_creation",
        "text_in_numeric_body_fails_closed",
        "merged_cell_in_selected_block_fails_closed",
        "request_and_build_both_reject_state_or_flow_drift",
        "canonical_state_is_deterministic_and_json_is_strict",
        "finite_input_output_and_debug_redaction_are_enforced",
    ),
    POLICY: (
        "component_only / unit_passed",
        "Cursor-only creation is also rejected",
        "three-dimensional",
        "## Gate boundary",
        "Reasoning level: `max`",
    ),
    REPORT: (
        "Result: `component_pass`",
        "Focused Rust table-chart tests: 12/12 PASS.",
        "`cataloged`: 3 to 2",
        "`unit_passed`: 40 to 41",
        "Green rows: remains 0/61",
    ),
}


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = json.loads(
            bounded_file(root, CONTRACT, 256_000).read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
        if not isinstance(contract, dict):
            raise ValueError("contract root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0)

    if set(contract) != EXPECTED_KEYS:
        add_error(errors, "contract_keys")
    expected_scalars = {
        "schema_version": "hwpx-agent.table-chart-contract/v1",
        "model_schema_version": "hwpx-agent.table-chart/v1",
        "scope": "p06_09_pure_bounded_linked_table_cell_block_chart_current_pc_local_development",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    if contract.get("features") != EXPECTED_FEATURES:
        add_error(errors, "features")
    if contract.get("official_references") != EXPECTED_REFERENCES:
        add_error(errors, "official_references")
    if contract.get("default_limits") != EXPECTED_LIMITS:
        add_error(errors, "default_limits")
    if contract.get("semantics") != EXPECTED_SEMANTICS:
        add_error(errors, "semantics")
    if contract.get("not_claimed") != EXPECTED_NOT_CLAIMED:
        add_error(errors, "not_claimed")
    if contract.get("gate_decision") != EXPECTED_GATE:
        add_error(errors, "gate_decision")
    binding = contract.get("binding")
    if not isinstance(binding, dict) or set(binding) != {
        "identity",
        "source",
        "request",
        "plan",
        "serialization",
    }:
        add_error(errors, "binding")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 14
        or len(set(failure_policy)) != len(failure_policy)
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        add_error(errors, "failure_policy")
    implementation_files = contract.get("implementation_files")
    if implementation_files != list(IMPLEMENTATION_MARKERS):
        add_error(errors, "implementation_files")

    source_count = validate_source_locks(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    validate_migration(root, errors)
    return result(errors, source_count, implementation_count)


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        add_error(errors, "source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            add_error(errors, "source_lock_shape")
            continue
        path = item.get("path")
        digest = item.get("sha256")
        if (
            not isinstance(path, str)
            or path in declared
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            add_error(errors, "source_lock_identity")
            continue
        declared[path] = digest
        try:
            actual = canonical_sha256(bounded_file(root, path))
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path")
            continue
        if actual != digest:
            add_error(errors, "source_lock_digest")
    if set(declared) != EXPECTED_SOURCE_PATHS:
        add_error(errors, "source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, relative, 2_500_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "implementation_path")
            continue
        if any(marker not in text for marker in markers):
            add_error(errors, "implementation_marker")
    return len(IMPLEMENTATION_MARKERS)


def validate_migration(root: Path, errors: list[str]) -> None:
    try:
        text = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "migration_path")
        return
    for marker in (
        "hwpx-agent.table-chart/v1",
        "Existing documents",
        "Cursor-only chart creation",
        "three-dimensional vertical bar",
        "partial plan or receipt",
        "separate Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-chart-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 1,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "actual_hwpx": False,
        "actual_hangul": False,
        "p06_09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_CHART_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
