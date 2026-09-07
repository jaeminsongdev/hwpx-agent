#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-formula-v1.json")
MIGRATION = "protocol/migrations/p06-table-formula-v0-to-v1.md"
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "FEATURE_COVERAGE_MATRIX.csv",
    "specs/capability-contracts.generated.json",
    "specs/examples/recipes/04_advanced_table.json",
}
EXPECTED_CAPABILITIES = [
    "table.block_sum",
    "table.block_average",
    "table.block_product",
    "table.horizontal_sum",
    "table.vertical_sum",
    "table.horizontal_average",
    "table.vertical_average",
    "table.horizontal_product",
    "table.vertical_product",
    "table.formula",
    "table.number_format",
    "table.formula_relative_ref",
    "table.formula_absolute_ref",
    "table.formula_cache",
]
EXPECTED_LIMITS = {
    "input_bytes": 8 * 1024,
    "nodes": 2_048,
    "depth": 64,
    "function_arguments": 256,
    "cache_text_bytes": 4 * 1024,
    "rows": 10_000,
    "columns": 1_024,
    "decimal_places": 12,
    "serialized_bytes": 1024 * 1024,
}
EXPECTED_NOT_CLAIMED = {
    "formula_evaluation_correctness": False,
    "dependency_graph_or_cycle_detection": False,
    "arbitrary_or_locale_specific_function_grammar": False,
    "currency_date_or_custom_number_format": False,
    "hwpx_formula_lowering_or_readback": False,
    "hancom_2020_formula_oracle": False,
    "formula_cache_value_verified_without_oracle_receipt": False,
    "pagination_or_render": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_06_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_formula.rs": (
        'TABLE_FORMULA_SCHEMA_VERSION: &str = "hwpx-agent.table-formula/v1"',
        "pub struct FormulaAst",
        "pub struct FormulaCell",
        "pub enum FormulaReferenceKind",
        "pub struct FormulaGridDimensions",
        "pub enum FormulaGridEdit",
        "pub enum FormulaCache",
        "pub enum FormulaCachePolicy",
        "pub enum FormulaNumberFormat",
        "pub fn parse",
        "pub fn rebase",
        "pub fn apply_grid_edit",
        "pub fn canonical_json",
        "pub fn canonical_sha256",
        "CachePreservationConflict",
        "ReferenceDeleted",
        "OwnerDeleted",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_formula;",
        "FormulaAst",
        "FormulaCell",
        "TABLE_FORMULA_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_formula.rs": (
        "parser_normalizes_arithmetic_functions_ranges_and_anchors",
        "parser_rejects_unknown_locale_and_malformed_syntax",
        "rebase_moves_only_relative_reference_axes",
        "structural_edits_update_absolute_and_relative_references",
        "cache_policy_is_explicit_and_formula_bound",
        "cache_and_number_format_tamper_fail_closed",
        "owner_deletion_and_exact_grid_escape_fail_atomically",
        "deterministic_256_case_reference_move_corpus",
        "public_errors_and_debug_redaction_are_stable",
    ),
    "implementation/p06/P06-06_FORMULA_AST_POLICY.md": (
        "FormulaAst",
        "Copy/rebase and structural table edits are distinct operations",
        "cannot manufacture an oracle-qualified value",
        "does not implement formula evaluation",
    ),
}


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def bounded_file(root: Path, relative: str, maximum: int = 16_000_000) -> Path:
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
        contract = load_contract(bounded_file(root, CONTRACT_RELATIVE.as_posix(), 512_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.table-formula-contract/v1",
        "model_schema_version": "hwpx-agent.table-formula/v1",
        "scope": "p06_06_pure_formula_ast_reference_cache_number_format_component_current_pc_local_development",
        "prerequisites": [
            "hwpx-agent.table-grid/v1",
            "checked_zero_based_cell_coordinates",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "component_capabilities": EXPECTED_CAPABILITIES,
        "grammar": {
            "encoding": "bounded_ascii_locale_neutral",
            "literals": "exact_base10_i64_coefficient_and_scale_without_exponent_or_redundant_fractional_zeroes",
            "references": "uppercase_A1_output_with_independent_dollar_anchored_row_and_column_axes",
            "ranges": "ordered_rectangular_two_endpoint_A1_ranges",
            "operators": [
                "unary_plus",
                "unary_minus",
                "add",
                "subtract",
                "multiply",
                "divide",
                "power",
            ],
            "functions": ["SUM", "AVG", "PRODUCT"],
            "canonical_output": "fully_parenthesized_no_whitespace_uppercase_functions_and_references",
        },
        "reference_transform": {
            "copy_rebase": "exact_current_dimensions_are_required_relative_axes_shift_by_owner_delta_and_absolute_axes_remain_fixed",
            "structural_insert_delete": "exact_pre_edit_dimensions_are_required_and_both_relative_and_absolute_axes_follow_surviving_cells_into_checked_post_dimensions",
            "range_interior_edit": "surviving_endpoints_expand_or_contract_deterministically",
            "deleted_endpoint": "fail_closed_without_broken_reference_or_partial_result",
            "bounds": "zero_based_rows_and_columns_must_remain_inside_nonzero_exact_dimensions_and_configured_hard_limits",
        },
        "cache": {
            "separation": "formula_ast_and_cached_result_are_distinct_fields",
            "states": ["absent", "unverified"],
            "oracle_binding": "not_admitted_by_this_pure_component_and_requires_a_later_receipt_verifying_adapter",
            "preserve": "allowed_only_when_canonical_formula_digest_is_unchanged",
            "clear": "produces_absent_cache_and_rejects_a_replacement",
            "update": "requires_a_non_absent_explicitly_unverified_replacement",
        },
        "number_formats": {
            "supported": ["general", "number", "percent", "scientific"],
            "decimal_places": "bounded_unsigned_exact_value",
            "target_compilation": "deferred_until_exact_HWPX_and_Hancom_2020_source_evidence",
        },
        "determinism": {
            "ast": "closed_tagged_enums_and_canonical_decimal_normalization",
            "serialization": "bounded_serde_field_order_JSON_with_strict_exact_grid_formula_cell_readback",
            "digest": "sha256_over_canonical_JSON",
            "privacy": "Debug_redacts_formula_literals_cache_text_and_values",
        },
        "default_limits": EXPECTED_LIMITS,
        "migration": MIGRATION,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    required_objects = {
        "grammar": {
            "encoding",
            "literals",
            "references",
            "ranges",
            "operators",
            "functions",
            "canonical_output",
        },
        "reference_transform": {
            "copy_rebase",
            "structural_insert_delete",
            "range_interior_edit",
            "deleted_endpoint",
            "bounds",
        },
        "cache": {"separation", "states", "oracle_binding", "preserve", "clear", "update"},
        "number_formats": {"supported", "decimal_places", "target_compilation"},
        "determinism": {"ast", "serialization", "digest", "privacy"},
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    grammar = contract.get("grammar")
    if not isinstance(grammar, dict) or grammar.get("functions") != ["SUM", "AVG", "PRODUCT"]:
        errors.append("grammar_functions")
    cache = contract.get("cache")
    if not isinstance(cache, dict) or cache.get("states") != [
        "absent",
        "unverified",
    ]:
        errors.append("cache_states")
    formats = contract.get("number_formats")
    if not isinstance(formats, dict) or formats.get("supported") != [
        "general",
        "number",
        "percent",
        "scientific",
    ]:
        errors.append("number_format_supported")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) < 11
        or any(not isinstance(value, str) or not value for value in failure_policy)
    ):
        errors.append("failure_policy")

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
            "hwpx-agent.table-formula/v1",
            "fail closed",
            "Cached results migrate separately",
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

    return result(errors=errors, source_locks=source_count, implementation_files=implementation_files)


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-formula-validation/v1",
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
        "P06_TABLE_FORMULA_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
