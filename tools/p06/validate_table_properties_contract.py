#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.p06.validate_table_geometry_contract import (
    add_error,
    bounded_file,
    canonical_sha256,
    reject_duplicate_keys,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-properties-v1.json"
MIGRATION = "protocol/migrations/p06-table-properties-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_PROPERTIES_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_PROPERTIES_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-007", "capability_id": "table.properties"},
    {"feature_id": "TABLE-008", "capability_id": "table.cell_border_each"},
    {"feature_id": "TABLE-009", "capability_id": "table.cell_border_unified"},
    {"feature_id": "TABLE-047", "capability_id": "table.cell_diagonal"},
]
EXPECTED_REFERENCES = [
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/cellborder/cellborder(each).htm",
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/cellborder/cellborder(many).htm",
    "https://help.hancom.com/hoffice110/ko-KR/Hwp/table/cellborder/cellborder(background).htm",
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/cellborder/cellborder(diagonal).htm",
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 16_777_216,
    "master_cells": 1_000_000,
    "selected_slots": 1_000_000,
    "identifier_bytes": 256,
    "serialized_bytes": 134_217_728,
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "border_fill_catalog_materialization": False,
    "package_mutation_or_preservation": False,
    "semantic_reopen": False,
    "formula_readback": False,
    "page_split_or_render": False,
    "hancom_2020_target_build": False,
    "automation_or_differential": False,
    "diagonal_hwpx_lowering": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod table_properties;",
        "TablePropertiesBuilder",
        "TableUnifiedBorderPatch",
        "TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID",
        "TABLE_CELL_DIAGONAL_CAPABILITY_ID",
        "TableDiagonalValue",
    ),
    "crates/domain-ir/src/table_properties.rs": (
        'TABLE_PROPERTIES_SCHEMA_VERSION: &str = "hwpx-agent.table-properties/v1"',
        'TABLE_PROPERTIES_CAPABILITY_ID: &str = "table.properties"',
        'TABLE_CELL_BORDER_EACH_CAPABILITY_ID: &str = "table.cell_border_each"',
        'TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID: &str = "table.cell_border_unified"',
        'TABLE_CELL_DIAGONAL_CAPABILITY_ID: &str = "table.cell_diagonal"',
        "pub enum TableDiagonalApplyMode",
        "pub struct TableDiagonalValue",
        "fn resolve_diagonal_identity",
        "fn validate_diagonal_value",
        "pub struct TablePropertiesState",
        "pub enum TablePropertiesOperation",
        "pub struct TablePropertiesPlan",
        "pub struct TablePropertiesBuilder",
        "fn validate_selection",
        "fn span_selection",
        "fn apply_operation",
        "fn apply_digest_patch",
        "impl fmt::Debug for TablePropertiesReceipt",
        "pub const fn code",
    ),
    "crates/domain-ir/tests/table_properties.rs": (
        "table_only_properties_change_preserves_every_cell_without_selection",
        "selected_cell_properties_change_only_the_declared_non_border_facet",
        "each_cell_border_applies_four_independent_edges_and_background_per_master",
        "unified_border_maps_outer_frame_and_internal_grid_lines_separately",
        "each_cell_diagonal_accepts_non_contiguous_cells_and_preserves_other_facets",
        "unified_diagonal_requires_a_rectangle_and_binds_one_region_identity",
        "unified_diagonal_accepts_only_complete_merged_cells",
        "diagonal_clear_empty_topology_and_independent_flags_are_explicit",
        "merged_cells_must_be_fully_selected_and_resolve_from_their_real_edges",
        "duplicate_out_of_bounds_and_non_rectangular_unified_selections_fail_closed",
        "properties_and_each_cell_border_accept_exact_non_contiguous_cell_sets",
        "clear_and_preserve_are_distinct_and_changes_are_counted_from_actual_state",
        "fixed_shape_corpus_assigns_every_selected_master_exactly_once",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "component_only / unit_passed",
        "non-contiguous multi-cell blocks cannot use the unified operation",
        "outer top/right/bottom/left",
        "## TABLE-047 diagonal semantics",
        "clearing an already absent side or diagonal is not counted as a change",
        "reasoning level max",
    ),
    REPORT: (
        "Result: component_pass",
        "Focused Rust table-properties tests: 21/21 PASS.",
        "deterministic 144-shape corpus",
        "cataloged 9 to 5",
        "unit_passed 34 to 38",
        "green rows: remains 0/61",
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

    expected_keys = {
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
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-properties-contract/v1",
        "model_schema_version": "hwpx-agent.table-properties/v1",
        "scope": (
            "p06_09_pure_bounded_table_and_cell_properties_"
            "current_pc_local_development"
        ),
        "features": EXPECTED_FEATURES,
        "official_references": EXPECTED_REFERENCES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": sorted(IMPLEMENTATION_MARKERS),
        "default_limits": EXPECTED_LIMITS,
        "not_claimed": EXPECTED_NOT_CLAIMED,
        "gate_decision": {
            "component": "pass",
            "direct_stage": "unit_passed",
            "actual_hwpx": False,
            "actual_hangul": False,
            "p06_09": "in_progress",
            "product_complete": False,
        },
    }
    for key, expected in exact.items():
        actual = contract.get(key)
        if key == "implementation_files" and isinstance(actual, list):
            actual = sorted(actual)
        if actual != expected:
            add_error(errors, key)

    expected_objects = {
        "semantics": {
            "selection",
            "properties",
            "each_border",
            "unified_border",
            "background",
            "diagonal",
            "preservation",
        },
        "binding": {"identity", "cells", "plan", "receipt", "serialization"},
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        exact_semantics = {
            "selection": (
                "canonical_exact_slot_sets_with_complete_merged_containment_"
                "and_rectangle_required_for_unified_border_or_diagonal"
            ),
            "each_border": (
                "same_four_side_patch_roles_resolved_independently_for_"
                "every_selected_master_cell"
            ),
            "unified_border": (
                "selection_outer_frame_and_inner_horizontal_vertical_"
                "patches_resolved_over_real_master_edges"
            ),
            "diagonal": (
                "explicit_each_cell_or_unified_region_identity_with_unmodified_"
                "slash_flags_back_slash_center_line_and_line_tuple_digest"
            ),
        }
        for key, expected in exact_semantics.items():
            if semantics.get(key) != expected:
                add_error(errors, f"semantics_{key}")

    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 17
        or len(set(failure_policy)) != 17
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        add_error(errors, "failure_policy")

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
            text = bounded_file(root, relative, 2_000_000).read_text(encoding="utf-8")
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
        "hwpx-agent.table-properties/v1",
        "Existing documents",
        "preserve, clear and set",
        "no partial plan",
        "separately versioned adapters",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-properties-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 4,
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
        "P06_TABLE_PROPERTIES_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
