#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-geometry-v1.json"
MIGRATION = "protocol/migrations/p06-table-geometry-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_GEOMETRY_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_GEOMETRY_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_FEATURES = {
    "TABLE-018": "table.equal_row_height",
    "TABLE-019": "table.equal_column_width",
    "TABLE-050": "table.row_min_height",
}
EXPECTED_LIMITS = {
    "rows": 10_000,
    "columns": 1_024,
    "dimension_micrometers": 1_000_000_000,
    "serialized_bytes": 32 * 1024 * 1024,
}
EXPECTED_EVIDENCE = {
    "rust_tests": 13,
    "fixed_seed_cases": 256,
    "contract_tests": 4,
    "backend": "component_only",
    "direct_stage": "unit_passed",
}
EXPECTED_NOT_CLAIMED = {
    "direct_hwpx_adapter": False,
    "semantic_reopen": False,
    "formula_preservation": False,
    "page_split_or_render_diff": False,
    "hangul_2020_target_oracle": False,
    "automation_or_differential": False,
    "release_enabled": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_geometry.rs": (
        'TABLE_GEOMETRY_SCHEMA_VERSION: &str = "hwpx-agent.table-geometry/v1"',
        "pub struct TableGeometryState",
        "pub enum TableGeometryOperation",
        "EqualRowHeights",
        "EqualColumnWidths",
        "SetRowMinimumHeight",
        "pub fn cell_extent",
        "pub fn apply",
        "fn checked_range",
        "struct BoundedWriter",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_geometry;",
        "TableGeometryState",
        "TableGeometryOperation",
        "TABLE_GEOMETRY_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_geometry.rs": (
        "equalizes_rows_with_ceiling_average_and_content_minimum",
        "equalizes_columns_without_touching_rows",
        "row_minimum_grows_small_rows_but_never_shrinks_large_rows",
        "operations_are_deterministic_and_idempotent",
        "merged_cell_extent_sums_every_covered_track",
        "canonical_state_roundtrips_and_is_grid_bound",
        "malformed_unknown_duplicate_and_oversized_json_fail_closed",
        "invalid_counts_dimensions_minimums_and_limits_are_rejected",
        "invalid_ranges_and_operation_dimensions_leave_source_unchanged",
        "debug_output_redacts_hashes_and_dimensions",
        "fixed_seed_corpus_preserves_minima_and_determinism",
        "schema_and_error_codes_are_stable",
        "unsupported_version_and_explicit_grid_hash_mismatch_fail_closed",
    ),
    POLICY: (
        "pure bounded component implemented; no HWPX or Hangul 2020 oracle claim",
        "ceiling of",
        "never shrinks",
        "leave the source state byte-for-byte unchanged",
        "unit_passed",
    ),
    REPORT: (
        "Result: `component_pass`",
        "13/13 PASS",
        "256/256",
        "green rows: remains 0/61",
        "no Hangul process",
    ),
}


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate key")
        output[key] = value
    return output


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


def canonical_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = text.replace("\r\n", "\n")
    if "\r" in canonical:
        raise ValueError("bare carriage return")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def add_error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


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
        "prerequisites",
        "source_lock_canonicalization",
        "source_locks",
        "semantics",
        "state_binding",
        "receipt",
        "default_limits",
        "failure_policy",
        "migration",
        "policy",
        "report",
        "expected_evidence",
        "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    expected_scalars = {
        "schema_version": "hwpx-agent.table-geometry-contract/v1",
        "model_schema_version": "hwpx-agent.table-geometry/v1",
        "scope": "p06_09_pure_bounded_table_geometry_current_pc_local_development",
        "features": EXPECTED_FEATURES,
        "prerequisites": [
            "hwpx-agent.table-grid/v1",
            "integer_micrometer_units",
            "p06_09_fail_closed_conformance_matrix",
        ],
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "default_limits": EXPECTED_LIMITS,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "expected_evidence": EXPECTED_EVIDENCE,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add_error(errors, key)

    expected_objects = {
        "semantics": {"equal_tracks", "row_minimum", "merged_extent", "outside_selection"},
        "state_binding": {"grid", "counts", "dimensions", "minimums"},
        "receipt": {"binding", "changed_tracks", "serialization", "debug"},
    }
    for key, keys in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != keys:
            add_error(errors, key)
    semantics = contract.get("semantics")
    if isinstance(semantics, dict) and semantics.get("outside_selection") != "preserved_exactly":
        add_error(errors, "semantics_outside_selection")
    receipt = contract.get("receipt")
    if isinstance(receipt, dict) and receipt.get("debug") != "hashes_and_dimensions_redacted":
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
        "hwpx-agent.table-geometry/v1",
        "TableTrackRange",
        "not coerced",
        "do not mutate",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-geometry-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 3,
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
        "P06_TABLE_GEOMETRY_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
