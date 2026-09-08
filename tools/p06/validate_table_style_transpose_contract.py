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
CONTRACT = "protocol/private/p06-table-style-transpose-v1.json"
MIGRATION = "protocol/migrations/p06-table-style-transpose-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_STYLE_TRANSPOSE_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_STYLE_TRANSPOSE_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-020", "capability_id": "table.table_style"},
    {"feature_id": "TABLE-021", "capability_id": "table.transpose"},
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "style": {
        "input_bytes": 8_388_608,
        "master_cells": 1_000_000,
        "style_rules": 13,
        "identifier_bytes": 256,
        "serialized_bytes": 67_108_864,
    },
    "transpose": {
        "input_bytes": 16_777_216,
        "master_cells": 1_000_000,
        "identifier_bytes": 256,
        "serialized_bytes": 134_217_728,
    },
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "style_catalog_materialization": False,
    "package_mutation_or_preservation": False,
    "semantic_reopen": False,
    "formula_readback": False,
    "page_split_or_render": False,
    "hancom_2020_target_build": False,
    "automation_or_differential": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod table_style;",
        "mod table_transpose;",
        "TableStyleBuilder",
        "TableTransposeBuilder",
    ),
    "crates/domain-ir/src/table_formula.rs": (
        "pub fn transpose(",
        "transposed_dimensions",
        "row_kind: reference.column_kind",
        "column_kind: reference.row_kind",
    ),
    "crates/domain-ir/src/table_style.rs": (
        'TABLE_STYLE_SCHEMA_VERSION: &str = "hwpx-agent.table-style/v1"',
        'TABLE_STYLE_CAPABILITY_ID: &str = "table.table_style"',
        "pub struct TableStyleDefinition",
        "pub struct TableStylePlan",
        "pub struct TableStyleBuilder",
        "impl fmt::Debug for TableStyleRule",
        "impl fmt::Debug for TableStyleReceipt",
        "fn resolve_span_style",
        "fn resolve_coordinate_style",
        "pub const fn code",
    ),
    "crates/domain-ir/src/table_transpose.rs": (
        'TABLE_TRANSPOSE_SCHEMA_VERSION: &str = "hwpx-agent.table-transpose/v1"',
        'TABLE_TRANSPOSE_CAPABILITY_ID: &str = "table.transpose"',
        "pub struct TableTransposeRequest",
        "pub struct TableTransposeRelocation",
        "pub struct TableTransposePlan",
        "pub struct TableTransposeBuilder",
        "impl fmt::Debug for TableTransposeReceipt",
        "caches_cleared",
        "pub const fn code",
    ),
    "crates/domain-ir/tests/table_style.rs": (
        "fixed_precedence_resolves_corners_headers_footers_columns_and_bands",
        "row_or_column_band_precedence_is_explicit",
        "merged_cells_reject_mixed_regions_or_use_the_explicit_anchor",
        "inactive_header_footer_and_column_flags_disable_corner_rules",
        "fixed_seed_shape_corpus_resolves_every_master_exactly_once",
        "public_error_codes_are_stable",
    ),
    "crates/domain-ir/tests/table_transpose.rs": (
        "transposes_complete_merged_grid_payload_style_formula_and_cache",
        "absent_formula_cache_is_not_reported_as_cleared",
        "formula_transpose_swaps_reference_indexes_and_anchor_axes",
        "double_formula_transpose_restores_the_exact_ast",
        "transposed_dimensions_obey_exact_column_ceiling",
        "fixed_seed_rectangular_corpus_preserves_exact_cell_identity",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded semantic components",
        "relative/absolute row and column anchor kinds are transposed",
        "component_only / unit_passed",
        "reasoning level max",
    ),
    REPORT: (
        "Result: component_pass",
        "Focused Rust table-style tests: 14/14 PASS.",
        "Focused Rust table-transpose tests: 14/14 PASS.",
        "cataloged 11 to 9",
        "unit_passed 32 to 34",
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
        "model_schema_versions",
        "scope",
        "features",
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
        "schema_version": "hwpx-agent.table-style-transpose-contract/v1",
        "model_schema_versions": {
            "style_definition": "hwpx-agent.table-style-definition/v1",
            "style_request": "hwpx-agent.table-style/v1",
            "transpose_request": "hwpx-agent.table-transpose/v1",
        },
        "scope": (
            "p06_09_pure_bounded_table_style_and_transpose_"
            "current_pc_local_development"
        ),
        "features": EXPECTED_FEATURES,
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
            "style_definition",
            "style_precedence",
            "merged_style",
            "transpose_grid",
            "transpose_formula",
            "preservation",
        },
        "binding": {
            "identity",
            "cells",
            "style_plan",
            "transpose_plan",
            "receipt",
            "serialization",
        },
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("style_precedence") != (
            "enabled_corners_then_header_footer_then_first_last_columns_"
            "then_explicit_band_precedence_then_whole_table"
        ):
            add_error(errors, "semantics_style_precedence")
        if semantics.get("transpose_grid") != (
            "swap_dimensions_coordinates_and_rectangular_span_axes_"
            "while_preserving_master_identity"
        ):
            add_error(errors, "semantics_transpose_grid")
        if semantics.get("transpose_formula") != (
            "swap_owner_reference_coordinates_and_anchor_axes_"
            "then_clear_unverified_cache"
        ):
            add_error(errors, "semantics_transpose_formula")

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
        "hwpx-agent.table-style-definition/v1",
        "hwpx-agent.table-style/v1",
        "hwpx-agent.table-transpose/v1",
        "Existing documents",
        "no partial plan",
        "separately versioned adapters",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-style-transpose-validation/v1",
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
        "P06_TABLE_STYLE_TRANSPOSE_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
