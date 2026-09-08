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
CONTRACT = "protocol/private/p06-table-thousands-v1.json"
MIGRATION = "protocol/migrations/p06-table-thousands-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_THOUSANDS_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_THOUSANDS_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-032", "capability_id": "table.thousands_add"},
    {"feature_id": "TABLE-033", "capability_id": "table.thousands_remove"},
]
EXPECTED_SOURCE_PATHS = {
    "crates/domain-ir/src/lib.rs",
    "crates/domain-ir/src/table_thousands.rs",
    "crates/domain-ir/tests/table_thousands.rs",
    POLICY,
    REPORT,
}
EXPECTED_LIMITS = {
    "input_bytes": 8_192,
    "selected_cells": 256,
    "rows": 10_000,
    "columns": 1_024,
    "decimal_places": 12,
    "serialized_bytes": 1_048_576,
}
EXPECTED_NOT_CLAIMED = {
    "visible_text_number_parsing_or_rewrite": False,
    "general_percent_scientific_or_custom_format_conversion": False,
    "formula_evaluation_or_cache_oracle": False,
    "hwpx_number_format_lowering_or_readback": False,
    "hancom_2020_target_build": False,
    "pagination_or_render": False,
    "automation_or_differential": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_thousands.rs": (
        'TABLE_THOUSANDS_SCHEMA_VERSION: &str = "hwpx-agent.table-thousands/v1"',
        "pub enum TableThousandsMode",
        "pub struct TableThousandsRequest",
        "pub struct TableThousandsPlan",
        "pub struct TableThousandsBuilder",
        "pub fn from_json",
        "pub const fn capability_id",
        "pub fn build",
        "FormulaNumberFormat::Number",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_thousands;",
        "TableThousandsBuilder",
        "TableThousandsRequest",
        "TABLE_THOUSANDS_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_thousands.rs": (
        "add_and_remove_change_only_grouping_and_preserve_sorted_selection",
        "add_is_idempotent_and_plan_bytes_are_deterministic",
        "request_rejects_empty_duplicate_out_of_bounds_and_oversized_selection",
        "build_requires_exact_unique_supplied_cells",
        "non_number_formats_fail_closed_without_partial_plan",
        "exact_dimensions_are_revalidated_during_build",
        "strict_json_and_input_bounds_fail_closed",
        "thousands_plan_output_bound_is_enforced_after_cell_validation",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded component implemented; no HWPX or Hangul 2020 oracle claim",
        "use_grouping=true",
        "use_grouping=false",
        "unit_passed",
    ),
    REPORT: (
        "Result: `component_pass`",
        "9/9 PASS",
        "cataloged`: 22 to 20",
        "unit_passed`: 21 to 23",
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
        "schema_version": "hwpx-agent.table-thousands-contract/v1",
        "model_schema_version": "hwpx-agent.table-thousands/v1",
        "scope": "p06_09_pure_formula_cell_grouping_component_current_pc_local_development",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": sorted(EXPECTED_SOURCE_PATHS),
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
        "semantics": {"selection", "input_format", "add", "remove", "preserve", "idempotence"},
        "binding": {
            "dimensions",
            "coordinates",
            "supplied_cells",
            "revalidation",
            "serialization",
        },
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("input_format") != "existing_number_only":
            add_error(errors, "semantics_input_format")
        if semantics.get("add") != "set_use_grouping_true_only":
            add_error(errors, "semantics_add")
        if semantics.get("remove") != "set_use_grouping_false_only":
            add_error(errors, "semantics_remove")
        if semantics.get("preserve") != "decimal_places_owner_formula_ast_and_cache_exact":
            add_error(errors, "semantics_preserve")

    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 10
        or len(set(failure_policy)) != 10
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
        "hwpx-agent.table-thousands/v1",
        "existing `Number` format",
        "no partial plan",
        "separately versioned",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-thousands-validation/v1",
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
        "P06_TABLE_THOUSANDS_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
