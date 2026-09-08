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
CONTRACT = "protocol/private/p06-table-ruling-v1.json"
MIGRATION = "protocol/migrations/p06-table-ruling-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_RULING_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_RULING_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-002", "capability_id": "table.draw"},
    {"feature_id": "TABLE-003", "capability_id": "table.eraser"},
]
EXPECTED_REFERENCES = [
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(draw).htm",
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(eraser).htm",
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
    "edges": 2_100_000,
    "payload_blocks": 1_000_000,
    "identifier_bytes": 256,
    "dimension_hwpunit": 1_000_000_000,
    "serialized_bytes": 134_217_728,
}
EXPECTED_SEMANTICS = {
    "state": "complete_exact_frame_physical_lattice_normalized_unit_edges_master_cells_payload_properties_formula_and_cache",
    "outer_rectangle": "no_existing_table_context_creates_exact_one_cell_frame_with_four_visible_edges",
    "draw_stroke": "physical_lattice_refinement_and_rectangular_connectivity_partition_for_full_row_full_column_and_local_cell_split",
    "diagonal": "independent_cell_local_slash_and_back_slash_line_identity_without_topology_change",
    "eraser": "shared_distinct_master_edge_structural_rectangular_merge_otherwise_explicit_transparent_line",
    "preservation": "ordered_payloads_equal_merge_properties_single_formula_rebase_topology_stale_cache_clear_and_atomic_no_partial_result",
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "package_mutation_or_preservation": False,
    "semantic_reopen": False,
    "formula_cache_readback": False,
    "page_split_or_render": False,
    "hancom_2020_target_build": False,
    "ui_coordinate_calibration": False,
    "automation_or_differential": False,
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
        "mod table_ruling;",
        "TableRulingBuilder",
        "TableRulingState",
        "TableRulingRequest",
        "TABLE_DRAW_CAPABILITY_ID",
        "TABLE_ERASER_CAPABILITY_ID",
    ),
    "crates/domain-ir/src/table_ruling.rs": (
        'TABLE_RULING_SCHEMA_VERSION: &str = "hwpx-agent.table-ruling/v1"',
        'TABLE_DRAW_CAPABILITY_ID: &str = "table.draw"',
        'TABLE_ERASER_CAPABILITY_ID: &str = "table.eraser"',
        "pub struct TableRulingState",
        "DrawOuterRectangle",
        "DrawStroke",
        "DrawDiagonal",
        "EraseStroke",
        "EraseDiagonal",
        "fn components_for_span",
        "fn merge_cells_across_stroke",
        "pub enum TableRulingError",
    ),
    "crates/domain-ir/tests/table_ruling.rs": (
        "outer_rectangle_creates_exact_one_cell_table_and_visible_frame",
        "full_row_and_column_strokes_build_a_complete_two_by_two_topology",
        "local_cell_split_refines_the_lattice_without_splitting_its_neighbor",
        "draw_and_erase_diagonals_are_nonstructural_and_directional",
        "erasing_a_shared_edge_merges_cells_and_concatenates_payload_in_row_major_order",
        "erasing_an_internal_edge_of_one_merged_cell_is_transparent_not_a_merge",
        "shared_edge_merge_rebases_the_single_formula_and_clears_only_its_stale_cache",
        "shared_edge_merge_clears_external_formula_caches_only_under_explicit_policy",
        "splitting_an_existing_merged_lattice_with_formula_state_fails_closed",
        "request_and_builder_both_reject_state_grid_or_flow_drift",
        "strict_json_complete_sets_and_finite_limits_fail_closed",
        "debug_output_redacts_identifiers_payloads_properties_formulas_and_digests",
    ),
    POLICY: (
        "component_only / unit_passed",
        "outer rectangle",
        "explicitly transparent",
        "## Gate boundary",
        "Reasoning level: `max`",
    ),
    REPORT: (
        "Result: `component_pass`",
        "Focused Rust table-ruling tests: 17/17 PASS.",
        "`cataloged`: 2 to 0",
        "`unit_passed`: 41 to 43",
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
        "schema_version": "hwpx-agent.table-ruling-contract/v1",
        "model_schema_version": "hwpx-agent.table-ruling/v1",
        "scope": "p06_09_pure_bounded_table_draw_eraser_ruling_topology_current_pc_local_development",
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
        or len(failure_policy) != 18
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
            text = bounded_file(root, relative, 4_000_000).read_text(encoding="utf-8")
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
        "hwpx-agent.table-ruling/v1",
        "Existing documents",
        "outer rectangle",
        "shared edge",
        "partial state, plan, or receipt",
        "separate Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-ruling-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 2,
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
        "P06_TABLE_RULING_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
