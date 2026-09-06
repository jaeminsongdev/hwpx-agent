#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_grid_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_grid_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_grid_validator", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table grid validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


grid_validator = load_grid_validator()

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-operations-v1.json")
EXPECTED_SOURCE_PATHS = grid_validator.EXPECTED_SOURCE_PATHS
EXPECTED_CAPABILITIES = [
    "table.create",
    "table.insert_rows",
    "table.insert_columns",
    "table.delete_rows",
    "table.delete_columns",
]
EXPECTED_OPERATIONS = {
    "create": "exact_rows_times_columns_caller_ids_become_row_major_1x1_masters",
    "insert_rows": "index_in_zero_through_rows_and_one_new_1x1_master_per_inserted_slot",
    "insert_columns": "index_in_zero_through_columns_and_one_new_1x1_master_per_inserted_slot",
    "delete_rows": "nonempty_in_bounds_interval_must_fully_contain_every_intersected_master",
    "delete_columns": "nonempty_in_bounds_interval_must_fully_contain_every_intersected_master",
}
EXPECTED_SPAN_POLICY = {
    "insert_inside_span": "reject",
    "insert_at_span_edge": "preserve_identity_and_shift_if_after",
    "delete_full_span": "remove_master_identity",
    "delete_partial_span": "reject",
    "implicit_expand_shrink_or_split": "forbidden_until_p06_03",
}
EXPECTED_IDENTITY_POLICY = {
    "new_ids": "caller_supplied_exact_unique_bounded",
    "survivors": "same_logical_id_and_span_with_deterministic_coordinate_remap",
    "deleted": "canonical_original_master_order",
    "debug_output": "dimensions_and_counts_only",
}
EXPECTED_VALIDATION_ORDER = [
    "nonzero_count",
    "index_or_range",
    "result_dimension_and_slot_limits",
    "exact_new_master_id_count",
    "span_boundary_conflict",
    "fallible_allocation",
    "table_grid_invariant_and_bounded_serialization",
]
EXPECTED_FAILURE_POLICY = [
    "zero_count",
    "insertion_index_out_of_bounds",
    "deletion_range_out_of_bounds",
    "would_empty_grid",
    "new_master_cell_count_mismatch",
    "span_boundary_conflict",
    "dimension_overflow",
    "underlying_table_grid_error",
]
EXPECTED_NOT_CLAIMED = {
    "cell_content_or_style_inheritance": False,
    "span_expand_shrink_or_split": False,
    "merge_or_split": False,
    "formula_reference_movement": False,
    "hwpx_xml_lift_or_lower": False,
    "hancom_runtime_execution": False,
    "semantic_reopen_or_render": False,
    "public_tool_support": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "phase_complete": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_operations.rs": (
        'pub const TABLE_OPERATIONS_SCHEMA_VERSION: &str = "hwpx-agent.table-operations/v1";',
        "pub fn create_unmerged",
        "pub fn insert_rows",
        "pub fn insert_columns",
        "pub fn delete_rows",
        "pub fn delete_columns",
        "pub struct TableOperationReceipt",
        "pub struct TableCellRemap",
        "SpanBoundaryConflict",
        "WouldEmptyGrid",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_operations;",
        "TableOperationError",
        "TableOperationReceipt",
        "TABLE_OPERATIONS_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_operations.rs": (
        "creates_unmerged_grid_from_exact_row_major_identifiers",
        "receipt_serialization_is_repeatable_and_canonically_ordered",
        "inserts_rows_and_columns_with_deterministic_identity_remaps",
        "delete_accepts_full_span_removal_and_rejects_partial_span_removal",
        "fixed_seed_unmerged_edit_sequences_preserve_indexes_and_roundtrip",
    ),
}


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=grid_validator.reject_duplicate_keys,
    )
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract_path = grid_validator.bounded_file(root, CONTRACT_RELATIVE.as_posix())
        contract = load_contract(contract_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-operations-contract/v1",
        "model_schema_version": "hwpx-agent.table-operations/v1",
        "table_grid_prerequisite": "hwpx-agent.table-grid/v1",
        "scope": "p06_02_pure_grid_create_insert_delete_current_pc_local_development",
        "source_lock_canonicalization": "utf8_lf_sha256",
        "atomicity": "source_grid_is_immutable_and_only_a_fully_validated_result_is_returned",
        "migration": "protocol/migrations/p06-table-operations-v0-to-v1.md",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)
    if contract.get("capabilities") != EXPECTED_CAPABILITIES:
        errors.append("capabilities")

    if contract.get("operations") != EXPECTED_OPERATIONS:
        errors.append("operations")
    if contract.get("span_policy") != EXPECTED_SPAN_POLICY:
        errors.append("span_policy")
    if contract.get("identity_policy") != EXPECTED_IDENTITY_POLICY:
        errors.append("identity_policy")
    if contract.get("validation_order") != EXPECTED_VALIDATION_ORDER:
        errors.append("validation_order")
    if contract.get("failure_policy") != EXPECTED_FAILURE_POLICY:
        errors.append("failure_policy")

    source_locks = contract.get("source_locks")
    source_count = len(source_locks) if isinstance(source_locks, list) else 0
    declared_paths: set[str] = set()
    if not isinstance(source_locks, list):
        errors.append("source_locks_shape")
    else:
        for entry in source_locks:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append("source_lock_shape")
                continue
            relative = entry.get("path")
            expected_digest = entry.get("sha256")
            if not isinstance(relative, str) or not isinstance(expected_digest, str):
                errors.append("source_lock_types")
                continue
            if relative in declared_paths:
                errors.append("source_lock_duplicate")
                continue
            declared_paths.add(relative)
            try:
                path = grid_validator.bounded_file(root, relative)
                actual_digest = grid_validator.sha256_utf8_lf(path)
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual_digest != expected_digest:
                errors.append("source_lock_digest")
        if declared_paths != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = grid_validator.bounded_file(
            root, "protocol/migrations/p06-table-operations-v0-to-v1.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.table-operations/v1",
            "TableGrid",
            "fail closed",
            "P06-03",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = grid_validator.bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")

    if contract.get("not_claimed") != EXPECTED_NOT_CLAIMED:
        errors.append("not_claimed")

    return result(
        errors=sorted(errors),
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-operations-validation/v1",
        "state": "pass" if not errors else "fail",
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "errors": errors,
    }


def main() -> int:
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["errors"]:
        return 1
    print("P06_TABLE_OPERATIONS_CONTRACT_PASS source_locks=4 implementation_files=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
