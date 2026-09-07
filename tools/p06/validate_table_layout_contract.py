#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-layout-v1.json")
MIGRATION = "protocol/migrations/p06-table-layout-v0-to-v1.md"
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "FEATURE_COVERAGE_MATRIX.csv",
    "specs/capability-contracts.generated.json",
}
EXPECTED_CAPABILITIES = [
    "table.width_height",
    "table.column_fixed_width",
    "table.autofit_content",
    "table.autofit_page",
]
EXPECTED_LIMITS = {
    "columns": 1_024,
    "cells": 1_000_000,
    "rows": 10_000,
    "dimension_micrometers": 1_000_000_000,
    "serialized_bytes": 32 * 1024 * 1024,
}
EXPECTED_NOT_CLAIMED = {
    "installed_font_extraction": False,
    "hancom_2020_renderer_oracle": False,
    "hwpx_layout_lowering_or_readback": False,
    "row_minimum_or_fixed_height_solver": False,
    "equal_row_or_column_operation": False,
    "pagination_or_formula_semantics": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_layout.rs": (
        'TABLE_LAYOUT_SCHEMA_VERSION: &str = "hwpx-agent.table-layout/v1"',
        "pub enum TableWidthSpec",
        "Absolute { width: LengthMicrometers }",
        "Percent { ratio: RatioMillionths }",
        "HARD_MAX_RATIO_MILLIONTHS: u64 = 10_000_000",
        "FitContent",
        "FitPage",
        "pub struct FontMetricEvidence",
        "font_metric_evidence_sha256",
        "pub struct TableLayoutSolver",
        "fn enforce_minimums",
        "fn apply_preferreds",
        "target_underfill",
        "pub fn require_verified",
        "TargetWidthUnsatisfied",
        "pub fn canonical_json",
        "pub fn canonical_sha256",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_layout;",
        "TableLayoutSolver",
        "TableWidthSpec",
        "TABLE_LAYOUT_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_layout.rs": (
        "fit_content_honors_fixed_minimum_and_preferred_widths",
        "absolute_and_percent_widths_resolve_to_exact_targets",
        "fixed_column_never_moves_toward_a_different_preferred_or_previous_width",
        "merged_minimum_is_distributed_only_across_automatic_columns",
        "minimums_are_not_shrunk_when_body_overflows",
        "impossible_fixed_span_reports_exact_content_deficit",
        "exact_target_underfill_is_not_a_verified_fit",
        "absent_or_estimated_metrics_never_promote_to_verified",
        "font_metric_provenance_is_exact_and_bound_into_the_plan",
        "public_layout_error_codes_are_stable",
        "deterministic_128_case_overflow_and_metric_corpus",
    ),
    "implementation/p06/P06-05_TABLE_LAYOUT_POLICY.md": (
        "absolute",
        "percent",
        "fit_content",
        "fit_page",
        "hard minimums are never shrunk",
        "font_metric_evidence_sha256",
        "Not claimed yet",
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
        "schema_version": "hwpx-agent.table-layout-contract/v1",
        "model_schema_version": "hwpx-agent.table-layout/v1",
        "scope": "p06_05_pure_table_width_solver_component_current_pc_local_development",
        "prerequisites": [
            "hwpx-agent.table-grid/v1",
            "checked_length_micrometers_and_ratio_millionths",
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
        "width_modes": {"absolute", "percent", "fit_content", "fit_page"},
        "column_constraints": {"cardinality", "minimum", "preferred", "previous", "fixed"},
        "cell_measurements": {
            "cardinality",
            "minimum_outer_width",
            "preferred_outer_width",
            "merged_span",
            "row_estimate",
        },
        "font_metric_evidence": {
            "verified_or_estimated",
            "missing",
            "plan_binding",
            "promotion",
        },
        "determinism": {
            "cell_order",
            "minimum_distribution",
            "preferred_distribution",
            "grid_binding",
            "serialization",
        },
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    for key, minimum in (("objective_order", 3), ("explicit_nonfit_receipts", 4), ("failure_policy", 9)):
        value = contract.get(key)
        if (
            not isinstance(value, list)
            or len(value) < minimum
            or any(not isinstance(item, str) or not item for item in value)
        ):
            errors.append(key)

    source_locks = contract.get("source_locks")
    source_count = len(source_locks) if isinstance(source_locks, list) else 0
    declared: set[str] = set()
    if not isinstance(source_locks, list):
        errors.append("source_locks_shape")
    else:
        for entry in source_locks:
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

    try:
        migration = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.table-layout/v1",
            "fail closed",
            "Hard minimums are never reduced",
            "new contract version",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        for marker in markers:
            if marker not in source:
                errors.append("implementation_marker")

    return result(
        errors=errors,
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-layout-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "source_locks": source_locks,
        "implementation_files": implementation_files,
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_LAYOUT_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
