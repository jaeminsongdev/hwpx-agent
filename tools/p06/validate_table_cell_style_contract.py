#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_grid_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_grid_contract.py")
    specification = importlib.util.spec_from_file_location("p06_grid_validator", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table grid validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


grid_validator = load_grid_validator()
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-cell-style-v1.json")
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "implementation/p02/evidence/owpml/owpml.records.v1.json",
    "implementation/p02/evidence/automation/automation-pdf.records.v1.json",
}
EXPECTED_CAPABILITIES = [
    "table.cell_padding",
    "table.cell_border",
    "table.cell_fill",
    "table.cell_alignment",
    "table.cell_text_direction",
    "table.cell_protection",
]
EXPECTED_NOT_CLAIMED = {
    "new_border_fill_catalog_insertion": False,
    "arbitrary_table_shape_repair": False,
    "formula_or_layout_semantics": False,
    "general_public_automation_route": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "phase_complete": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_cell_style.rs": (
        'TABLE_CELL_STYLE_PROFILE_ID: &str = "hwpx-agent.table-cell-style.hancom-2020/1"',
        "pub struct CellMargins",
        "pub enum CellTextDirection",
        "pub enum CellVerticalAlignment",
        "pub enum CellProtection",
        "pub struct TableCellStyle",
        "pub struct TableCellStyleReader",
        "pub struct TableCellStyleLowerer",
        "pub fn count_in_section",
        "pub fn read_in_section",
        "pub fn lower_in_section_with_receipt",
        "CellLimit",
        "CatalogInvalid",
        "content_sha256",
        "ReferenceMismatch",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "mod table_cell_style;",
        "TableCellStyleLowerer",
        "TABLE_CELL_STYLE_PROFILE_ID",
    ),
    "crates/hwpx-package/tests/table_cell_style.rs": (
        "lowers_every_style_dimension_and_preserves_content",
        "all_direction_alignment_and_protection_variants_round_trip",
        "selected_section_cell_changes_without_touching_its_sibling",
        "dangling_and_mismatched_references_fail_closed",
        "malformed_shapes_and_noncanonical_absent_margin_fail_closed",
    ),
    "crates/hwpx-package/examples/p06_04_table_cell_style_target_fixture.rs": (
        "TableCellStyleReader::read_in_section",
        "TableCellStyleReader::count_in_section",
        "TableCellStyleLowerer::lower_in_section",
        "target_styles",
        "compose_target_package",
        "create_new(true)",
        "source changed while target was built",
    ),
    "implementation/p06/tools/create-hancom-2020-table-source.ps1": (
        "HWPFrame.HwpObject.2",
        "11.0.0.9136",
        "HTableCreation",
        "TableCreate",
        "TableCellAlignCenterCenter",
        "TableCellTextVertAll",
        "SaveAs($output, 'HWPX', '')",
        "SaveAs($pdf, 'PDF', '')",
        "computer_use_click_or_type_invoked = $false",
    ),
    "implementation/p06/tools/run-hancom-2020-cell-style-readback.ps1": (
        "invoke-hancom-2020-bounded-readback.ps1",
        "hwpx-agent.p06-04-hancom-2020-cell-style-readback/v1",
        "TABLE_CELL_STYLE_READBACK",
        "ExpectedInputSha256",
        "ExpectedTextSha256",
        "RenderPdfPath",
        "TimeoutSeconds",
    ),
    "implementation/p06/tests/Test-Hancom2020CellStyleReadback.ps1": (
        "all_scripts_parse",
        "preflight_fails_before_com",
        "process_cleanup",
        "no_register_module",
        "no_ui_input",
        "no_network",
        "no_registry_write",
    ),
}


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=grid_validator.reject_duplicate_keys,
    )
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract_path = grid_validator.bounded_file(root, CONTRACT_RELATIVE.as_posix())
        contract = load_contract(contract_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-cell-style-contract/v1",
        "model_schema_version": "hwpx-agent.table-cell-style.hancom-2020/1",
        "prerequisites": [
            "hwpx-agent.paragraph-style/1",
            "p03_preserving_xml_exact_source_spans",
        ],
        "scope": "p06_04_current_pc_hancom_2020_cell_style_lowering_and_readback",
        "source_lock_canonicalization": "utf8_lf_sha256",
        "atomicity": (
            "source_bytes_are_immutable_and_only_a_fully_reparsed_semantically_equal_result_returns"
        ),
        "runtime_readback": (
            "bounded_x86_sta_watchdog_exact_input_and_text_digests_save_reopen_pdf_and_zero_process_residue"
        ),
        "migration": "protocol/migrations/p06-table-cell-style-v0-to-v1.md",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)
    if contract.get("capabilities") != EXPECTED_CAPABILITIES:
        errors.append("capabilities")
    if contract.get("not_claimed") != EXPECTED_NOT_CLAIMED:
        errors.append("not_claimed")

    required_objects = {
        "representation": {
            "margins", "border_and_fill", "horizontal_alignment", "vertical_alignment",
            "text_direction", "protection",
        },
        "current_2020_shape": {
            "cell", "paragraphs", "reference_width", "unknown_style_attribute",
            "unrelated_cell_content",
        },
        "lowering": {
            "entrypoints", "mutation", "margins_absent", "paragraph_alignment", "readback",
            "receipt",
        },
        "source_evidence": {"owpml", "automation", "runtime_target"},
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    for key in ("validation_order", "failure_policy"):
        value = contract.get(key)
        if not isinstance(value, list) or not value or any(not isinstance(item, str) for item in value):
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
                actual = grid_validator.sha256_utf8_lf(
                    grid_validator.bounded_file(root, relative)
                )
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual != digest:
                errors.append("source_lock_digest")
        if declared != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = grid_validator.bounded_file(
            root, "protocol/migrations/p06-table-cell-style-v0-to-v1.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.table-cell-style.hancom-2020/1",
            "borderFillIDRef",
            "paraPrIDRef",
            "fail closed",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = grid_validator.bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")

    return result(
        errors=sorted(errors),
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-cell-style-validation/v1",
        "state": "pass" if not errors else "fail",
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "errors": errors,
    }


def main() -> int:
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["errors"]:
        return 1
    print("P06_TABLE_CELL_STYLE_CONTRACT_PASS source_locks=6 implementation_files=7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
