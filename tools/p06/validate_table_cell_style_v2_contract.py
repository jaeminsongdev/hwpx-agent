#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_v1_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_cell_style_contract.py")
    specification = importlib.util.spec_from_file_location("p06_cell_style_v1_validator", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table cell style v1 validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


v1 = load_v1_validator()


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-cell-style-v2.json")
PREDECESSOR_RELATIVE = PurePosixPath("protocol/private/p06-table-cell-style-v1.json")
PREDECESSOR_SHA256 = "8788b6a5dd96d56d40c9bc3f5dfaf3ea307efdaa5c1ee66700a48dd7cf51ff08"
MIGRATION_RELATIVE = PurePosixPath("protocol/migrations/p06-table-cell-style-v1-to-v2.md")
EXPECTED_SOURCE_PATHS = v1.EXPECTED_SOURCE_PATHS
EXPECTED_CAPABILITIES = v1.EXPECTED_CAPABILITIES
EXPECTED_NOT_CLAIMED = v1.EXPECTED_NOT_CLAIMED
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/preservation.rs": (
        "pub enum PreservationRuleProfile",
        "CoreV1",
        "Hangul2020PreviewTextV2",
        "build_with_graph_limits_and_profile",
        'part.path.as_str() == "Preview/PrvText.txt"',
        'part.media_type.as_str() == "text/plain"',
    ),
    "crates/hwpx-package/tests/preservation_map.rs": (
        "exact_plain_text_preview_may_start_with_table_angle_brackets",
        "PreservationRuleProfile::Hangul2020PreviewTextV2",
        "preservation_rejected_xml_content_media_mismatch",
        "angle_bracket_text_outside_exact_preview_path_stays_rejected",
    ),
    "crates/hwpx-package/src/id_index.rs": (
        "current_hancom_2020_core_v1",
        "current_hancom_2020_table_v2",
        '"hancom-2020-hwpml-2011-table/v2"',
        "preservation_profile",
        "includes_table_rules",
        "IdKind::Table",
        "IdKind::SubList",
        "linkListNextIDRef",
    ),
    "crates/hwpx-package/tests/id_index.rs": (
        "table_v2_adds_typed_table_domains_without_weakening_core_v1",
        "core v1 silently accepted table ID domains",
        'linkListIDRef=\\"20\\"',
        "dangling sub-list reference was accepted",
    ),
    "crates/hwpx-package/src/table_cell_style.rs": (
        "TABLE_CELL_STYLE_HANCOM_2020_PROFILE_ID",
        "pub enum TableCellStyleProfile",
        "Hangul2020V2",
        "read_in_section_with_profile",
        "lower_in_section_with_profile_and_receipt",
        "Preserve those exact spans",
        '["subList", "cellAddr", "cellSpan", "cellSz", "cellMargin"]',
    ),
    "crates/hwpx-package/tests/table_cell_style.rs": (
        "exact_hangul_2020_v2_order_is_explicit_and_preserving",
        "hangul_2020_v2_preserves_inactive_default_margin_numbers",
        "v1 silently accepted the v2 child order",
        "v1 silently accepted inactive nonzero margins",
    ),
    "crates/hwpx-package/examples/p06_04_table_cell_style_target_fixture.rs": (
        "IdRuleProfile::current_hancom_2020_table_v2()",
        "TableCellStyleProfile::Hangul2020V2",
        "create_new(true)",
        "source changed while target was built",
    ),
    "implementation/p06/P06-04_CELL_STYLE_POLICY.md": (
        "hwpx-agent.table-cell-style.hancom-2020/2",
        "Immutable predecessor",
        "inactive numeric spans",
        "there is no auto-detection",
        "Hangul 2022 and 2024 remain deferred",
    ),
}


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=v1.grid_validator.reject_duplicate_keys,
    )
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract_path = v1.grid_validator.bounded_file(root, CONTRACT_RELATIVE.as_posix())
        contract = load_contract(contract_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-cell-style-contract/v2",
        "model_schema_version": "hwpx-agent.table-cell-style.hancom-2020/2",
        "scope": "p06_04_exact_current_pc_hancom_2020_observed_cell_style_lowering_and_readback",
        "source_lock_canonicalization": "utf8_lf_sha256",
        "atomicity": "source_bytes_are_immutable_and_only_a_fully_reparsed_same_profile_semantically_equal_result_returns",
        "runtime_readback": "active_document_binding_pre_save_markers_bounded_x86_sta_watchdog_exact_input_and_text_digests_save_reopen_pdf_and_zero_process_residue",
        "migration": MIGRATION_RELATIVE.as_posix(),
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    expected_predecessor = {
        "path": PREDECESSOR_RELATIVE.as_posix(),
        "sha256": PREDECESSOR_SHA256,
    }
    if contract.get("predecessor") != expected_predecessor:
        errors.append("predecessor")
    try:
        predecessor = v1.grid_validator.bounded_file(root, PREDECESSOR_RELATIVE.as_posix())
        if hashlib.sha256(predecessor.read_bytes()).hexdigest() != PREDECESSOR_SHA256:
            errors.append("predecessor_digest")
    except (OSError, ValueError):
        errors.append("predecessor_path")

    expected_prerequisites = [
        "hwpx-agent.table-cell-style.hancom-2020/1",
        "hwpx-agent.paragraph-style/1",
        "hwpx-agent.preservation/hancom-2020-preview-text-v2",
        "hancom-2020-hwpml-2011-table/v2",
        "p03_preserving_xml_exact_source_spans",
    ]
    if contract.get("prerequisites") != expected_prerequisites:
        errors.append("prerequisites")
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
            "cell", "paragraphs", "reference_width", "table_id_profile",
            "preview_text_profile", "unknown_style_attribute", "unrelated_cell_content",
        },
        "lowering": {
            "entrypoints", "mutation", "margins_absent", "paragraph_alignment", "readback",
            "receipt",
        },
        "source_evidence": {"owpml", "automation", "actual_observation", "runtime_target"},
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
                actual = v1.grid_validator.sha256_utf8_lf(
                    v1.grid_validator.bounded_file(root, relative)
                )
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual != digest:
                errors.append("source_lock_digest")
        if declared != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = v1.grid_validator.bounded_file(root, MIGRATION_RELATIVE.as_posix()).read_text(
            encoding="utf-8"
        )
        for marker in (
            "hwpx-agent.table-cell-style.hancom-2020/1",
            "no automatic profile detection",
            'hasMargin="0"',
            "Preview/PrvText.txt",
            "Hangul 2022",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = v1.grid_validator.bounded_file(root, relative).read_text(encoding="utf-8")
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
        "schema_version": "hwpx-agent.p06-table-cell-style-v2-validation/v1",
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
    print("P06_TABLE_CELL_STYLE_V2_CONTRACT_PASS source_locks=6 implementation_files=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
