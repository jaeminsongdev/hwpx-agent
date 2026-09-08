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
CONTRACT = "protocol/private/p06-table-text-conversion-v1.json"
MIGRATION = "protocol/migrations/p06-table-text-conversion-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_TEXT_CONVERSION_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_TEXT_CONVERSION_REPORT.md"
EXPECTED_FEATURES = [
    {"feature_id": "TABLE-004", "capability_id": "table.text_to_table"},
    {"feature_id": "TABLE-005", "capability_id": "table.table_to_text"},
]
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/06_table_model.md",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
}
EXPECTED_LIMITS = {
    "input_bytes": 33_554_432,
    "output_bytes": 33_554_432,
    "rows": 10_000,
    "columns": 1_024,
    "cells": 1_000_000,
    "cell_bytes": 1_048_576,
    "serialized_bytes": 67_108_864,
}
EXPECTED_NOT_CLAIMED = {
    "locale_dependent_or_arbitrary_delimiters": False,
    "document_graph_table_mutation": False,
    "merged_cell_style_or_formula_preservation": False,
    "hwpx_table_lowering_or_readback": False,
    "hancom_2020_target_build": False,
    "pagination_or_render": False,
    "automation_or_differential": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_text_conversion.rs": (
        'TABLE_TEXT_CONVERSION_SCHEMA_VERSION: &str = "hwpx-agent.table-text-conversion/v1"',
        'TABLE_TEXT_TO_TABLE_CAPABILITY_ID: &str = "table.text_to_table"',
        'TABLE_TABLE_TO_TEXT_CAPABILITY_ID: &str = "table.table_to_text"',
        "pub struct TableTextConversionLimits",
        "pub enum TableDelimiter",
        "pub enum TableLineEnding",
        "pub struct TableTextGrid",
        "pub fn parse_delimited",
        "pub fn to_delimited",
        "pub fn canonical_sha256",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_text_conversion;",
        "TableTextConversionLimits",
        "TableTextGrid",
        "TABLE_TEXT_CONVERSION_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_text_conversion.rs": (
        "tab_text_parses_to_exact_rectangular_unicode_grid",
        "quoted_csv_accepts_crlf_delimiters_quotes_and_semantic_newlines",
        "deterministic_writer_quotes_minimally_and_roundtrips_both_line_endings",
        "final_record_ending_and_empty_fields_are_unambiguous",
        "malformed_quotes_line_endings_controls_and_ragged_rows_fail_closed",
        "strict_grid_json_rejects_duplicate_unknown_version_and_invalid_content",
        "every_finite_limit_is_enforced",
        "canonical_json_sha_and_debug_are_deterministic_and_private",
        "public_error_codes_are_stable",
    ),
    POLICY: (
        "pure bounded component implemented; no HWPX or Hangul 2020 oracle claim",
        "tab, comma and semicolon",
        "no partial grid or byte vector",
        "unit_passed",
    ),
    REPORT: (
        "Result: `component_pass`",
        "9/9 PASS",
        "cataloged`: 20 to 18",
        "unit_passed`: 23 to 25",
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
        "syntax",
        "semantics",
        "default_limits",
        "failure_policy",
        "not_claimed",
        "gate_decision",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-text-conversion-contract/v1",
        "model_schema_version": "hwpx-agent.table-text-conversion/v1",
        "scope": "p06_09_pure_delimited_text_grid_component_current_pc_local_development",
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
            "actual_document_graph": False,
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

    syntax = contract.get("syntax")
    if not isinstance(syntax, dict) or set(syntax) != {
        "encoding",
        "delimiters",
        "quotes",
        "input_line_endings",
        "semantic_cell_line_ending",
        "output_line_endings",
        "final_record_ending",
    }:
        add_error(errors, "syntax")
    elif (
        syntax.get("encoding") != "utf8_only"
        or syntax.get("delimiters") != ["tab", "comma", "semicolon"]
        or syntax.get("input_line_endings") != ["LF", "CRLF"]
        or syntax.get("semantic_cell_line_ending") != "LF"
        or syntax.get("final_record_ending") != "not_emitted"
    ):
        add_error(errors, "syntax_semantics")
    semantics = contract.get("semantics")
    if not isinstance(semantics, dict) or set(semantics) != {
        "grid",
        "empty_fields",
        "text_to_table",
        "table_to_text",
        "roundtrip",
        "privacy",
    }:
        add_error(errors, "semantics")
    elif (
        semantics.get("grid") != "nonempty_rectangular_rows_and_columns"
        or semantics.get("roundtrip") != "writer_output_reparses_to_exact_semantic_grid"
        or semantics.get("privacy") != "debug_redacts_cell_content"
    ):
        add_error(errors, "semantics_behavior")

    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 12
        or len(set(failure_policy)) != 12
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
        "hwpx-agent.table-text-conversion/v1",
        "bounded UTF-8",
        "no partial output",
        "may not promote",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-text-conversion-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 2,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "actual_document_graph": False,
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
        "P06_TABLE_TEXT_CONVERSION_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
