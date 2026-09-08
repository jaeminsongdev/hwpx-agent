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
CONTRACT = "protocol/private/p06-table-auto-fill-v1.json"
MIGRATION = "protocol/migrations/p06-table-auto-fill-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_AUTO_FILL_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_AUTO_FILL_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-057", "capability_id": "table.auto_fill"},
    {"feature_id": "TABLE-058", "capability_id": "table.auto_fill_series"},
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 4_194_304,
    "selected_cells": 1_000_000,
    "series_items": 4_096,
    "text_bytes": 16_384,
    "total_text_bytes": 4_194_304,
    "generation_work": 1_000_000,
    "serialized_bytes": 67_108_864,
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "rich_content_lowering": False,
    "formula_generation_or_propagation": False,
    "native_series_index_mapping": False,
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
    "crates/domain-ir/src/table_auto_fill.rs": (
        'TABLE_AUTO_FILL_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill/v1"',
        'TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill-series/v1"',
        'TABLE_AUTO_FILL_CAPABILITY_ID: &str = "table.auto_fill"',
        'TABLE_AUTO_FILL_SERIES_CAPABILITY_ID: &str = "table.auto_fill_series"',
        "pub struct TableAutoFillSeries",
        "pub struct TableAutoFillRequest",
        "pub struct TableAutoFillMutation",
        "pub struct TableAutoFillReceipt",
        "pub struct TableAutoFillPlan",
        "pub struct TableAutoFillBuilder",
        "fn generate_number",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_auto_fill;",
        "TableAutoFillBuilder",
        "TableAutoFillSeries",
        "TABLE_AUTO_FILL_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_auto_fill.rs": (
        "explicit_cycle_fills_row_major_and_binds_preserved_cell_state",
        "column_major_order_is_explicit_even_after_coordinate_canonicalization",
        "linear_number_uses_exact_fixed_point_and_canonical_values",
        "linear_date_and_start_index_are_checked_and_deterministic",
        "formula_replacement_requires_an_explicit_bound_policy",
        "merged_region_fails_before_a_fill_plan_exists",
        "series_and_cell_bindings_fail_closed",
        "value_series_selection_and_work_limits_are_finite",
        "mixed_scale_first_value_normalizes_before_i64_admission",
        "numeric_date_and_index_overflow_return_no_partial_plan",
        "strict_series_and_request_json_reject_duplicate_unknown_version_and_size",
        "canonical_series_request_plan_and_receipt_are_repeatable",
        "output_limit_fails_without_returning_a_partial_plan",
        "debug_surfaces_redact_ids_values_indices_and_digests",
        "fixed_seed_cycle_corpus_preserves_exact_sequence_and_styles",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded components implemented; no HWPX or Hangul 2020 oracle claim",
        "custom sequence is represented by its actual values and SHA-256 identity",
        "component_only / unit_passed",
        "reasoning remains `max`",
    ),
    REPORT: (
        "Result: `component_pass`",
        "16/16 PASS",
        "cataloged`: 13 to 11",
        "unit_passed`: 30 to 32",
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
        "schema_version": "hwpx-agent.table-auto-fill-contract/v1",
        "model_schema_versions": {
            "series": "hwpx-agent.table-auto-fill-series/v1",
            "request": "hwpx-agent.table-auto-fill/v1",
        },
        "scope": "p06_09_pure_bounded_table_auto_fill_current_pc_local_development",
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
        "semantics": {"series", "number", "region", "order", "formula", "style"},
        "binding": {"identity", "cells", "mutation", "receipt", "serialization"},
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("series") != (
            "explicit_cycle_exact_linear_number_or_linear_date_days"
        ):
            add_error(errors, "semantics_series")
        if semantics.get("formula") != (
            "reject_or_replace_exactly_bound_existing_formula_without_generation_claim"
        ):
            add_error(errors, "semantics_formula")
        if semantics.get("style") != (
            "preserved_style_sha256_bound_for_every_selected_coordinate"
        ):
            add_error(errors, "semantics_style")

    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 16
        or len(set(failure_policy)) != 16
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
        "hwpx-agent.table-auto-fill-series/v1",
        "hwpx-agent.table-auto-fill/v1",
        "Existing documents",
        "no partial plan",
        "separately versioned",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-auto-fill-validation/v1",
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
        "P06_TABLE_AUTO_FILL_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
