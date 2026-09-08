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
CONTRACT = "protocol/private/p06-table-sort-v1.json"
MIGRATION = "protocol/migrations/p06-table-sort-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_SORT_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_SORT_REPORT.md"
EXPECTED_FEATURE = {"feature_id": "TABLE-056", "capability_id": "table.sort_cells"}
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 4_194_304,
    "selected_cells": 1_000_000,
    "sort_keys": 64,
    "text_bytes": 16_384,
    "comparison_work": 100_000_000,
    "serialized_bytes": 67_108_864,
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "locale_sensitive_hancom_collation": False,
    "native_formula_rebase": False,
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
    "crates/domain-ir/src/table_sort.rs": (
        'TABLE_SORT_SCHEMA_VERSION: &str = "hwpx-agent.table-sort/v1"',
        'TABLE_SORT_CAPABILITY_ID: &str = "table.sort_cells"',
        "pub struct TableSortRequest",
        "pub struct TableSortRelocation",
        "pub struct TableSortReceipt",
        "pub struct TableSortPlan",
        "pub struct TableSortBuilder",
        "pub fn from_json",
        "pub fn build",
        "validate_comparison_work",
        "compare_numeric",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_sort;",
        "TableSortBuilder",
        "TableSortRequest",
        "TABLE_SORT_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_sort.rs": (
        "row_sort_moves_complete_payload_rows_in_destination_order",
        "key_precedence_is_preserved_and_equal_lines_stay_stable",
        "descending_does_not_reverse_explicit_blank_placement",
        "column_sort_supports_explicit_ascii_case_insensitive_text",
        "integer_and_fixed_decimal_compare_exactly_without_floating_point",
        "formula_policy_is_explicit_and_bound_into_relocations",
        "merged_region_fails_before_a_sort_plan_exists",
        "region_keys_cells_values_and_limits_fail_closed",
        "strict_json_rejects_duplicate_unknown_version_and_size",
        "plan_and_receipt_are_deterministic_and_noop_is_explicit",
        "output_limit_fails_without_returning_a_partial_plan",
        "debug_output_redacts_ids_values_and_digests",
        "fixed_seed_permutations_sort_to_exact_numeric_order",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded component implemented; no HWPX or Hangul 2020 oracle claim",
        "Blank placement is not reversed by descending order",
        "comparison work",
        "component_only / unit_passed",
    ),
    REPORT: (
        "Result: `component_pass`",
        "14/14 PASS",
        "cataloged`: 14 to 13",
        "unit_passed`: 29 to 30",
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
        "feature",
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
        "schema_version": "hwpx-agent.table-sort-contract/v1",
        "model_schema_version": "hwpx-agent.table-sort/v1",
        "scope": "p06_09_pure_bounded_table_sort_current_pc_local_development",
        "feature": EXPECTED_FEATURE,
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
            "region",
            "line_unit",
            "key_precedence",
            "blank_order",
            "value_order",
            "numeric",
            "text",
            "formula",
        },
        "binding": {"identity", "cells", "relocation", "receipt", "serialization"},
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("line_unit") != (
            "complete_rows_or_columns_move_as_whole_cell_payloads"
        ):
            add_error(errors, "semantics_line_unit")
        if semantics.get("key_precedence") != (
            "caller_order_is_semantic_and_equal_lines_keep_original_order"
        ):
            add_error(errors, "semantics_key_precedence")
        if semantics.get("formula") != (
            "reject_move_verbatim_or_rebase_relative_policy_bound_without_claiming_execution"
        ):
            add_error(errors, "semantics_formula")

    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 14
        or len(set(failure_policy)) != 14
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
        "hwpx-agent.table-sort/v1",
        "Existing documents",
        "no partial plan",
        "separately versioned",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-sort-validation/v1",
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
        "P06_TABLE_SORT_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
