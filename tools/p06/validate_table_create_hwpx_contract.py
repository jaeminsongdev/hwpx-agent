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
CONTRACT = "protocol/private/p06-table-create-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-create-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_CREATE_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_CREATE_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-operations-v1.json",
}
EXPECTED_FEATURES = {"TABLE-001": "table.create"}
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
    "nonblank_or_merged_initial_table": False,
    "repeat_header_or_caption_creation": False,
    "arbitrary_native_template": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_operations.rs": (
        "pub fn create_unmerged(",
        "TableOperationKind::Create",
        "inserted_master_cell_ids",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/create_hwpx.rs": (
        'TABLE_CREATE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-create-hwpx/v1"',
        '"hwpx-agent.table-create-hwpx.hancom-2020-template/1"',
        "pub struct TableCreateHwpxRequest",
        "pub struct TableCreateHwpxPlan",
        "pub struct TableCreateHwpxLoweringReceipt",
        "pub fn lower_at_placeholder",
        "expected_template_state_sha256",
        "expected_template_grid_sha256",
        "fn validate_request_source",
        "fn require_template_profile",
        "fn require_native_template_wrapper",
        "fn require_native_created_cell_scaffolds",
        "fn created_edges",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod create_hwpx;",
        "pub use create_hwpx",
        "ExistingRenderProfile::Create",
        "render_create_from_template",
        "permits_created_geometry",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_CREATE_HWPX_PROFILE_ID",
        "TableCreateHwpxReader",
        "TableCreateHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_create_hwpx.rs": (
        "creates_arbitrary_rectangular_nonuniform_unmerged_table_and_reopens_exactly",
        "one_by_one_boundary_uses_only_template_outer_edges",
        "request_rejects_part_template_context_flow_identity_track_and_json_tampering",
        "lowerer_rechecks_source_template_current_flow_and_foreign_plan",
        "nonblank_template_and_native_identifier_collision_fail_closed",
        "input_is_bounded_and_debug_omits_ids_hashes_and_content",
        "closed_package_replacement_preserves_every_nontarget_part_and_graph",
        "rejects_control_wrapped_table_template_as_non_native_profile",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "arbitrary nonzero bounded",
        "blank Hancom-2020-shaped 2x2 template",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "8/8 PASS",
        "unit_passed`: 12 to 11",
        "integration_passed`: 34 to 35",
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
        "schema_version": "hwpx-agent.table-create-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-create-hwpx.hancom-2020-template/1",
        "model_profile_id": "hwpx-agent.table-operations/v1",
        "scope": (
            "p06_09_static_current_pc_hancom_2020_hwpx_"
            "complete_blank_unmerged_create_admission"
        ),
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableCreateHwpxLimits",
            "TableRulingHwpxLimits",
            "TableLayoutHwpxLimits",
            "ParagraphStyleLimits",
            "TableFormulaHwpxLimits",
            "FormulaLimits",
            "TableGridLimits",
            "TableRulingLimits",
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
        "input": {"destination", "template", "source", "domain", "profile"},
        "transformation": {"grid", "geometry", "edges", "cells", "pagination"},
        "lowering": {"precondition", "edit_scope", "binding", "publication"},
        "preservation": {"template_semantics", "destination", "package", "source"},
        "receipt": {"binding", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        (
            "input",
            "source",
            "destination_header_section_template_section_state_grid_insertion_context_and_document_flow_sha256",
            "input_source_binding",
        ),
        (
            "input",
            "profile",
            "arbitrary_nonzero_rectangular_blank_unmerged_explicit_nonzero_physical_tracks",
            "input_profile",
        ),
        (
            "transformation",
            "grid",
            "create_exact_rows_times_columns_row_major_one_by_one_masters_with_caller_ids",
            "create_grid",
        ),
        (
            "transformation",
            "edges",
            "expand_uniform_template_outer_and_inner_horizontal_vertical_edge_bands",
            "create_edges",
        ),
        (
            "transformation",
            "cells",
            "create_zero_payload_formula_free_cells_with_exact_template_non_ruling_properties",
            "create_cells",
        ),
        (
            "lowering",
            "precondition",
            "relift_destination_and_template_recheck_empty_context_current_flow_and_rebuild_domain_plan",
            "lowering_precondition",
        ),
        (
            "lowering",
            "publication",
            "return_only_after_header_section_reparse_exact_blank_target_state_grid_pagination_formula_free_and_table_count_readback",
            "lowering_publication",
        ),
        (
            "preservation",
            "package",
            "non_target_parts_and_relationship_graph_preserved",
            "preservation_package",
        ),
        (
            "receipt",
            "debug",
            "all_hashes_logical_ids_content_formulas_raw_xml_and_document_content_omitted",
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
        or len(failure_policy) != 9
        or len(set(failure_policy)) != 9
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
        "hwpx-agent.table-create-hwpx.hancom-2020-template/1",
        "rebuild the domain create plan independently",
        "have no reviewed exact native creation mapping",
        "existing documents are not rewritten in place",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-create-hwpx-validation/v1",
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
        "P06_TABLE_CREATE_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
