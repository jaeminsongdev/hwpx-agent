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
CONTRACT = "protocol/private/p06-table-style-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-style-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_STYLE_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_STYLE_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-style-transpose-v1.json",
}
EXPECTED_FEATURES = {"TABLE-020": "table.table_style"}
EXPECTED_EVIDENCE = {
    "adapter_tests": 4,
    "feature_count": 1,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "validations": ["formula_readback", "page_split", "schema", "semantic_reopen"],
}
EXPECTED_NOT_CLAIMED = {
    "render_diff": False,
    "hangul_2020_target_build": False,
    "automation_runtime": False,
    "differential_exact_match": False,
    "rollback_or_retry": False,
    "release_enabled": False,
    "arbitrary_user_document_compatibility": False,
    "multiple_formula_native_profile": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_style.rs": (
        'TABLE_STYLE_SCHEMA_VERSION: &str = "hwpx-agent.table-style/v1"',
        "pub fn grid_sha256",
        "pub fn style_definition_sha256",
        "pub struct TableStylePlan",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/style_hwpx.rs": (
        'TABLE_STYLE_HWPX_PROFILE_ID: &str =',
        "pub struct TableStyleHwpxCellValue",
        "pub struct TableStyleHwpxPartBinding",
        "pub struct TableStyleHwpxLoweringReceipt",
        "pub fn lower_existing",
        "fn validate_request_source",
        "fn build_target_diagonal_binding",
        "fn validate_value_catalog",
        "normalized_unified_diagonal_cell_count",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/properties_hwpx.rs": (
        "pub(super) fn read_existing",
        "pub(super) fn render",
        "pub(super) struct ValueMaps",
        "pub(super) fn validate_catalog_bounds",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod style_hwpx;",
        "pub use style_hwpx",
        "TableStyleHwpxReader",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_STYLE_HWPX_PROFILE_ID",
        "TableStyleHwpxReader",
        "TableStyleHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_properties_hwpx.rs": (
        "table_style_full_regions_round_trip_table_cells_formula_and_pagination",
        "table_style_breaks_only_untruthful_unified_diagonal_groups",
        "table_style_part_state_plan_and_complete_catalog_drift_fail_closed",
        "table_style_closed_package_preserves_other_table_and_non_section_parts",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "Every definition rule must resolve",
        "truthful existing unified binding",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "4/4 PASS",
        "unit_passed`: 30 to 29",
        "integration_passed`: 16 to 17",
        "green rows: remains 0/61",
        "No user document",
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
        "source_lock_canonicalization", "source_locks", "input", "style_identity",
        "lowering", "diagonal_provenance", "preservation", "receipt",
        "limits_profiles", "failure_policy", "migration", "policy", "report",
        "expected_evidence", "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-style-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-style-hwpx.hancom-2020/1",
        "model_profile_ids": {
            "definition": "hwpx-agent.table-style-definition/v1",
            "request": "hwpx-agent.table-style/v1",
        },
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_complete_table_style_admission",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableLayoutHwpxLimits", "ParagraphStyleLimits", "TableCellStyleLimits",
            "TableFormulaHwpxLimits", "FormulaLimits", "TableGridLimits",
            "TablePropertiesLimits", "TableStyleLimits",
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
        "input": {"existing_table", "style_plan", "typed_values", "profile"},
        "style_identity": {"table", "cell", "diagonal", "regions"},
        "lowering": {"precondition", "edit_scope", "catalog", "publication"},
        "diagonal_provenance": {"preserve", "normalize", "new_value", "readback"},
        "preservation": {
            "payload", "formula", "geometry", "unselected_section", "non_section_parts",
            "source",
        },
        "receipt": {"binding", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        ("style_identity", "cell", "typed_non_border_four_directional_border_background_and_visible_diagonal_semantic_sha256", "cell_identity"),
        ("style_identity", "diagonal", "reusable_visual_value_separate_from_exact_each_cell_or_unified_application_provenance", "diagonal_identity"),
        ("lowering", "precondition", "relift_exact_source_style_state_then_rebuild_and_compare_definition_request_plan_parts_grid_and_document_flow", "lowering_precondition"),
        ("lowering", "publication", "return_only_after_header_section_reparse_and_exact_target_style_property_grid_formula_and_payload_readback", "lowering_publication"),
        ("diagonal_provenance", "preserve", "keep_truthful_unified_binding_only_when_every_member_retains_the_same_visual_diagonal", "diagonal_preserve"),
        ("diagonal_provenance", "normalize", "if_any_member_changes_convert_every_remaining_visible_member_of_that_group_to_exact_each_cell_binding", "diagonal_normalize"),
        ("preservation", "formula", "exact_supported_owner_ast_number_format_display_cache_and_formula_sha256", "preservation_formula"),
        ("preservation", "geometry", "exact_grid_spans_cell_extents_table_spacing_and_pagination_attributes", "preservation_geometry"),
        ("receipt", "debug", "all_hashes_logical_ids_paragraph_property_ids_payloads_formulas_cache_and_raw_xml_omitted", "receipt_debug"),
    )
    for group, key, expected, code in checks:
        value = contract.get(group)
        if not isinstance(value, dict) or value.get(key) != expected:
            add_error(errors, code)

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
            not isinstance(path, str) or path in declared or not isinstance(digest, str)
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
            text = bounded_file(root, relative, 3_000_000).read_text(encoding="utf-8")
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
        "hwpx-agent.table-style-hwpx.hancom-2020/1",
        "rebuilds the domain plan",
        "normalized to an explicit",
        "existing documents are not rewritten in place",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-style-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 1,
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
        "P06_TABLE_STYLE_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
