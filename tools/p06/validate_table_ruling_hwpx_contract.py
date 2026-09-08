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
CONTRACT = "protocol/private/p06-table-ruling-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-ruling-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_RULING_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_RULING_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-ruling-v1.json",
}
EXPECTED_FEATURES = {
    "TABLE-002": "table.draw",
    "TABLE-003": "table.eraser",
}
EXPECTED_EVIDENCE = {
    "adapter_tests": 15,
    "feature_count": 2,
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
    "structural_formula_native_lowering": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_ruling.rs": (
        'TABLE_RULING_SCHEMA_VERSION: &str = "hwpx-agent.table-ruling/v1"',
        "pub enum TableRulingOperation",
        "DrawOuterRectangle",
        "pub fn before_state_sha256",
        "pub fn document_flow_sha256",
        "pub fn insertion_context_sha256",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        'TABLE_RULING_HWPX_PROFILE_ID: &str =',
        "pub struct TableRulingHwpxBinding",
        "pub struct TableRulingHwpxReadback",
        "pub struct TableRulingHwpxLoweringReceipt",
        "pub fn outer_insertion_context_sha256",
        "pub fn lower_outer_rectangle",
        "pub fn lower_existing",
        "fn validate_outer_plan",
        "fn ensure_native_table_id_available",
        "UnsupportedFormulaMutation",
        "NonUniformCellSide",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "mod table_ruling_hwpx;",
        "TABLE_RULING_HWPX_PROFILE_ID",
        "TableRulingHwpxReader",
        "TableRulingHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_ruling_hwpx.rs": (
        "outer_rectangle_replaces_exact_empty_paragraph_and_reopens_target",
        "lifts_complete_edges_payloads_properties_and_physical_state",
        "bindings_extents_payloads_and_shared_edges_fail_closed",
        "structural_eraser_merges_rows_and_preserves_payload_order",
        "draw_split_creates_empty_cell_and_diagonal_uses_reviewed_header_identity",
        "nonstructural_eraser_synthesizes_and_deduplicates_one_border_fill",
        "lowerer_rejects_source_state_grid_and_missing_line_drift",
        "nonuniform_native_cell_side_fails_closed",
        "incompatible_dual_diagonal_lines_fail_closed",
        "full_row_then_column_draw_refines_native_lattice_without_losing_payload",
        "line_only_edit_preserves_formula_and_structural_formula_change_fails_closed",
        "closed_package_reopen_preserves_formula_pagination_and_unselected_parts",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "never treats an existing table as absent",
        "UnsupportedFormulaMutation",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "15/15 PASS",
        "unit_passed`: 36 to 34",
        "integration_passed`: 10 to 12",
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
        "schema_version",
        "profile_id",
        "model_profile_id",
        "scope",
        "features",
        "source_lock_canonicalization",
        "source_locks",
        "input",
        "native_mapping",
        "lowering",
        "preservation",
        "representability",
        "receipt",
        "limits_profiles",
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
        "schema_version": "hwpx-agent.table-ruling-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-ruling-hwpx.hancom-2020/1",
        "model_profile_id": "hwpx-agent.table-ruling/v1",
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_table_ruling_admission",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableLayoutHwpxLimits",
            "ParagraphStyleLimits",
            "TableFormulaHwpxLimits",
            "FormulaLimits",
            "TableGridLimits",
            "TableRulingLimits",
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
        "input": {"existing_table", "outer_rectangle", "source_binding", "profile"},
        "native_mapping": {
            "grid_topology",
            "edges",
            "diagonals",
            "outer_creation",
            "payload_formula",
            "canonical_values",
        },
        "lowering": {
            "existing_precondition",
            "existing_edit_scope",
            "outer_precondition",
            "publication",
        },
        "preservation": {
            "payload_order",
            "cell_properties",
            "formula",
            "pagination",
            "unselected_section",
            "non_section_parts",
            "package_rebuild",
            "source",
        },
        "representability": {
            "cell_side",
            "diagonal_pair",
            "structural_formula",
            "outer_template",
        },
        "receipt": {"profile", "binding", "counts", "debug"},
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)

    native = contract.get("native_mapping")
    if isinstance(native, dict):
        if native.get("grid_topology") != (
            "hp_tbl_rowCnt_colCnt_hp_tr_hp_tc_cellAddr_cellSpan_cellSz"
        ):
            add_error(errors, "native_grid_topology")
        if native.get("outer_creation") != (
            "replace_one_digest_bound_empty_top_level_hp_p_with_one_reviewed_native_table_wrapper"
        ):
            add_error(errors, "native_outer_creation")
    lowering = contract.get("lowering")
    if isinstance(lowering, dict):
        if lowering.get("existing_precondition") != (
            "relift_exact_source_state_grid_then_verify_plan_before_after_state_grid_and_document_flow"
        ):
            add_error(errors, "lowering_existing_precondition")
        if lowering.get("publication") != (
            "return_only_after_header_section_reparse_and_exact_target_state_grid_readback"
        ):
            add_error(errors, "lowering_publication")
    preservation = contract.get("preservation")
    if isinstance(preservation, dict):
        if preservation.get("formula") != (
            "line_only_exact_ast_cache_bytes_and_structural_formula_mutation_fail_closed"
        ):
            add_error(errors, "preservation_formula")
        if preservation.get("unselected_section") != (
            "byte_identical_outside_selected_table_or_exact_outer_placeholder"
        ):
            add_error(errors, "preservation_unselected_section")
    representability = contract.get("representability")
    if isinstance(representability, dict):
        if representability.get("cell_side") != (
            "one_uniform_line_identity_per_native_master_cell_side_or_fail_closed"
        ):
            add_error(errors, "representability_cell_side")
        if representability.get("structural_formula") != (
            "current_native_formula_profile_rejects_topology_mutation_instead_of_guessing_rebase_or_cache_serialization"
        ):
            add_error(errors, "representability_structural_formula")
    receipt = contract.get("receipt")
    if isinstance(receipt, dict) and receipt.get("debug") != (
        "all_hashes_logical_ids_payloads_formulas_cache_and_raw_xml_omitted"
    ):
        add_error(errors, "receipt_debug")

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
        "hwpx-agent.table-ruling-hwpx.hancom-2020/1",
        "Existing documents are not rewritten in place",
        "instead of synthesizing undocumented defaults",
        "remain fail closed",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-ruling-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 2,
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
        "P06_TABLE_RULING_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
