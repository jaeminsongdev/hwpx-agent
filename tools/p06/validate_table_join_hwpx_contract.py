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
CONTRACT = "protocol/private/p06-table-join-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-join-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_JOIN_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_JOIN_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-partition-v1.json",
}
EXPECTED_FEATURES = {"TABLE-011": "table.join_table"}
EXPECTED_EVIDENCE = {
    "adapter_tests": 7,
    "feature_count": 1,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "validations": ["formula_readback", "page_split", "schema", "semantic_reopen"],
}
EXPECTED_NOT_CLAIMED = {
    "render_diff": False,
    "saved_real_hwpx": False,
    "hangul_2020_target_build": False,
    "automation_runtime": False,
    "differential_exact_match": False,
    "rollback_or_retry": False,
    "release_enabled": False,
    "arbitrary_user_document_compatibility": False,
    "formula_rebase_or_cache_clear": False,
    "repeat_header_join": False,
    "caption_join": False,
    "different_junction_edges": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_partition.rs": (
        "pub struct WholeTableJoinRequestDraft",
        "pub struct WholeTableJoinPlan",
        "pub fn join(",
        "fn common_lattice(",
    ),
    "crates/hwpx-package/src/table_pagination.rs": (
        "pub struct TablePaginationHwpxReadback",
        "fn read_repeat_header_rows",
        "TABLE_PAGINATION_HWPX_PROFILE_ID",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx/partition_hwpx.rs": (
        'TABLE_JOIN_HWPX_SCHEMA_VERSION: &str =',
        'TABLE_JOIN_HWPX_PROFILE_ID: &str =',
        "pub struct TableJoinHwpxReadback",
        "pub struct TableJoinHwpxRequest",
        "pub struct TableJoinHwpxPlan",
        "pub struct TableJoinHwpxLoweringReceipt",
        "fn joined_edges(",
        "fn render_join_section(",
        "fn reject_duplicate_json_keys(",
        "JunctionEdgeMismatch",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": (
        "mod partition_hwpx;",
        "TableJoinHwpxBuilder",
        "pub(super) fn render_partition_existing",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_JOIN_HWPX_PROFILE_ID",
        "TableJoinHwpxReader",
        "TableJoinHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_join_hwpx.rs": (
        "join_projects_unequal_tables_and_reopens_complete_state",
        "join_rejects_non_whitespace_or_missing_separator",
        "join_rejects_formula_profile_and_junction_edge_loss",
        "join_rejects_divergent_page_split",
        "join_rejects_source_flow_and_plan_drift",
        "join_json_is_strict_bounded_and_debug_is_redacted",
        "join_closed_package_preserves_sibling_formula_and_non_section_parts",
    ),
    POLICY: (
        "direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "reduced-rational boundary",
        "one joined shared edge",
        "direct_hwpx / integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "7/7 PASS",
        "unit_passed`: 26 to 25",
        "integration_passed`: 20 to 21",
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
        "source_lock_canonicalization", "source_locks", "input", "join", "binding",
        "preservation", "native_profile", "receipt", "limits_profiles", "failure_policy",
        "migration", "policy", "report", "expected_evidence", "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-join-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-join-hwpx.hancom-2020-wrapper/1",
        "model_profile_ids": {
            "partition": "hwpx-agent.table-partition/v1",
            "ruling": "hwpx-agent.table-ruling/v1",
            "pagination": "hwpx-agent.table-pagination-hwpx.hancom-2020/1",
        },
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_exact_whole_table_join_admission",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": [
            "TableLayoutHwpxLimits", "ParagraphStyleLimits", "TableFormulaHwpxLimits",
            "FormulaLimits", "TableGridLimits", "TableRulingLimits",
            "TablePartitionLimits", "TablePaginationHwpxLimits",
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
        "input": {"existing_tables", "join", "wrappers", "formula_policy"},
        "join": {"separator", "identity", "lattice", "geometry", "junction"},
        "binding": {"request", "build", "lower", "publication"},
        "preservation": {"cells", "payload", "edges", "pagination", "formula", "package"},
        "native_profile": {"formula", "repeat_header", "caption", "pagination", "native_ids", "edits"},
        "receipt": {"hashes", "counts", "debug"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)

    checks = (
        ("join", "separator", "one_or_more_exact_paragraph_run_text_wrappers_with_empty_or_ascii_space_text_only", "separator"),
        ("join", "lattice", "union_exact_reduced_rational_column_boundaries_materialized_at_larger_width_half_up", "lattice"),
        ("join", "junction", "require_projected_leading_bottom_and_trailing_top_edge_identity_equality_at_every_track", "junction"),
        ("binding", "publication", "return_only_after_final_table_reopens_with_exact_grid_ruling_partition_and_page_split_semantics", "publication"),
        ("preservation", "payload", "ordered_raw_paragraph_blocks_and_bound_logical_payload_identities_remain_byte_exact", "payload_preservation"),
        ("preservation", "formula", "selected_table_formulas_fail_closed_sibling_owner_ast_number_format_and_display_cache_remain_exact", "formula_preservation"),
        ("preservation", "package", "source_never_mutated_trailing_document_flow_sibling_tables_and_every_non_target_package_part_byte_identical", "package_preservation"),
        ("native_profile", "pagination", "both_source_page_split_values_must_match_and_the_leading_value_survives", "pagination_boundary"),
        ("native_profile", "native_ids", "leading_table_and_wrapper_ids_survive_trailing_table_wrapper_and_separator_ids_retire_no_new_ids", "native_ids"),
        ("receipt", "debug", "all_hashes_logical_ids_payloads_formulas_cache_and_raw_xml_omitted", "receipt_debug"),
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
    validate_feature_catalog(root, errors)
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
            or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest)
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


def validate_feature_catalog(root: Path, errors: list[str]) -> None:
    try:
        text = bounded_file(root, "docs/04_feature_catalog/07_table.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "feature_catalog_path")
        return
    matches = [line for line in text.splitlines() if line.startswith("| TABLE-011 |")]
    if len(matches) != 1 or "`table.join_table`" not in matches[0]:
        add_error(errors, "feature_catalog_mapping")


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
        "hwpx-agent.table-join-hwpx.hancom-2020-wrapper/1",
        "relifts both sources and rebuilds the domain result",
        "one joined native shared edge cannot preserve both",
        "rewritten in place",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-join-hwpx-validation/v1",
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
        "P06_TABLE_JOIN_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
