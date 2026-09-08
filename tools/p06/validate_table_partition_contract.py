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
CONTRACT = "protocol/private/p06-table-partition-v1.json"
MIGRATION = "protocol/migrations/p06-table-partition-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_PARTITION_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_PARTITION_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-010", "capability_id": "table.split_table"},
    {"feature_id": "TABLE-011", "capability_id": "table.join_table"},
]
EXPECTED_REFERENCES = [
    "https://help.hancom.com/hoffice110/ko-KR/Hwp/table/table(dividing).htm",
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(attach).htm",
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/toolbox/object_table.htm",
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 33_554_432,
    "master_cells": 1_000_000,
    "separator_tokens": 4_096,
    "separator_spaces": 1_000_000,
    "identifier_bytes": 256,
    "serialized_bytes": 134_217_728,
    "table_width_hwpunit": 100_000_000,
}
EXPECTED_SEMANTICS = {
    "state": "complete_exact_grid_table_width_column_tracks_master_payload_cell_property_and_validated_formula_state",
    "split_boundary": "cursor_row_starts_second_table_first_row_rejected_and_crossing_row_spans_fail_closed",
    "split_preservation": "leading_identity_and_all_master_payload_cell_properties_preserved_both_tables_inherit_source_properties",
    "join_gap": "positive_space_runs_and_paragraph_breaks_only_with_at_least_one_paragraph_break",
    "join_properties": "leading_table_identity_and_properties_retained_trailing_rows_appended_and_larger_width_used",
    "join_columns": "unequal_column_layouts_projected_to_reduced_rational_union_with_deterministic_hwpunit_materialization",
    "formulas": "explicit_reject_or_rebase_and_clear_cache_cross_split_boundary_references_rejected",
    "preservation": "state_request_and_document_flow_sha256_bound_with_no_source_mutation_or_partial_plan",
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "section_xml_lowering": False,
    "package_mutation_or_preservation": False,
    "semantic_reopen": False,
    "formula_readback": False,
    "page_split_or_render": False,
    "hancom_2020_target_build": False,
    "automation_or_differential": False,
    "common_lattice_target_rounding_verified": False,
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
        "mod table_partition;",
        "TablePartitionBuilder",
        "WholeTableSplitRequest",
        "WholeTableJoinRequest",
        "TABLE_SPLIT_TABLE_CAPABILITY_ID",
        "TABLE_JOIN_TABLE_CAPABILITY_ID",
    ),
    "crates/domain-ir/src/table_partition.rs": (
        'TABLE_PARTITION_SCHEMA_VERSION: &str = "hwpx-agent.table-partition/v1"',
        'TABLE_SPLIT_TABLE_CAPABILITY_ID: &str = "table.split_table"',
        'TABLE_JOIN_TABLE_CAPABILITY_ID: &str = "table.join_table"',
        "pub struct TablePartitionState",
        "pub struct WholeTableSplitRequest",
        "pub struct WholeTableJoinRequest",
        "pub struct WholeTableSplitPlan",
        "pub struct WholeTableJoinPlan",
        "pub struct TablePartitionBuilder",
        "fn common_lattice",
        "fn rebase_split_formula",
        "fn rebase_join_formula",
        "pub const fn code",
    ),
    "crates/domain-ir/tests/table_partition.rs": (
        "split_starts_second_table_at_cursor_row_and_preserves_complete_cells",
        "split_rejects_first_row_out_of_bounds_and_stale_state",
        "split_rejects_a_merged_cell_crossing_the_row_boundary",
        "split_rejects_cross_table_formula_references_without_partial_output",
        "join_builds_common_column_lattice_uses_larger_width_and_leading_properties",
        "join_rejects_non_whitespace_missing_break_and_empty_space_tokens",
        "common_column_lattice_fails_closed_when_hwpunit_rounding_collapses_a_track",
        "canonical_state_is_order_independent_and_debug_redacts_sensitive_values",
    ),
    POLICY: (
        "component_only / unit_passed",
        "The cursor row is the only split boundary",
        "## TABLE-010 split semantics",
        "larger source width",
        "reduced-rational column boundaries",
        "reasoning level max",
    ),
    REPORT: (
        "Result: `component_pass`",
        "Focused Rust table-partition tests: 13/13 PASS.",
        "cataloged` 5 to 3",
        "unit_passed` 38 to 40",
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

    if set(contract) != EXPECTED_KEYS:
        add_error(errors, "contract_keys")
    expected_scalars = {
        "schema_version": "hwpx-agent.table-partition-contract/v1",
        "model_schema_version": "hwpx-agent.table-partition/v1",
        "scope": "p06_09_pure_bounded_whole_table_split_join_current_pc_local_development",
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
        "split",
        "join",
        "plan",
        "serialization",
    }:
        add_error(errors, "binding")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 16
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
        "hwpx-agent.table-partition/v1",
        "Existing documents",
        "current cell coordinate",
        "separator-paragraph ID",
        "no partial plan or receipt",
        "separate Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-partition-validation/v1",
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
        "P06_TABLE_PARTITION_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
