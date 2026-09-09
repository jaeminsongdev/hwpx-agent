#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from tools.p06.validate_table_geometry_contract import (
        add_error,
        bounded_file,
        canonical_sha256,
        reject_duplicate_keys,
    )
except ModuleNotFoundError:
    from validate_table_geometry_contract import (  # type: ignore[no-redef]
        add_error,
        bounded_file,
        canonical_sha256,
        reject_duplicate_keys,
    )


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-aggregate-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-aggregate-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_AGGREGATE_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_AGGREGATE_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-aggregate-v1.json",
    "protocol/private/p06-table-ruling-v1.json",
    "protocol/private/p06-table-pagination-target-v2.json",
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
    "domain_tests": 8,
    "adapter_tests": 4,
    "axis_function_combinations": 9,
    "contract_tests": 4,
    "feature_count": 8,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "fixture_classes": ["boundary", "happy_path", "negative", "preservation", "security"],
    "validations": ["formula_readback", "page_split", "schema", "semantic_reopen"],
}
EXPECTED_NOT_CLAIMED = {
    "formula_evaluation_or_verified_cache": False,
    "saved_real_hwpx": False,
    "hangul_2020_target_build": False,
    "render_diff": False,
    "rollback_or_retry": False,
    "automation_runtime": False,
    "differential_exact_match": False,
    "release_enabled": False,
    "arbitrary_user_document_compatibility": False,
    "merged_or_existing_formula_source": False,
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
        "pub struct TableAggregateBuilder",
        "pub struct TableAggregatePlan",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/aggregate_hwpx.rs": (
        'TABLE_AGGREGATE_HWPX_SCHEMA_VERSION: &str =',
        'TABLE_AGGREGATE_HWPX_PROFILE_ID: &str =',
        "pub struct TableAggregateHwpxReadback",
        "pub struct TableAggregateHwpxRequestDraft",
        "pub struct TableAggregateHwpxPlan",
        "pub struct TableAggregateHwpxLoweringReceipt",
        "pub fn lower_existing(",
        "fn validate_request_source(",
        "fn state_with_formula(",
        "fn same_pagination_semantics(",
        "fn reject_duplicate_json_keys(",
    ),
    "crates/hwpx-package/src/table_formula.rs": (
        "TABLE_AGGREGATE_FORMULA_HWPX_PROFILE_ID",
        "pub(crate) fn read_aggregate_in_section(",
        "pub(crate) fn insert_aggregate_in_section(",
        "fn aggregate_native_formula(",
        "fn empty_cell_run(",
        "fn reserve_field_ids(",
        "fn aggregate_field_xml(",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod aggregate_hwpx;",
        "TableAggregateHwpxBuilder",
        "read_existing_aggregate_preserving_caption",
        "aggregate_formula: bool",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_AGGREGATE_HWPX_PROFILE_ID",
        "TableAggregateHwpxReader",
        "TableAggregateHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_aggregate_hwpx.rs": (
        "all_nine_axis_function_mappings_lower_and_preserve_complete_state",
        "merged_nonempty_and_existing_formula_sources_fail_closed",
        "source_flow_plan_json_native_shape_and_debug_tampering_fail_closed",
        "closed_package_reopen_preserves_every_unselected_part",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "not a function-by-function easy subset",
        "direct_hwpx / integration_passed",
        "unit_passed` from 21 to 13",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "8/8 PASS",
        "4/4 PASS",
        "9/9 static lower/reopen PASS",
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
        "schema_version", "profile_id", "model_profile_ids", "scope", "features",
        "compatibility_regression", "source_lock_canonicalization", "source_locks",
        "input", "transition", "binding", "preservation", "native_profile", "receipt",
        "limits_profiles", "failure_policy", "migration", "policy", "report",
        "expected_evidence", "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-aggregate-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-aggregate-hwpx.hancom-2020-wrapper/1",
        "model_profile_ids": {
            "aggregate": "hwpx-agent.table-aggregate/v1",
            "formula": "hwpx-agent.table-formula/v1",
            "ruling": "hwpx-agent.table-ruling/v1",
            "pagination": "hwpx-agent.table-pagination-hwpx.hancom-2020/1",
        },
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_exact_aggregate_formula_admission",
        "features": EXPECTED_FEATURES,
        "compatibility_regression": {"TABLE-025": "table.horizontal_sum"},
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableLayoutHwpxLimits", "ParagraphStyleLimits", "TableFormulaHwpxLimits",
            "FormulaLimits", "TableGridLimits", "TableRulingLimits",
            "TablePaginationHwpxLimits",
        ],
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
        "input": {"existing_table", "operation", "destination"},
        "transition": {"formula", "cache", "native_field"},
        "binding": {"request", "build", "lower", "publication"},
        "preservation": {"grid", "payload_properties_edges", "pagination", "package"},
        "native_profile": {"source", "formula", "cache", "destination", "public_formula_boundary"},
        "receipt": {"hashes", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        ("transition", "formula", "derive_one_relative_A1_SUM_AVG_or_PRODUCT_range_from_the_typed_aggregate_request", "formula_transition"),
        ("transition", "cache", "replace_domain_absent_cache_only_with_caller_explicit_unverified_decimal_display_value", "cache_transition"),
        ("binding", "publication", "return_only_after_exact_target_state_grid_formula_cache_pagination_caption_flow_and_package_part_reopen", "publication"),
        ("preservation", "payload_properties_edges", "all_non_destination_ordered_payloads_complete_cell_and_table_properties_and_unit_edges_remain_exact", "complete_preservation"),
        ("preservation", "package", "source_never_mutated_header_binding_siblings_spine_and_every_non_target_package_part_byte_identical", "package_preservation"),
        ("native_profile", "source", "formula_free_unmerged_exact_current_Hangul_2020_table_wrapper", "source_profile"),
        ("native_profile", "public_formula_boundary", "legacy_public_reader_and_lowerer_remain_SUM_LEFT_only", "public_formula_boundary"),
        ("receipt", "debug", "all_hashes_ids_payloads_formulas_cache_caption_content_and_raw_XML_omitted", "receipt_debug"),
    )
    for group, field, expected, code in checks:
        value = contract.get(group)
        if not isinstance(value, dict) or value.get(field) != expected:
            add_error(errors, code)

    locks = contract.get("source_locks")
    declared: dict[str, str] = {}
    if not isinstance(locks, list):
        add_error(errors, "source_locks_shape")
        locks = []
    for item in locks:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            add_error(errors, "source_lock_shape")
            continue
        path = item.get("path")
        expected = item.get("sha256")
        if not isinstance(path, str) or path in declared or not isinstance(expected, str):
            add_error(errors, "source_lock_identity")
            continue
        declared[path] = expected
        try:
            if canonical_sha256(bounded_file(root, path, 4_000_000)) != expected:
                add_error(errors, "source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path")
    if set(declared) != EXPECTED_SOURCE_PATHS:
        add_error(errors, "source_lock_paths_exact")

    for path, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, path, 4_000_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "implementation_path")
            continue
        if any(marker not in text for marker in markers):
            add_error(errors, "implementation_marker")

    try:
        migration = bounded_file(root, MIGRATION, 128_000).read_text(encoding="utf-8")
        for marker in (
            "Before this profile",
            "formula-free unmerged source",
            "may not promote",
            "licensed Hangul 2020",
        ):
            if marker not in migration:
                add_error(errors, "migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "migration_path")

    return result(errors, len(declared), len(IMPLEMENTATION_MARKERS))


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-aggregate-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 8,
        "direct_stage": "integration_passed" if not unique else "not_proven",
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
        "P06_TABLE_AGGREGATE_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
