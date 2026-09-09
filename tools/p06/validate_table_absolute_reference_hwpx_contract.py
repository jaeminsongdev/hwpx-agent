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
CONTRACT = "protocol/private/p06-table-absolute-reference-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-absolute-reference-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_ABSOLUTE_REFERENCE_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_ABSOLUTE_REFERENCE_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-formula-v1.json",
}
EXPECTED_FEATURES = {"TABLE-060": "table.formula_absolute_ref"}
EXPECTED_EVIDENCE = {
    "adapter_tests": 8,
    "feature_count": 1,
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
    "verified_formula_cache": False,
    "non_general_number_format": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_formula.rs": (
        'TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID: &str =',
        "pub fn read_canonical_cell_in_section",
        "pub fn lower_canonical_cell_in_section_with_receipt",
        "fn canonical_native_ast",
        "fn expression_has_absolute_axis",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/formula_reference_hwpx.rs": (
        'TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION: &str =',
        '"hwpx-agent.table-absolute-reference-hwpx.hancom-2020-canonical-field/1"',
        'TABLE_ABSOLUTE_REFERENCE_CAPABILITY_ID: &str = "table.formula_absolute_ref"',
        "pub struct TableAbsoluteReferenceHwpxRequest",
        "pub struct TableAbsoluteReferenceHwpxPlan",
        "pub struct TableAbsoluteReferenceHwpxLoweringReceipt",
        "fn validate_transition",
        "fn reference_upgrade_count",
        "UnsupportedRecalculate",
        "PreservationMismatch",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod formula_reference_hwpx;",
        "pub use formula_reference_hwpx",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID",
        "TableAbsoluteReferenceHwpxReader",
        "TableAbsoluteReferenceHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_absolute_reference_hwpx.rs": (
        "upgrades_independent_axes_and_preserves_other_formula_pagination_and_caption",
        "recursive_formula_grammar_and_update_or_clear_cache_round_trip",
        "invalid_anchor_coordinate_operator_cache_and_recalculate_fail_closed",
        "request_json_and_every_source_binding_fail_closed_on_tamper",
        "builder_and_lowerer_repeat_source_flow_and_plan_checks",
        "selected_owner_native_shape_and_finite_limits_are_exact",
        "already_absolute_noop_is_byte_exact_and_debug_is_redacted",
        "closed_package_graph_and_every_non_target_part_are_preserved",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 target claim",
        "complete bounded locale-neutral `FormulaAst` grammar",
        "Each reference axis may remain unchanged or move from `relative` to",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "8/8 PASS",
        "unit_passed`: 6 to 5",
        "integration_passed`: 40 to 41",
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
        "schema_version": "hwpx-agent.table-absolute-reference-hwpx-contract/v1",
        "profile_id": (
            "hwpx-agent.table-absolute-reference-hwpx."
            "hancom-2020-canonical-field/1"
        ),
        "model_profile_id": "hwpx-agent.table-formula/v1",
        "scope": (
            "p06_09_static_current_pc_hancom_2020_hwpx_complete_"
            "absolute_reference_admission"
        ),
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "FormulaLimits",
            "TableFormulaHwpxLimits",
            "TableLayoutHwpxLimits",
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
        "input": {"selector", "source", "target", "profile"},
        "transformation": {"formula", "anchors", "cache", "other_formulas", "noop"},
        "lowering": {"precondition", "edit_scope", "fixed", "publication"},
        "preservation": {"selected", "table", "document", "source"},
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
            "canonical_general_format_formula_field_with_zero_or_more_other_formula_fields",
            "input_profile",
        ),
        (
            "transformation",
            "formula",
            "preserve_literals_operators_functions_arguments_ranges_and_coordinates_while_only_upgrading_relative_axes_to_absolute",
            "transition_formula",
        ),
        (
            "transformation",
            "cache",
            "preserve_exact_update_with_bound_unverified_decimal_or_clear_to_absent_without_recalculation",
            "transition_cache",
        ),
        (
            "transformation",
            "other_formulas",
            "opaque_unowned_bytes_preserved_without_reinterpretation",
            "other_formulas",
        ),
        (
            "lowering",
            "precondition",
            "relift_source_recompute_every_digest_validate_reference_only_transition_and_rebuild_plan",
            "lowering_precondition",
        ),
        (
            "lowering",
            "edit_scope",
            "selected_formula_command_formula_last_result_and_visible_result_text_spans_only",
            "lowering_edit_scope",
        ),
        (
            "lowering",
            "publication",
            "return_only_after_target_formula_cache_unowned_bytes_pagination_counts_and_header_reopen_exactly",
            "lowering_publication",
        ),
        (
            "preservation",
            "document",
            "header_page_split_repeat_headers_caption_table_count_package_graph_and_non_target_parts",
            "preservation_document",
        ),
        (
            "receipt",
            "debug",
            "all_formulas_cache_values_hashes_native_text_and_document_content_omitted",
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
        "hwpx-agent.table-absolute-reference-hwpx.hancom-2020-canonical-field/1",
        "only relative axes become absolute",
        "Existing documents are not rewritten in place",
        "may not promote",
        "fail closed",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-absolute-reference-hwpx-validation/v1",
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
        "P06_TABLE_ABSOLUTE_REFERENCE_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
