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
CONTRACT = "protocol/private/p06-table-auto-fill-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-auto-fill-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_AUTO_FILL_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_AUTO_FILL_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-auto-fill-v1.json",
}
EXPECTED_FEATURES = {
    "TABLE-057": "table.auto_fill",
    "TABLE-058": "table.auto_fill_series",
}
EXPECTED_EVIDENCE = {
    "adapter_tests": 8,
    "feature_count": 2,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "validations": ["formula_readback", "page_split", "schema", "semantic_reopen"],
}
EXPECTED_NOT_CLAIMED = {
    "render_diff": False,
    "hangul_2020_target_build": False,
    "saved_real_hwpx": False,
    "automation_runtime": False,
    "differential_exact_match": False,
    "rollback_or_retry": False,
    "release_enabled": False,
    "formula_recalculation": False,
    "source_date_type_inference": False,
    "rich_content_or_merged_fill": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_auto_fill.rs": (
        'TABLE_AUTO_FILL_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill/v1"',
        'TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill-series/v1"',
        "pub fn value_at",
        "pub struct TableAutoFillBuilder",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/auto_fill_hwpx.rs": (
        'TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill-hwpx/v1"',
        '"hwpx-agent.table-auto-fill-hwpx.hancom-2020-single-run/1"',
        "pub struct TableAutoFillHwpxRequest",
        "pub struct TableAutoFillHwpxPlan",
        "pub struct TableAutoFillHwpxLoweringReceipt",
        "pub fn lower",
        "fn validate_request_source",
        "fn target_state",
        "fn formula_references_any",
        "UnsupportedFormulaDependency",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod auto_fill_hwpx;",
        "pub use auto_fill_hwpx",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_AUTO_FILL_HWPX_PROFILE_ID",
        "TableAutoFillHwpxReader",
        "TableAutoFillHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_auto_fill_hwpx.rs": (
        "explicit_cycle_rewrites_only_selected_runs_and_preserves_styles_pagination_and_caption",
        "column_major_numbers_and_extended_dates_follow_exact_series_order",
        "replace_bound_clears_exact_formula_while_reject_and_unselected_formula_fail_or_preserve",
        "request_rejects_source_series_payload_flow_and_json_tamper",
        "builder_and_lowerer_recheck_source_flow_series_and_plan_binding",
        "merged_multi_paragraph_multi_run_and_inline_style_fail_closed",
        "noop_is_byte_exact_for_target_typed_text_collision_and_debug_is_redacted",
        "closed_package_reopens_and_preserves_every_non_target_part",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "any finite nonempty rectangular region",
        "stale cache",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "8/8 PASS",
        "unit_passed`: 8 to 6",
        "integration_passed`: 38 to 40",
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
        "classification",
        "transformation",
        "lowering",
        "preservation",
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
        "schema_version": "hwpx-agent.table-auto-fill-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-auto-fill-hwpx.hancom-2020-single-run/1",
        "model_profile_id": "hwpx-agent.table-auto-fill/v1",
        "scope": (
            "p06_09_static_current_pc_hancom_2020_hwpx_complete_"
            "single_run_auto_fill_admission"
        ),
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableAutoFillLimits",
            "TableRulingHwpxLimits",
            "TableLayoutHwpxLimits",
            "ParagraphStyleLimits",
            "TableFormulaHwpxLimits",
            "FormulaLimits",
            "TableGridLimits",
            "TableRulingLimits",
            "TablePaginationHwpxLimits",
            "TextFlowLimits",
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
        "input": {"table", "source", "series", "profile"},
        "classification": {"blank", "boolean", "numeric", "date", "text"},
        "transformation": {"fill", "edit", "formula", "identity", "fixed"},
        "lowering": {"precondition", "edit_scope", "binding", "publication"},
        "preservation": {"payload", "properties", "document", "noop", "source"},
        "receipt": {"binding", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        (
            "input",
            "profile",
            "merge_free_rectangular_region_with_one_exact_plain_or_native_formula_run_per_cell",
            "input_profile",
        ),
        (
            "classification",
            "date",
            "generated_series_dates_render_as_exact_proleptic_gregorian_iso_8601_without_source_date_inference",
            "classification_date",
        ),
        (
            "transformation",
            "edit",
            "rewrite_only_selected_run_content_while_preserving_paragraph_run_and_cell_style_envelopes",
            "fill_edit",
        ),
        (
            "transformation",
            "formula",
            "reject_or_replace_selected_exact_native_formula_and_reject_stale_unselected_formula_dependencies",
            "fill_formula",
        ),
        (
            "transformation",
            "fixed",
            "preserve_grid_edges_master_cells_properties_unselected_payloads_pagination_caption_and_table_count",
            "fill_fixed",
        ),
        (
            "lowering",
            "precondition",
            "relift_source_reclassify_scalars_recompute_payload_formula_style_digests_rebuild_domain_plan_and_compare_parts_state_grid_pagination_series_flow",
            "lowering_precondition",
        ),
        (
            "lowering",
            "publication",
            "return_only_after_full_adapter_reparse_exact_target_state_grid_scalar_formula_pagination_and_table_count_readback",
            "lowering_publication",
        ),
        (
            "preservation",
            "noop",
            "original_header_section_bytes_payload_identity_and_document_flow",
            "preservation_noop",
        ),
        (
            "receipt",
            "debug",
            "all_hashes_logical_ids_text_series_values_payloads_formulas_raw_xml_and_document_content_omitted",
            "receipt_debug",
        ),
    )
    for group, key, expected, code in checks:
        value = contract.get(group)
        if not isinstance(value, dict) or value.get(key) != expected:
            add_error(errors, code)

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
            text = bounded_file(root, relative, 4_000_000).read_text(encoding="utf-8")
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
        "hwpx-agent.table-auto-fill-hwpx.hancom-2020-single-run/1",
        "independently rebuilds the domain fill plan",
        "fails closed",
        "Existing documents are not rewritten in place",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-auto-fill-hwpx-validation/v1",
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
        "P06_TABLE_AUTO_FILL_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
