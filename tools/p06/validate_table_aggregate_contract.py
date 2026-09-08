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
CONTRACT = "protocol/private/p06-table-aggregate-v1.json"
MIGRATION = "protocol/migrations/p06-table-aggregate-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_AGGREGATE_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_AGGREGATE_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-formula-v1.json",
}
EXPECTED_FEATURES = {
    "TABLE-022": "table.block_sum",
    "TABLE-023": "table.block_average",
    "TABLE-024": "table.block_product",
    "TABLE-026": "table.vertical_sum",
    "TABLE-027": "table.horizontal_average",
    "TABLE-028": "table.vertical_average",
    "TABLE-029": "table.horizontal_product",
    "TABLE-030": "table.vertical_product",
}
EXPECTED_EVIDENCE = {
    "rust_tests": 8,
    "axis_function_combinations": 9,
    "contract_tests": 4,
    "backend": "component_only",
    "direct_stage": "unit_passed",
    "validations": ["schema"],
}
EXPECTED_NOT_CLAIMED = {
    "formula_evaluation_or_verified_cache": False,
    "direct_hwpx_adapter": False,
    "semantic_reopen_or_formula_readback": False,
    "page_split_or_render_diff": False,
    "hangul_2020_target_oracle": False,
    "automation_or_differential": False,
    "release_enabled": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_aggregate.rs": (
        'TABLE_AGGREGATE_SCHEMA_VERSION: &str = "hwpx-agent.table-aggregate/v1"',
        "pub enum TableAggregateAxis",
        "pub struct TableAggregateRequest",
        "pub struct TableAggregatePlan",
        "pub struct TableAggregateBuilder",
        "pub fn from_json",
        "pub const fn capability_id",
        "pub fn build",
        "fn reject_duplicate_json_keys",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_aggregate;",
        "TableAggregateBuilder",
        "TableAggregateRequest",
        "TABLE_AGGREGATE_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_aggregate.rs": (
        "all_nine_aggregate_operations_compile_to_exact_formulas",
        "capability_ids_are_exact_for_all_functions_and_axes",
        "horizontal_and_vertical_ranges_must_be_strictly_before_destination",
        "reversed_self_referencing_and_out_of_bounds_requests_fail_closed",
        "strict_json_rejects_duplicate_unknown_and_wrong_version_fields",
        "plan_serialization_is_deterministic_and_debug_redacts_formula",
        "input_output_and_dimension_limits_are_enforced",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded component implemented; no HWPX or Hangul 2020 oracle claim",
        "strictly to the left",
        "strictly above",
        "unit_passed",
    ),
    REPORT: (
        "Result: `component_pass`",
        "8/8 PASS",
        "9/9 exact canonical formulas",
        "cataloged`: 30 to 22",
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
        "compatibility_regression",
        "prerequisites",
        "source_lock_canonicalization",
        "source_locks",
        "semantics",
        "binding",
        "default_limits",
        "failure_policy",
        "migration",
        "policy",
        "report",
        "expected_evidence",
        "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-aggregate-contract/v1",
        "model_schema_version": "hwpx-agent.table-aggregate/v1",
        "scope": "p06_09_pure_bounded_table_aggregate_planner_current_pc_local_development",
        "features": EXPECTED_FEATURES,
        "compatibility_regression": {"TABLE-025": "table.horizontal_sum"},
        "prerequisites": [
            "hwpx-agent.table-formula/v1",
            "checked_zero_based_cell_coordinates",
            "exact_table_dimensions",
        ],
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "default_limits": {"rows": 10_000, "columns": 1_024, "serialized_bytes": 1_048_576},
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "expected_evidence": EXPECTED_EVIDENCE,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    expected_objects = {
        "semantics": {
            "block",
            "horizontal",
            "vertical",
            "functions",
            "references",
            "cache",
            "number_format",
        },
        "binding": {"dimensions", "coordinates", "capability", "serialization"},
    }
    for key, keys in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != keys:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("horizontal") != "one_row_strictly_left_of_destination":
            add_error(errors, "semantics_horizontal")
        if semantics.get("vertical") != "one_column_strictly_above_destination":
            add_error(errors, "semantics_vertical")
        if semantics.get("functions") != ["SUM", "AVG", "PRODUCT"]:
            add_error(errors, "semantics_functions")
        if semantics.get("cache") != "absent":
            add_error(errors, "semantics_cache")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 8
        or len(set(failure_policy)) != 8
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
        "hwpx-agent.table-aggregate/v1",
        "strictly left",
        "strictly above",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-aggregate-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 8,
        "planner_capabilities": 9,
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
        "P06_TABLE_AGGREGATE_CONTRACT_PASS "
        f"features={validation['features']} planner_capabilities={validation['planner_capabilities']} "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
