#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-inspection-v1.json")
MIGRATION = "protocol/migrations/p06-table-inspection-v0-to-v1.md"
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "WORK_BREAKDOWN_STRUCTURE.csv",
}
EXPECTED_LIMITS = {
    "tables": 100_000,
    "master_cells": 1_000_000,
    "path_steps": 64,
    "nested_depth": 64,
    "serialized_bytes": 32 * 1024 * 1024,
}
EXPECTED_NOT_CLAIMED = {
    "hwpx_selector_lift_or_lower": False,
    "hangul_2020_cursor_or_selection": False,
    "hangul_2020_save_reopen_or_render": False,
    "automation_selection": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_inspector.rs": (
        'TABLE_INSPECTION_SCHEMA_VERSION: &str = "hwpx-agent.table-inspection/v1"',
        "pub struct TableSelector",
        "pub struct TableCellSelector",
        "pub struct TableInspectionSnapshot",
        "pub fn table_selector_for",
        "pub fn cell_selector_at",
        "pub fn cell_selector_for",
        "pub fn resolve_table",
        "pub fn resolve_cell",
        "pub fn canonical_sha256",
        "TableInspectionError::Stale",
        "struct BoundedWriter",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_inspector;",
        "TableInspectionSnapshot",
        "TableCellSelector",
        "TABLE_INSPECTION_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_inspector.rs": (
        "merged_coordinates_resolve_to_one_canonical_master",
        "nested_tables_keep_parent_cell_paths_and_exact_id_selection",
        "parent_cell_inspection_lists_only_direct_nested_tables",
        "drawing_nested_and_note_root_tables_keep_typed_paths",
        "revision_graph_table_and_cell_anchor_drift_fail_closed",
        "table_selector_requires_exact_path_and_fingerprint",
        "unknown_table_cell_and_coordinate_are_distinct_failures",
        "table_cell_depth_path_and_output_limits_are_finite",
        "canonical_snapshot_is_deterministic_metadata_only_and_versioned",
        "debug_surfaces_do_not_disclose_logical_ids_or_cell_content",
        "public_error_codes_are_stable",
    ),
    "implementation/p06/P06-08_TABLE_INSPECTION_POLICY.md": (
        "pure, bounded table inspector implemented; no backend selection claim",
        "same master cell",
        "parent master-cell coordinate",
        "metadata only",
        "No Hangul 2020 cursor/selection",
    ),
}


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def bounded_file(root: Path, relative: str, maximum: int = 5_000_000) -> Path:
    candidate = PurePosixPath(relative)
    if (
        candidate.is_absolute()
        or not candidate.parts
        or any(part in ("", ".", "..") for part in candidate.parts)
        or "\\" in relative
        or ":" in relative
        or "\0" in relative
    ):
        raise ValueError("unbounded path")
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in candidate.parts:
        cursor /= part
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise ValueError("linked path")
    path = cursor.resolve(strict=True)
    if resolved_root not in path.parents or not path.is_file():
        raise ValueError("invalid bounded file")
    if path.stat().st_size <= 0 or path.stat().st_size > maximum:
        raise ValueError("file bound")
    return path


def sha256_utf8_lf(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_contract(bounded_file(root, CONTRACT_RELATIVE.as_posix(), 256_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-inspection-contract/v1",
        "model_schema_version": "hwpx-agent.table-inspection/v1",
        "scope": "p06_08_pure_bounded_table_inspector_current_pc_local_development",
        "prerequisites": [
            "hwpx-agent.document-graph/v2",
            "hwpx-agent.table-grid/v1",
            "p04_selector_structural_path",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "default_limits": EXPECTED_LIMITS,
        "migration": MIGRATION,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    required_objects = {
        "table_selector": {"identity", "location", "content_anchor", "resolution", "fallback"},
        "cell_selector": {"table_anchor", "coordinate", "master_anchor", "covered_slot", "fallback"},
        "nested_tables": {"path", "siblings", "direct_membership", "drawing_flow"},
        "snapshot": {"authority", "binding", "ordering", "content_policy", "digest"},
    }
    for key, required_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != required_keys:
            errors.append(key)
    table_selector = contract.get("table_selector")
    cell_selector = contract.get("cell_selector")
    if isinstance(table_selector, dict) and table_selector.get("fallback") != "none":
        errors.append("table_selector_fallback")
    if isinstance(cell_selector, dict) and cell_selector.get("fallback") != "none":
        errors.append("cell_selector_fallback")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) < 9
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        errors.append("failure_policy")

    source_count = validate_source_locks(contract.get("source_locks"), root, errors)
    validate_migration(root, errors)
    implementation_count = validate_implementation(root, errors)
    return result(errors=errors, source_locks=source_count, implementation_files=implementation_count)


def validate_source_locks(value: Any, root: Path, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_locks_shape")
        return 0
    declared: set[str] = set()
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append("source_lock_types")
            continue
        if relative in declared:
            errors.append("source_lock_duplicate")
            continue
        declared.add(relative)
        try:
            actual = sha256_utf8_lf(bounded_file(root, relative))
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_path_or_encoding")
            continue
        if actual != expected:
            errors.append("source_lock_digest")
    if declared != EXPECTED_SOURCE_PATHS:
        errors.append("source_lock_paths_exact")
    return len(value)


def validate_migration(root: Path, errors: list[str]) -> None:
    try:
        migration = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path_or_encoding")
        return
    for marker in (
        "hwpx-agent.table-inspection/v1",
        "TableSelector",
        "TableCellSelector",
        "not coerced",
        "may not promote",
    ):
        if marker not in migration:
            errors.append("migration_marker")


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, relative, 2_000_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path_or_encoding")
            continue
        if any(marker not in text for marker in markers):
            errors.append("implementation_marker")
    return len(IMPLEMENTATION_MARKERS)


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-inspection-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "p06_08": "component_pass" if not errors else "in_progress",
        "actual_hangul": False,
        "product_complete": False,
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_INSPECTION_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
