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
CONTRACT = "protocol/private/p06-table-properties-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-properties-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_PROPERTIES_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_PROPERTIES_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-properties-v1.json",
}
EXPECTED_FEATURES = {
    "TABLE-007": "table.properties",
    "TABLE-008": "table.cell_properties",
    "TABLE-009": "table.border_fill",
    "TABLE-047": "table.diagonal",
}
EXPECTED_EVIDENCE = {
    "adapter_tests": 12,
    "feature_count": 4,
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
    "independent_cell_spacing_lowering": False,
    "multiple_formula_native_profile": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_properties.rs": (
        'TABLE_PROPERTIES_SCHEMA_VERSION: &str = "hwpx-agent.table-properties/v1"',
        "pub struct TablePropertyRegion",
        "pub fn table_diagonal_identity_sha256",
        "pub enum TablePropertiesOperation",
        "expected_state_sha256: String",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/properties_hwpx.rs": (
        'TABLE_PROPERTIES_HWPX_PROFILE_ID: &str =',
        "pub struct TablePropertiesHwpxBinding",
        "pub struct TablePropertiesHwpxValueCatalog",
        "pub struct TablePropertiesHwpxReadback",
        "pub struct TablePropertiesHwpxLoweringReceipt",
        "pub fn lower_existing",
        "fn validate_part_binding",
        "fn validate_catalog_bounds",
        "fn validate_cell_value",
        "MissingDiagonalBinding",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod properties_hwpx;",
        "pub use properties_hwpx",
        "TablePropertiesHwpxReader",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_PROPERTIES_HWPX_PROFILE_ID",
        "TablePropertiesHwpxReader",
        "TablePropertiesHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_properties_hwpx.rs": (
        "reader_lifts_complete_typed_state_and_redacts_debug",
        "each_cell_borders_background_and_formula_round_trip",
        "unified_border_resolves_outer_and_inner_roles_on_merged_grid",
        "diagonal_each_unified_and_clear_keep_explicit_logical_bindings",
        "typed_table_and_cell_property_catalogs_lower_without_raw_xml",
        "unused_typed_catalog_values_are_prevalidated_and_debug_is_redacted",
        "closed_package_preserves_unselected_table_formula_pagination_and_other_parts",
        "part_state_flow_and_catalog_drift_fail_closed",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "Every supplied value is prevalidated",
        "does not expose it as an",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "12/12 PASS",
        "unit_passed`: 34 to 30",
        "integration_passed`: 12 to 16",
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
        "schema_version", "profile_id", "model_profile_id", "scope", "features",
        "source_lock_canonicalization", "source_locks", "input", "native_mapping",
        "lowering", "preservation", "representability", "receipt", "limits_profiles",
        "failure_policy", "migration", "policy", "report", "expected_evidence",
        "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-properties-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-properties-hwpx.hancom-2020/1",
        "model_profile_id": "hwpx-agent.table-properties/v1",
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_table_properties_admission",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableLayoutHwpxLimits", "ParagraphStyleLimits", "TableCellStyleLimits",
            "TableFormulaHwpxLimits", "FormulaLimits", "TableGridLimits",
            "TablePropertiesLimits",
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
        "input": {"existing_table", "source_binding", "typed_values", "profile"},
        "native_mapping": {
            "table_properties", "cell_properties", "borders_background", "diagonals",
            "payload_formula", "canonical_values",
        },
        "lowering": {"precondition", "edit_scope", "catalog", "publication"},
        "preservation": {
            "payload_order", "formula", "geometry", "unselected_section",
            "non_section_parts", "package_rebuild", "source",
        },
        "representability": {
            "diagonal_provenance", "formula_profile", "cell_spacing", "typed_catalog",
        },
        "receipt": {"profile", "binding", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        ("native_mapping", "table_properties", "hp_tbl_lock_borderFillIDRef_noAdjust", "native_table_properties"),
        ("native_mapping", "cell_properties", "hp_tc_cellMargin_protect_editable_and_hp_subList_textDirection_vertAlign_paraPrIDRef", "native_cell_properties"),
        ("lowering", "precondition", "relift_exact_source_state_grid_then_verify_plan_before_after_state_grid_parts_and_document_flow", "lowering_precondition"),
        ("lowering", "publication", "return_only_after_header_section_reparse_and_exact_target_state_grid_readback", "lowering_publication"),
        ("preservation", "formula", "exact_supported_ast_display_cache_and_owner_identity", "preservation_formula"),
        ("preservation", "geometry", "exact_grid_cell_extents_table_cell_spacing_and_unselected_pagination_semantics", "preservation_geometry"),
        ("representability", "diagonal_provenance", "native_hwpx_does_not_preserve_each_cell_vs_unified_intent_so_every_visible_diagonal_requires_exact_binding", "representability_diagonal"),
        ("representability", "cell_spacing", "geometry_coupled_and_preserved_not_exposed_as_an_independent_property_value", "representability_cell_spacing"),
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
        "hwpx-agent.table-properties-hwpx.hancom-2020/1",
        "Every supplied catalog value is checked",
        "Existing documents are not rewritten in place",
        "remains fail closed",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-properties-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 4,
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
        "P06_TABLE_PROPERTIES_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
