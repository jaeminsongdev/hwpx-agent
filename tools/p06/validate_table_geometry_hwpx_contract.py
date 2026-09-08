#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-geometry-hwpx-v1.json"
MIGRATION = "protocol/migrations/p06-table-geometry-hwpx-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_GEOMETRY_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_GEOMETRY_HWPX_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-geometry-v1.json",
}
EXPECTED_FEATURES = {
    "TABLE-018": "table.equal_row_height",
    "TABLE-019": "table.equal_column_width",
    "TABLE-050": "table.row_min_height",
}
EXPECTED_EVIDENCE = {
    "adapter_tests": 9,
    "feature_count": 3,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "validations": ["formula_readback", "page_split", "schema", "semantic_reopen"],
}
EXPECTED_NOT_CLAIMED = {
    "render_diff": False,
    "hangul_2020_target_build": False,
    "automation_runtime": False,
    "differential_exact_match": False,
    "release_enabled": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_geometry.rs": (
        "pub fn grid_sha256",
        "pub fn row_heights",
        "pub fn column_widths",
        "pub fn canonical_sha256",
    ),
    "crates/hwpx-package/src/table_layout.rs": (
        'TABLE_GEOMETRY_HWPX_PROFILE_ID: &str =',
        "pub struct TableGeometryHwpxLoweringReceipt",
        "pub struct TableGeometryHwpxLowerer",
        "pub fn lower_with_receipt",
        "pub fn lower_in_section_with_receipt",
        "fn lower_geometry_selected",
        "fn from_geometry",
        "GeometryGridMismatch",
        "geometry_state_sha256",
        "content_sha256",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_GEOMETRY_HWPX_PROFILE_ID",
        "TableGeometryHwpxLowerer",
        "TableGeometryHwpxLoweringReceipt",
    ),
    "crates/hwpx-package/tests/table_geometry_hwpx.rs": (
        "lowers_all_three_geometry_operations_with_exact_readback",
        "full_package_preserves_formula_pagination_and_all_non_section_parts",
        "receipt_binds_state_and_preserves_content_and_margins",
        "merged_cell_uses_exact_row_and_column_track_sums",
        "section_selection_preserves_the_unselected_table_exactly",
        "lowering_is_deterministic_and_idempotent",
        "grid_identity_and_source_shape_fail_before_publication",
        "output_and_dimension_limits_fail_closed",
        "receipt_debug_and_public_errors_are_stable",
    ),
    POLICY: (
        "direct HWPX integration implemented; no licensed Hangul 2020 oracle claim",
        "Only the selected table's",
        "returns no output",
        "integration_passed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "9/9 PASS",
        "Formula AST/cache and pagination policy",
        "byte-identical",
        "green rows: remains 0/61",
        "No Hangul process",
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
        "profile_id",
        "scope",
        "features",
        "source_lock_canonicalization",
        "source_locks",
        "input",
        "lowering",
        "preservation",
        "receipt",
        "limits_profile",
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
        "schema_version": "hwpx-agent.table-geometry-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-geometry-hwpx.hancom-2020/1",
        "scope": "p06_09_static_current_pc_hancom_2020_hwpx_geometry_adapter",
        "features": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "limits_profile": "TableLayoutHwpxLimits",
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
        "input": {"state", "source", "profile"},
        "lowering": {"unit_conversion", "editable_attributes", "merged_cells", "publication"},
        "preservation": {
            "cell_text_comments",
            "inner_margins",
            "unselected_tables",
            "formula",
            "pagination",
            "non_section_parts",
            "package_rebuild",
            "source",
        },
        "receipt": {"binding", "counts", "semantic_readback", "debug"},
    }
    for key, keys in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != keys:
            add_error(errors, key)
    lowering = contract.get("lowering")
    if isinstance(lowering, dict) and lowering.get("editable_attributes") \
            != "selected_hp_sz_and_hp_cellSz_width_height_only":
        add_error(errors, "lowering_edit_scope")
    preservation = contract.get("preservation")
    if isinstance(preservation, dict) and preservation.get("unselected_tables") != "byte_identical":
        add_error(errors, "preservation_unselected")
    receipt = contract.get("receipt")
    if isinstance(receipt, dict) and receipt.get("debug") \
            != "hashes_and_raw_dimensions_redacted":
        add_error(errors, "receipt_debug")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 7
        or len(set(failure_policy)) != 7
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
        "hwpx-agent.table-geometry-hwpx.hancom-2020/1",
        "not coerced",
        "returns bytes only",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-geometry-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 3,
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
        "P06_TABLE_GEOMETRY_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
