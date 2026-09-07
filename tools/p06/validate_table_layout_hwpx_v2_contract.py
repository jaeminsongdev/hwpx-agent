#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_v1_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_layout_hwpx_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_layout_hwpx_v1", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table layout HWPX v1 validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


v1 = load_v1_validator()
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-layout-hwpx-v2.json")
PREDECESSOR_RELATIVE = PurePosixPath("protocol/private/p06-table-layout-hwpx-v1.json")
PREDECESSOR_SHA256 = "ab21dbcb1b646956f5e645ef10ea37c68e6416f9384fc7292bdc565acf8f4092"
MIGRATION_RELATIVE = PurePosixPath("protocol/migrations/p06-table-layout-hwpx-v1-to-v2.md")
REPORT_RELATIVE = PurePosixPath("implementation/p06/P06-05_TARGET_FIXTURE.md")
EXPECTED_SOURCE_PATHS = v1.EXPECTED_SOURCE_PATHS
EXPECTED_CAPABILITIES = v1.EXPECTED_CAPABILITIES
EXPECTED_LIMITS = v1.EXPECTED_LIMITS
EXPECTED_NOT_CLAIMED = {
    "hancom_2020_target_runtime_readback": False,
    "hancom_2020_target_visual_oracle": False,
    "row_minimum_or_fixed_height_solver": False,
    "equal_row_or_column_operation": False,
    "pagination_or_formula_semantics": False,
    "arbitrary_table_shape_repair": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_layout.rs": (
        'TABLE_LAYOUT_HWPX_PROFILE_ID_V1: &str =',
        'TABLE_LAYOUT_HWPX_PROFILE_ID: &str = "hwpx-agent.table-layout-hwpx.hancom-2020/2"',
        "pub struct TableInnerMarginReadback",
        "pub inner_margin: TableInnerMarginReadback",
        "source_shape.readback.inner_margin",
        'bounded_u32(value, "left", limits)',
        "value > limits.0.dimension_hwpunit",
        "pub struct TableLayoutHwpxLowerer",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_LAYOUT_HWPX_PROFILE_ID_V1",
        "TableInnerMarginReadback",
    ),
    "crates/hwpx-package/tests/table_layout.rs": (
        "after.inner_margin, before.inner_margin",
        "after.inner_margin.left_hwpunit, 510",
        "margin_source",
        "Err(TableLayoutHwpxError::OutOfRange)",
    ),
    "crates/hwpx-package/examples/p06_05_table_layout_source_diagnostic.rs": (
        "hwpx-agent.p06-05-table-layout-source-diagnostic/v1",
        "inner_margin_hwpunit={},{},{},{}",
        "readback.inner_margin.left_hwpunit",
    ),
    "crates/hwpx-package/examples/p06_05_table_layout_target_fixture.rs": (
        "EXPECTED_SOURCE_INNER_MARGIN",
        "df47d07aa15a6493ed52bcddfbd594ff255d9566138ab7137f90b13fedd2ed98",
        "[52_990, 17_010]",
        "[13_758, 4_586]",
        '"Preview/PrvText.txt"',
        ".create_new(true)",
        "target.layout.inner_margin != source.layout.inner_margin",
        "TableLayoutHwpxLowerer::lower_in_section_with_receipt",
    ),
    "implementation/p06/P06-05_HWPX_LAYOUT_POLICY.md": (
        "hwpx-agent.table-layout-hwpx.hancom-2020/2",
        "TableInnerMarginReadback",
        "Preview/PrvImage.png",
        "NOT RUN",
    ),
    REPORT_RELATIVE.as_posix(): (
        "a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc",
        "c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab",
        "NOT RUN",
        "P06-05 is not complete",
    ),
    "crates/hwpx-package/Cargo.toml": (
        'domain-ir = { version = "0.1.0", path = "../domain-ir" }',
    ),
}


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract_path = v1.base.bounded_file(root, CONTRACT_RELATIVE.as_posix(), 256_000)
        contract = v1.load_contract(contract_path)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-layout-hwpx-contract/v2",
        "model_schema_version": "hwpx-agent.table-layout-hwpx.hancom-2020/2",
        "scope": (
            "p06_05_exact_current_pc_hancom_2020_hwpx_table_layout_lowering_and_readback_component"
        ),
        "prerequisites": [
            "hwpx-agent.table-layout-hwpx.hancom-2020/1",
            "hwpx-agent.table-layout/v1",
            "hwpx-agent.table-grid/v1",
            "hwpx-agent.table-cell-style.hancom-2020/2",
            "hwpx-agent.p06-05-current-font-metric-receipt/v1",
            "p03_preserving_xml_exact_source_spans",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "capabilities": EXPECTED_CAPABILITIES,
        "default_limits": EXPECTED_LIMITS,
        "atomicity": (
            "source_and_font_receipt_bytes_are_immutable_and_only_a_fully_reparsed_exact_v2_"
            "layout_margin_content_and_package_result_returns"
        ),
        "migration": MIGRATION_RELATIVE.as_posix(),
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    if contract.get("predecessor") != {
        "path": PREDECESSOR_RELATIVE.as_posix(),
        "sha256": PREDECESSOR_SHA256,
    }:
        errors.append("predecessor")
    try:
        predecessor = v1.base.bounded_file(root, PREDECESSOR_RELATIVE.as_posix(), 256_000)
        if hashlib.sha256(predecessor.read_bytes()).hexdigest() != PREDECESSOR_SHA256:
            errors.append("predecessor_digest")
    except (OSError, ValueError):
        errors.append("predecessor_path")

    required_objects = {
        "plan_admission": {"verification", "grid_binding", "shape", "totals", "font_receipt"},
        "current_2020_shape": {
            "roots", "table", "inner_margin", "rows", "cells", "coverage", "unknown_shape"
        },
        "quantization": {
            "unit", "table_width", "table_height", "merged_cell", "solver_margin_input"
        },
        "lowering": {
            "entrypoints", "mutation", "inner_margin_identity", "sibling_preservation",
            "readback", "receipt",
        },
        "target_fixture": {"source", "font_receipt", "plan", "target", "preview", "runtime_gate"},
        "source_evidence": {"owpml", "solver", "actual_observation", "runtime_target"},
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    for key, minimum in (("validation_order", 8), ("failure_policy", 9)):
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
                actual = v1.base.sha256_utf8_lf(v1.base.bounded_file(root, relative))
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual != digest:
                errors.append("source_lock_digest")
        if declared != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = v1.base.bounded_file(
            root, MIGRATION_RELATIVE.as_posix(), 256_000
        ).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.table-layout-hwpx.hancom-2020/1",
            "no automatic",
            "dimension_hwpunit",
            "Only existing `hp:sz`",
            "Preview/PrvImage.png",
            "Hangul 2024",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = v1.base.bounded_file(root, relative).read_text(encoding="utf-8")
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
        "schema_version": "hwpx-agent.p06-table-layout-hwpx-v2-validation/v1",
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
        "P06_TABLE_LAYOUT_HWPX_V2_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
