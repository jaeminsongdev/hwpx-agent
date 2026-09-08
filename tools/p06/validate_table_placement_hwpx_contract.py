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
CONTRACT = "protocol/private/p06-table-placement-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-placement-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_PLACEMENT_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_PLACEMENT_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-placement-v1.json",
}
EXPECTED_FEATURES = {
    "TABLE-034": "table.position",
    "TABLE-036": "table.inline_floating",
    "TABLE-037": "table.wrap",
    "TABLE-038": "table.outer_margin",
}
EXPECTED_EVIDENCE = {
    "adapter_tests": 7,
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
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_placement.rs": (
        'TABLE_PLACEMENT_SCHEMA_VERSION: &str = "hwpx-agent.table-placement/v1"',
        "pub enum TableAttachmentMode",
        "pub struct TableFloatingPlacement",
        "pub struct TablePlacementState",
        "pub enum TablePlacementOperation",
        "pub fn canonical_sha256",
    ),
    "crates/hwpx-package/src/table_placement.rs": (
        'TABLE_PLACEMENT_HWPX_PROFILE_ID: &str =',
        "pub struct TablePlacementHwpxReadback",
        "pub struct TablePlacementHwpxLoweringReceipt",
        "pub struct TablePlacementHwpxReader",
        "pub struct TablePlacementHwpxLowerer",
        "pub fn lower_with_receipt",
        "pub fn lower_in_section_with_receipt",
        "fn native_from_state",
        "fn placement_edits",
        "SourceStateMismatch",
        "ReadbackMismatch",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "mod table_placement;",
        "TABLE_PLACEMENT_HWPX_PROFILE_ID",
        "TablePlacementHwpxReader",
        "TablePlacementHwpxLowerer",
    ),
    "crates/hwpx-package/tests/table_placement_hwpx.rs": (
        "reader_maps_complete_current_profile_and_rejects_malformed_native_values",
        "position_operation_covers_every_reference_alignment_and_flag_variant",
        "inline_floating_transitions_preserve_inactive_native_fields",
        "wrap_and_outer_margin_operations_cover_all_native_values",
        "state_identity_source_drift_and_finite_limits_fail_closed",
        "section_selection_is_exact_deterministic_idempotent_and_redacted",
        "closed_package_reopen_preserves_grid_formula_cache_pagination_and_other_parts",
    ),
    POLICY: (
        "direct HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "inactive floating-position attributes byte-for-byte",
        "direct_hwpx / integration_passed",
        "Tight`/`Through` wrapping is not admitted",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "7/7 PASS",
        "16/16 exact readback PASS",
        "unit_passed`: 40 to 36",
        "integration_passed`: 6 to 10",
        "green rows: remains 0/61",
        "No Hangul process",
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
        "inactive_preservation",
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
        "schema_version": "hwpx-agent.table-placement-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-placement-hwpx.hancom-2020/1",
        "model_profile_id": "hwpx-agent.table-placement/v1",
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_table_placement_admission",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profiles": ["TablePlacementLimits", "TableLayoutHwpxLimits"],
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
        "input": {"source_state", "target_state", "source", "profile"},
        "native_mapping": {
            "attachment",
            "floating_position",
            "wrap_flow",
            "outer_margins",
            "canonical_values",
        },
        "inactive_preservation": {"inline_target", "floating_target", "unowned"},
        "lowering": {"precondition", "editable_attributes", "unit_conversion", "publication"},
        "preservation": {
            "grid_cells_payload_properties",
            "merged_sibling",
            "formula",
            "pagination",
            "non_section_parts",
            "package_rebuild",
            "source",
        },
        "receipt": {"profile", "binding", "counts", "debug"},
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)

    native = contract.get("native_mapping")
    if isinstance(native, dict):
        if native.get("wrap_flow") != "hp_tbl_textWrap_and_textFlow_four_table_values_each":
            add_error(errors, "native_wrap_flow")
        if native.get("canonical_values") != (
            "exact_reviewed_enums_boolean_0_or_1_and_decimal_hwpunit"
        ):
            add_error(errors, "native_canonical_values")
    inactive = contract.get("inactive_preservation")
    if isinstance(inactive, dict):
        if inactive.get("inline_target") != (
            "preserve_all_floating_position_native_attributes"
        ):
            add_error(errors, "inactive_inline")
        if inactive.get("floating_target") != (
            "preserve_inactive_affectLSpacing_native_attribute"
        ):
            add_error(errors, "inactive_floating")
    lowering = contract.get("lowering")
    if isinstance(lowering, dict) and lowering.get("editable_attributes") != (
        "differing_owned_hp_tbl_hp_pos_and_hp_outMargin_value_spans_only"
    ):
        add_error(errors, "lowering_edit_scope")
    preservation = contract.get("preservation")
    if isinstance(preservation, dict):
        if preservation.get("grid_cells_payload_properties") != (
            "strict_layout_content_sha256_exact"
        ):
            add_error(errors, "preservation_content")
        if preservation.get("merged_sibling") != "byte_identical":
            add_error(errors, "preservation_sibling")
    receipt = contract.get("receipt")
    if isinstance(receipt, dict) and receipt.get("debug") != (
        "hashes_identifiers_offsets_margins_and_document_values_omitted"
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
        "hwpx-agent.table-placement-hwpx.hancom-2020/1",
        "Existing documents are not rewritten",
        "not coerced",
        "returns bytes only",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-placement-hwpx-validation/v1",
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
        "P06_TABLE_PLACEMENT_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
