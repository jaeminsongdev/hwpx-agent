#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_operations_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_operations_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_operations_validator", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table operations validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


operations_validator = load_operations_validator()
grid_validator = operations_validator.grid_validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-merge-split-v1.json")
EXPECTED_SOURCE_PATHS = operations_validator.EXPECTED_SOURCE_PATHS
EXPECTED_CAPABILITIES = ["table.merge_cells", "table.split_cell"]
EXPECTED_CONTENT_STATE = {
    "master_entries": "exactly_one_per_current_grid_master",
    "content_block_ownership": "globally_unique_ordered_logical_ids",
    "grid_binding": "canonical_grid_sha256",
    "lookup": "private_sorted_id_index_logarithmic",
    "limits": "identifier_and_total_block_count_are_finite",
    "debug_output": "counts_only",
}
EXPECTED_MERGE_GEOMETRY = {
    "request": "explicit_complete_rectangular_slot_set",
    "partial_existing_master": "reject",
    "nonrectangular_or_duplicate": "reject",
    "single_master_noop": "reject",
}
EXPECTED_MERGE_CONTENT_POLICY = {
    "concatenate": "all_blocks_in_canonical_source_cell_then_intra_cell_order",
    "distribute": "one_destination_equivalent_to_lossless_canonical_concatenation",
    "first": "top_left_source_only_and_all_other_blocks_explicitly_receipted_as_discarded",
    "reject_if_multiple": "fail_when_more_than_one_source_cell_is_nonempty",
}
EXPECTED_SPLIT_GEOMETRY = {
    "request": "nonzero_row_and_column_part_counts_inside_one_existing_master",
    "divisibility": "both_source_spans_must_divide_evenly",
    "logical_grid_dimensions": "unchanged",
    "single_part_noop": "reject",
}
EXPECTED_SPLIT_CONTENT_POLICY = {
    "distribute": "stable_contiguous_balanced_chunks_in_row_major_destination_order",
    "concatenate_first_reject_if_multiple": (
        "all_source_blocks_remain_in_preserved_top_left_result"
    ),
    "discard": "forbidden",
}
EXPECTED_IDENTITY_POLICY = {
    "merge_survivor": "master_covering_region_top_left",
    "merge_retired": "other_selected_masters_in_canonical_premerge_order",
    "split_survivor": "source_master_at_top_left",
    "split_created": "exact_caller_ids_in_row_major_order_excluding_top_left",
}
EXPECTED_RECEIPT = {
    "binding": "before_and_after_canonical_grid_sha256",
    "fields": "operation_policy_region_preserved_retired_created_transfers_discarded",
    "ordering": "deterministic",
    "serialization": "bounded_compact_json",
    "mutation": "private_fields_read_only_getters",
}
EXPECTED_VALIDATION_ORDER = [
    "content_state_grid_binding",
    "selection_or_subdivision_geometry",
    "existing_master_span_containment",
    "explicit_content_policy",
    "exact_new_master_id_count",
    "fallible_bounded_allocation",
    "table_grid_invariant",
    "content_ownership_invariant",
    "bounded_receipt_serialization",
]
EXPECTED_FAILURE_POLICY = [
    "content_master_set_mismatch",
    "duplicate_content_master_or_block",
    "content_grid_mismatch",
    "empty_duplicate_out_of_bounds_or_nonrectangular_selection",
    "partial_master_selection",
    "no_structural_change",
    "multiple_nonempty_cells",
    "invalid_or_nondivisible_split",
    "new_master_cell_count_mismatch",
    "finite_limit_or_allocation_failure",
    "underlying_table_grid_error",
]
EXPECTED_NOT_CLAIMED = {
    "flow_body_bytes_validated": False,
    "style_or_formula_semantics": False,
    "table_split_or_join": False,
    "split_with_logical_grid_expansion": False,
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
    "crates/domain-ir/src/table_merge_split.rs": (
        'pub const TABLE_MERGE_SPLIT_SCHEMA_VERSION: &str = "hwpx-agent.table-merge-split/v1";',
        "pub enum ContentPreservationPolicy",
        "pub struct TableContentState",
        "pub struct TableSplitRequest",
        "pub fn merge_cells",
        "pub fn split_cell",
        "pub struct TableMergeSplitReceipt",
        "NonRectangularSelection",
        "PartialMasterSelection",
        "MultipleNonemptyCells",
        "SplitNotDivisible",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_merge_split;",
        "ContentPreservationPolicy",
        "TableContentState",
        "TableMergeSplitError",
        "TableSplitRequest",
        "TABLE_MERGE_SPLIT_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_merge_split.rs": (
        "content_state_enforces_block_and_identifier_limits",
        "merge_concatenates_in_canonical_cell_order_and_preserves_top_left_identity",
        "merge_rejects_nonrectangular_duplicate_out_of_bounds_and_noop_selections",
        "merge_rejects_partial_intersection_with_existing_span",
        "split_distributes_contiguous_balanced_content_and_roundtrips_merge",
        "fixed_seed_merge_split_corpus_preserves_all_content_and_grid_invariants",
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
        "schema_version": "hwpx-agent.table-merge-split-contract/v1",
        "model_schema_version": "hwpx-agent.table-merge-split/v1",
        "prerequisites": ["hwpx-agent.table-grid/v1", "hwpx-agent.table-operations/v1"],
        "scope": "p06_03_pure_ir_merge_split_content_ownership_current_pc_local_development",
        "source_lock_canonicalization": "utf8_lf_sha256",
        "atomicity": (
            "source_grid_and_content_are_immutable_and_only_fully_revalidated_results_return"
        ),
        "migration": "protocol/migrations/p06-table-merge-split-v0-to-v1.md",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)
    exact_objects = {
        "capabilities": EXPECTED_CAPABILITIES,
        "content_state": EXPECTED_CONTENT_STATE,
        "merge_geometry": EXPECTED_MERGE_GEOMETRY,
        "merge_content_policy": EXPECTED_MERGE_CONTENT_POLICY,
        "split_geometry": EXPECTED_SPLIT_GEOMETRY,
        "split_content_policy": EXPECTED_SPLIT_CONTENT_POLICY,
        "identity_policy": EXPECTED_IDENTITY_POLICY,
        "receipt": EXPECTED_RECEIPT,
        "validation_order": EXPECTED_VALIDATION_ORDER,
        "failure_policy": EXPECTED_FAILURE_POLICY,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in exact_objects.items():
        if contract.get(key) != expected:
            errors.append(key)

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
            root, "protocol/migrations/p06-table-merge-split-v0-to-v1.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.table-merge-split/v1",
            "TableContentState",
            "fail closed",
            "discarded content-block ID",
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

    return result(
        errors=sorted(errors),
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-merge-split-validation/v1",
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
    print("P06_TABLE_MERGE_SPLIT_CONTRACT_PASS source_locks=4 implementation_files=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
