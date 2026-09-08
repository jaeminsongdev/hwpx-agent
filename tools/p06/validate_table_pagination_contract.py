#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-pagination-v1.json")
MIGRATION = "protocol/migrations/p06-table-pagination-v0-to-v1.md"
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "FEATURE_COVERAGE_MATRIX.csv",
    "specs/capability-contracts.generated.json",
}
EXPECTED_CAPABILITIES = [
    "table.repeat_header",
    "table.allow_page_split",
    "table.row_split_policy",
    "table.caption",
]
EXPECTED_LIMITS = {
    "rows": 10_000,
    "pages": 20_000,
    "fragments": 1_000_000,
    "dimension_micrometers": 1_000_000_000,
    "serialized_bytes": 32 * 1024 * 1024,
}
EXPECTED_NOT_CLAIMED = {
    "hancom_2020_page_count_or_bounding_boxes": False,
    "hancom_2020_save_reopen_or_pdf": False,
    "hwpx_pagination_lowering_or_readback": False,
    "automation_pagination_binding": False,
    "left_or_right_caption_layout": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_07_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_pagination.rs": (
        'TABLE_PAGINATION_SCHEMA_VERSION: &str = "hwpx-agent.table-pagination/v1"',
        '"hwpx-agent.table-pagination-observation/v1"',
        "pub enum TablePageSplitPolicy",
        "Allow",
        "AvoidRow",
        "AvoidTable",
        "RequiredKeep",
        "pub enum RowSplitEligibility",
        "NestedTable",
        "UnbreakableObject",
        "pub struct TableCaption",
        "pub enum TablePageItem",
        "RepeatedHeader",
        "RowFragment",
        "pub struct TablePaginationValidator",
        "validate_merged_cell_page_boundaries",
        "HeaderSpanCrossesBody",
        "HeaderRowSplit",
        "pub fn canonical_sha256",
        "struct BoundedWriter",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_pagination;",
        "TablePaginationValidator",
        "TablePageSplitPolicy",
        "TABLE_PAGINATION_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_pagination.rs": (
        "exact_boundary_and_one_row_after_repeat_header_validate",
        "one_micrometer_before_exact_and_after_boundary_are_distinct",
        "allow_policy_validates_one_row_split_across_exact_boundary",
        "avoid_row_nested_and_unbreakable_rows_fail_closed",
        "avoid_table_and_required_keep_reject_split_or_detached_caption",
        "top_and_bottom_caption_position_and_height_are_exact",
        "repeated_header_mismatch_and_cross_body_span_fail_closed",
        "avoid_row_rejects_vertical_merged_cell_across_pages",
        "page_capacity_fragment_and_row_accounting_fail_closed",
        "bounded_json_rejects_unknown_duplicate_and_oversized_inputs",
        "public_error_codes_are_stable",
    ),
    "implementation/p06/P06-07_TABLE_PAGINATION_POLICY.md": (
        "pure, bounded table-pagination observation validator implemented; no renderer claim",
        "one micrometer before and after the boundary",
        "No current Hangul 2020 page count",
        "No left/right caption layout",
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
        "schema_version": "hwpx-agent.table-pagination-contract/v1",
        "model_schema_version": "hwpx-agent.table-pagination/v1",
        "observation_schema_version": "hwpx-agent.table-pagination-observation/v1",
        "scope": "p06_07_pure_bounded_table_pagination_observation_validator_current_pc_local_development",
        "prerequisites": [
            "hwpx-agent.table-grid/v1",
            "checked_length_micrometers",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "component_capabilities": EXPECTED_CAPABILITIES,
        "default_limits": EXPECTED_LIMITS,
        "migration": MIGRATION,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    required_objects = {
        "page_split_policies": {"allow", "avoid_row", "avoid_table", "required_keep"},
        "repeat_header": {
            "selection",
            "span_rule",
            "first_page",
            "continuation_pages",
            "capacity",
        },
        "row_fragments": {"coverage", "sequence", "height", "continuation", "blocked_shapes"},
        "captions": {
            "v1_sides",
            "identity",
            "capacity",
            "top_order",
            "bottom_order",
            "required_keep",
        },
        "page_observation": {"identity", "capacities", "accounting", "authority"},
        "determinism": {"policy_binding", "observation_binding", "grid_binding", "receipt"},
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    captions = contract.get("captions")
    if isinstance(captions, dict) and captions.get("v1_sides") != ["top", "bottom"]:
        errors.append("caption_sides")
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
    return result(
        errors=errors,
        source_locks=source_count,
        implementation_files=implementation_count,
    )


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
        "hwpx-agent.table-pagination/v1",
        "hwpx-agent.table-pagination-observation/v1",
        "Unknown values",
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
        "schema_version": "hwpx-agent.p06-table-pagination-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "p06_07": "in_progress",
        "actual_hangul": False,
        "product_complete": False,
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_PAGINATION_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
