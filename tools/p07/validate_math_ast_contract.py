#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-math-ast-v1.json"
MIGRATION = "protocol/migrations/p07-math-ast-v0-to-v1.md"
POLICY = "implementation/p07/P07-01_MATH_AST_POLICY.md"
REPORT = "implementation/p07/P07-01_MATH_AST_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md",
    "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
}
EXPECTED_SEMANTICS = {
    "nodes": "typed_literals_operators_functions_fraction_script_root_accent_annotation_large_operator_derivative_delimiter_matrix_cases_aligned_combinatorial_set_builder",
    "source_spans": "nonempty_end_exclusive_within_exact_source_length_and_parent_contained",
    "normalization": "exact_decimal_unicode_nfc_empty_style_elision_positive_elision_row_and_associative_flattening_no_operand_reorder_degree_two_root_equivalence",
    "semantic_identity": "version_bound_projection_excludes_source_length_spans_and_visual_style_but_preserves_operator_order_content_and_structure",
    "serialization": "deterministic_complete_normalized_bounded_json_and_sha256",
    "ambiguity": "source_adapters_must_return_candidates_and_confidence_before_ast_admission",
}
EXPECTED_LIMITS = {
    "source_bytes": 1_048_576,
    "nodes": 8_192,
    "depth": 128,
    "children_per_node": 512,
    "matrix_rows": 256,
    "matrix_columns": 256,
    "string_bytes": 65_536,
    "total_string_bytes": 1_048_576,
    "serialized_bytes": 4_194_304,
}
EXPECTED_NOT_CLAIMED = {
    "latex_adapter": False,
    "mathml_adapter": False,
    "eqedit_parser_or_compiler": False,
    "equation_node_integration": False,
    "direct_hwpx_adapter": False,
    "package_mutation_or_preservation": False,
    "native_object_or_semantic_readback": False,
    "hancom_2020_target_build": False,
    "save_reopen_or_editor_smoke": False,
    "page_layout_or_render": False,
    "automation_or_differential": False,
    "p07_complete": False,
    "production_ready": False,
    "product_complete": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "actual_hwpx": False,
    "actual_hangul": False,
    "p07": "in_progress",
    "product_complete": False,
}
EXPECTED_KEYS = {
    "schema_version",
    "model_schema_version",
    "normalization_version",
    "scope",
    "task",
    "feature_boundary",
    "source_lock_canonicalization",
    "source_locks",
    "migration",
    "policy",
    "report",
    "implementation_files",
    "semantics",
    "default_limits",
    "failure_policy",
    "not_claimed",
    "gate_decision",
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod math_ast;",
        "MathAstDraft",
        "MathExpression",
        "MATH_AST_NORMALIZATION_VERSION",
    ),
    "crates/domain-ir/src/math_ast.rs": (
        'MATH_AST_SCHEMA_VERSION: &str = "hwpx-agent.math-ast/v1"',
        'MATH_AST_NORMALIZATION_VERSION: &str = "hwpx-agent.math-ast-normalization/v1"',
        "pub struct MathSourceSpan",
        "pub enum MathExpression",
        "pub struct MathAst",
        "pub fn semantic_sha256",
        "fn flatten_associative",
        "pub enum MathAstError",
    ),
    "crates/domain-ir/tests/math_ast.rs": (
        "normalizes_exact_numbers_and_unicode_without_losing_spans",
        "semantic_identity_ignores_spans_styles_positive_and_associative_grouping",
        "canonical_json_roundtrips_and_rejects_schema_tampering",
        "large_operators_and_multivariable_derivatives_are_complete",
        "matrix_cases_aligned_combinatorial_and_set_builder_are_complete",
        "finite_node_depth_and_source_limits_are_enforced",
        "finite_collection_string_and_output_limits_are_enforced",
        "error_codes_are_stable_and_content_free",
        "canonicalization_properties_hold_over_many_shapes_and_spellings",
        "debug_redacts_source_content_spans_and_tree_payloads",
    ),
    POLICY: (
        "component_only / unit_passed",
        "semantic projection excludes source length, spans and visual style",
        "Parser ambiguity is outside this layer",
        "## Gate boundary",
    ),
    REPORT: (
        "Result: `component_pass`",
        "19/19 PASS",
        "128 generated spelling/grouping/style variants",
        "false` / `not_run",
    ),
}


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    base = root.resolve()
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as error:
        raise ValueError("path traversal") from error
    if not candidate.is_file() or candidate.stat().st_size > maximum:
        raise ValueError("missing or oversized file")
    return candidate


def canonical_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def add_error(errors: list[str], error: str) -> None:
    if error not in errors:
        errors.append(error)


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

    if set(contract) != EXPECTED_KEYS:
        add_error(errors, "contract_keys")
    expected_scalars = {
        "schema_version": "hwpx-agent.math-ast-contract/v1",
        "model_schema_version": "hwpx-agent.math-ast/v1",
        "normalization_version": "hwpx-agent.math-ast-normalization/v1",
        "scope": "p07_01_pure_bounded_semantic_math_ast_local_component",
        "task": "P07-01",
        "feature_boundary": ["EQ-006"],
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    if contract.get("semantics") != EXPECTED_SEMANTICS:
        add_error(errors, "semantics")
    if contract.get("default_limits") != EXPECTED_LIMITS:
        add_error(errors, "default_limits")
    if contract.get("not_claimed") != EXPECTED_NOT_CLAIMED:
        add_error(errors, "not_claimed")
    if contract.get("gate_decision") != EXPECTED_GATE:
        add_error(errors, "gate_decision")
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 13
        or len(set(failure_policy)) != len(failure_policy)
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        add_error(errors, "failure_policy")
    implementation_files = contract.get("implementation_files")
    if implementation_files != list(IMPLEMENTATION_MARKERS):
        add_error(errors, "implementation_files")

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
            text = bounded_file(root, relative).read_text(encoding="utf-8")
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
        "hwpx-agent.math-ast/v1",
        "Existing documents",
        "non-empty contained source span",
        "Semantic identity",
        "separate P07 Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-math-ast-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "task": "P07-01",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "actual_hwpx": False,
        "actual_hangul": False,
        "p07": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        sys.exit(1)
    print(
        "P07_MATH_AST_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
