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
CONTRACT = "protocol/private/p06-table-placement-v1.json"
MIGRATION = "protocol/migrations/p06-table-placement-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_PLACEMENT_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_PLACEMENT_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-034", "capability_id": "table.position"},
    {"feature_id": "TABLE-036", "capability_id": "table.inline_floating"},
    {"feature_id": "TABLE-037", "capability_id": "table.wrap"},
    {"feature_id": "TABLE-038", "capability_id": "table.outer_margin"},
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 65_536,
    "offset_micrometers": 1_000_000_000,
    "margin_micrometers": 1_000_000_000,
    "serialized_bytes": 65_536,
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "native_attribute_normalization": False,
    "semantic_reopen": False,
    "formula_or_page_preservation": False,
    "pagination_or_render": False,
    "hancom_2020_target_build": False,
    "automation_or_differential": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_placement.rs": (
        'TABLE_PLACEMENT_SCHEMA_VERSION: &str = "hwpx-agent.table-placement/v1"',
        "pub enum TableAttachmentMode",
        "pub struct TableFloatingPlacement",
        "pub struct TablePlacementState",
        "pub enum TablePlacementOperation",
        "pub struct TablePlacementReceipt",
        "pub fn from_json",
        "pub fn apply",
        "pub const fn capability_id",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_placement;",
        "TablePlacementState",
        "TablePlacementOperation",
        "TABLE_PLACEMENT_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_placement.rs": (
        "state_roundtrips_with_exact_attachment_and_inactive_values",
        "position_changes_only_floating_placement",
        "inline_and_floating_conversion_preserve_wrap_and_margins",
        "wrap_and_flow_change_together_without_touching_position",
        "outer_margin_operation_is_independent_and_idempotent",
        "inactive_position_and_wrap_operations_fail_closed",
        "offset_margin_and_limit_bounds_fail_closed",
        "strict_json_version_and_size_fail_closed",
        "canonical_state_and_receipt_are_deterministic",
        "output_limit_is_checked_after_operation",
        "debug_output_redacts_identifiers_offsets_margins_and_hashes",
        "fixed_seed_operations_remain_bounded_and_deterministic",
        "schema_capability_and_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded component implemented; no HWPX or Hangul 2020 oracle claim",
        "Both reject inline tables because their values are inactive",
        "component_only / unit_passed",
    ),
    REPORT: (
        "Result: `component_pass`",
        "13/13 PASS",
        "cataloged`: 18 to 14",
        "unit_passed`: 25 to 29",
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
        "schema_version",
        "model_schema_version",
        "scope",
        "features",
        "source_lock_canonicalization",
        "source_locks",
        "migration",
        "policy",
        "report",
        "implementation_files",
        "semantics",
        "binding",
        "default_limits",
        "failure_policy",
        "not_claimed",
        "gate_decision",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-placement-contract/v1",
        "model_schema_version": "hwpx-agent.table-placement/v1",
        "scope": "p06_09_pure_bounded_table_placement_current_pc_local_development",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": sorted(IMPLEMENTATION_MARKERS),
        "default_limits": EXPECTED_LIMITS,
        "not_claimed": EXPECTED_NOT_CLAIMED,
        "gate_decision": {
            "component": "pass",
            "direct_stage": "unit_passed",
            "actual_hwpx": False,
            "actual_hangul": False,
            "p06_09": "in_progress",
            "product_complete": False,
        },
    }
    for key, expected in exact.items():
        actual = contract.get(key)
        if key == "implementation_files" and isinstance(actual, list):
            actual = sorted(actual)
        if actual != expected:
            add_error(errors, key)

    expected_objects = {
        "semantics": {
            "position",
            "attachment",
            "wrap",
            "outer_margin",
            "inactive_values",
            "idempotence",
        },
        "binding": {
            "identity",
            "references",
            "alignments",
            "offsets",
            "margins",
            "receipt",
            "serialization",
        },
    }
    for key, expected_fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_fields:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("position") != "replace_complete_floating_position_payload_only":
            add_error(errors, "semantics_position")
        if semantics.get("wrap") != (
            "replace_text_wrap_and_side_flow_together_on_floating_table_only"
        ):
            add_error(errors, "semantics_wrap")
        if semantics.get("outer_margin") != (
            "replace_four_nonnegative_margins_only_in_either_attachment_mode"
        ):
            add_error(errors, "semantics_outer_margin")

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
        "hwpx-agent.table-placement/v1",
        "Existing documents are not rewritten",
        "no partial state",
        "separately versioned",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-placement-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 4,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "actual_hwpx": False,
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
        "P06_TABLE_PLACEMENT_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
