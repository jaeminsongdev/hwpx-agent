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
CONTRACT = "protocol/private/p06-table-nested-table-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-nested-table-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_NESTED_TABLE_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_NESTED_TABLE_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-ruling-v1.json",
    "protocol/private/p06-table-inspection-v1.json",
}
EXPECTED_FEATURES = {"TABLE-054": "table.nested_table"}
EXPECTED_EVIDENCE = {
    "adapter_tests": 7,
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
    "arbitrary_external_resources": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_formula.rs": (
        "fn nearest_ancestor_table(",
        "nearest_ancestor_table(document, index)? != Some(table)",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod nested_table_hwpx;",
        "pub use nested_table_hwpx::{",
        "fn is_payload_paragraph(",
        "nearest_ancestor_table(document, index)? == Some(table)",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/nested_table_hwpx.rs": (
        'TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION: &str =',
        '"hwpx-agent.table-nested-table-hwpx.hancom-2020-inline-template/1"',
        'TABLE_NESTED_TABLE_CAPABILITY_ID: &str = "table.nested_table"',
        "pub struct TableNestedTableHwpxRequest",
        "pub struct TableNestedTableHwpxPlan",
        "pub struct TableNestedTableHwpxLoweringReceipt",
        "fn state_with_inserted_payload",
        "fn ensure_template_native_identity_available",
        "fn validate_template_payload_profile",
        "fn same_pagination_policy",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_NESTED_TABLE_HWPX_PROFILE_ID",
        "TableNestedTableHwpxReader",
        "TableNestedTableHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_nested_table_hwpx.rs": (
        "inserts_complete_nested_table_and_reopens_parent_payload_formula_and_pagination",
        "covered_merged_cell_and_non_inline_template_fail_closed",
        "request_rejects_all_bound_drift_duplicate_unknown_and_identity_tampering",
        "lowerer_rechecks_source_template_current_flow_and_foreign_plan",
        "native_table_and_formula_identity_collisions_fail_before_mutation",
        "input_is_bounded_and_debug_redacts_ids_hashes_and_formula_content",
        "closed_package_reopen_preserves_all_nontarget_parts_and_nested_state",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 target claim",
        "complete typed grid",
        "Formula ownership is the nearest ancestor table",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "7/7 PASS",
        "unit_passed`: 5 to 4",
        "integration_passed`: 41 to 42",
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
        "schema_version": "hwpx-agent.table-nested-table-hwpx-contract/v1",
        "profile_id": (
            "hwpx-agent.table-nested-table-hwpx."
            "hancom-2020-inline-template/1"
        ),
        "model_profile_id": "hwpx-agent.table-ruling/v1",
        "scope": (
            "p06_09_static_current_pc_hancom_2020_hwpx_complete_"
            "nested_table_admission"
        ),
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableRulingHwpxLimits",
            "TableGridLimits",
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
        "input": {"selector", "source", "template", "target"},
        "transformation": {"insertion", "parent", "nested", "formula_scope", "identities"},
        "lowering": {"precondition", "edit_scope", "fixed", "publication"},
        "preservation": {"parent", "nested", "document", "source"},
        "receipt": {"binding", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        (
            "input",
            "selector",
            "exact_parent_table_ordinal_master_cell_coordinate_and_direct_empty_paragraph_ordinal",
            "input_selector",
        ),
        (
            "input",
            "template",
            "caption_free_inline_resource_free_wrapper_with_complete_grid_edges_cell_payload_properties_formula_cache_pagination_and_placement_state",
            "input_template",
        ),
        (
            "transformation",
            "parent",
            "preserve_grid_spans_edges_properties_formulas_cache_pagination_and_all_payload_order_while_inserting_one_typed_payload_identity",
            "transition_parent",
        ),
        (
            "transformation",
            "nested",
            "preserve_complete_template_grid_spans_edges_properties_text_payload_formula_cache_pagination_and_inline_placement",
            "transition_nested",
        ),
        (
            "transformation",
            "formula_scope",
            "nearest_table_ownership_excludes_nested_formula_fields_from_parent_formula_state",
            "formula_scope",
        ),
        (
            "lowering",
            "precondition",
            "relift_source_and_template_recompute_every_digest_recheck_native_and_logical_identities_and_rebuild_plan",
            "lowering_precondition",
        ),
        (
            "lowering",
            "edit_scope",
            "one_exact_empty_direct_parent_cell_paragraph_span_only",
            "lowering_edit_scope",
        ),
        (
            "lowering",
            "publication",
            "return_only_after_parent_nested_formula_pagination_placement_table_count_package_and_non_target_part_reopen_exactly",
            "lowering_publication",
        ),
        (
            "preservation",
            "document",
            "header_package_graph_compression_classes_and_every_non_target_part",
            "preservation_document",
        ),
        (
            "receipt",
            "debug",
            "all_logical_ids_hashes_formula_cache_native_text_and_document_content_omitted",
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
        "hwpx-agent.table-nested-table-hwpx.hancom-2020-inline-template/1",
        "Nearest-table formula ownership",
        "Existing documents are not rewritten in place",
        "may not promote",
        "fail closed",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-nested-table-hwpx-validation/v1",
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
        "P06_TABLE_NESTED_TABLE_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
