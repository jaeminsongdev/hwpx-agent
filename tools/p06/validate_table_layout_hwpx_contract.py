#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_base_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_layout_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_layout_validator", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table layout validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


base = load_base_validator()
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-layout-hwpx-v1.json")
MIGRATION = "protocol/migrations/p06-table-layout-hwpx-v0-to-v1.md"
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "implementation/p02/evidence/owpml/owpml.records.v1.json",
    "protocol/private/p06-table-layout-v1.json",
}
EXPECTED_CAPABILITIES = [
    "table.width_height",
    "table.column_fixed_width",
    "table.autofit_content",
    "table.autofit_page",
]
EXPECTED_LIMITS = {
    "input_bytes": 8 * 1024 * 1024,
    "output_bytes": 8 * 1024 * 1024,
    "elements": 131_072,
    "tables": 4_096,
    "cells": 32_768,
    "rows": 10_000,
    "columns": 1_024,
    "slots": 1_000_000,
    "dimension_hwpunit": 100_000_000,
}
EXPECTED_NOT_CLAIMED = {
    "installed_font_extraction": False,
    "hancom_2020_renderer_oracle": False,
    "row_minimum_or_fixed_height_solver": False,
    "equal_row_or_column_operation": False,
    "pagination_or_formula_semantics": False,
    "arbitrary_table_shape_repair": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_04_complete": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_layout.rs": (
        'TABLE_LAYOUT_HWPX_PROFILE_ID_V1: &str =',
        '"hwpx-agent.table-layout-hwpx.hancom-2020/1"',
        "pub struct TableLayoutHwpxReader",
        "pub struct TableLayoutHwpxLowerer",
        "pub fn count_in_section",
        "pub fn read_in_section",
        "pub fn lower_in_section_with_receipt",
        "plan.require_verified()",
        "PlanGridMismatch",
        "GridShapeMismatch",
        "content_sha256",
        'required_attribute(value, "widthRelTo")? != "ABSOLUTE"',
        'required_u32(root_element, "cellSpacing")? != 0',
    ),
    "crates/hwpx-package/src/lib.rs": (
        "mod table_layout;",
        "TableLayoutHwpxLowerer",
        "TABLE_LAYOUT_HWPX_PROFILE_ID",
    ),
    "crates/hwpx-package/tests/table_layout.rs": (
        "verified_plan_lowers_table_and_cells_and_preserves_content",
        "merged_cell_uses_exact_column_span_sum",
        "selected_section_table_changes_without_touching_sibling",
        "lowering_is_idempotent_and_deterministic",
        "estimated_or_missing_font_metrics_cannot_be_published",
        "source_grid_overlap_gap_or_span_drift_fails_closed",
        "relative_table_size_nonzero_spacing_and_unknown_shape_are_rejected",
        "finite_input_output_element_cell_and_dimension_limits_hold",
    ),
    "implementation/p06/P06-05_HWPX_LAYOUT_POLICY.md": (
        "TableLayoutPlan::require_verified()",
        "cellSpacing=\"0\"",
        "gap-free, nonoverlapping grid",
        "Only existing `hp:sz`",
        "content-token SHA-256",
        "Not claimed yet",
    ),
    "crates/hwpx-package/Cargo.toml": (
        'domain-ir = { version = "0.1.0", path = "../domain-ir" }',
    ),
}


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=base.reject_duplicate_keys
    )
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_contract(base.bounded_file(root, CONTRACT_RELATIVE.as_posix(), 256_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-layout-hwpx-contract/v1",
        "model_schema_version": "hwpx-agent.table-layout-hwpx.hancom-2020/1",
        "scope": "p06_05_current_pc_hancom_2020_hwpx_table_layout_lowering_and_readback_component",
        "prerequisites": [
            "hwpx-agent.table-layout/v1",
            "hwpx-agent.table-grid/v1",
            "p03_preserving_xml_exact_source_spans",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "capabilities": EXPECTED_CAPABILITIES,
        "default_limits": EXPECTED_LIMITS,
        "atomicity": (
            "source_bytes_are_immutable_and_only_a_fully_reparsed_exact_layout_and_content_result_returns"
        ),
        "migration": MIGRATION,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    required_objects = {
        "plan_admission": {"verification", "grid_binding", "shape", "totals"},
        "current_2020_shape": {
            "roots", "table", "rows", "cells", "coverage", "unknown_shape"
        },
        "quantization": {"unit", "table_width", "table_height", "merged_cell"},
        "lowering": {"entrypoints", "mutation", "sibling_preservation", "readback", "receipt"},
        "source_evidence": {"owpml", "solver", "runtime_target"},
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    for key, minimum in (("validation_order", 7), ("failure_policy", 8)):
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
            digest = entry.get("sha256")
            if not isinstance(relative, str) or not isinstance(digest, str) or relative in declared:
                errors.append("source_lock_types_or_duplicate")
                continue
            declared.add(relative)
            try:
                actual = base.sha256_utf8_lf(base.bounded_file(root, relative))
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual != digest:
                errors.append("source_lock_digest")
        if declared != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = base.bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.table-layout-hwpx.hancom-2020/1",
            "fail closed",
            "Only existing `hp:sz`",
            "new contract version",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = base.bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")

    return result(
        errors=sorted(set(errors)),
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-layout-hwpx-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": errors,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_LAYOUT_HWPX_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
