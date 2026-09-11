#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-latex-adapter-v1.json"
MIGRATION = "protocol/migrations/p07-latex-adapter-v0-to-v1.md"
POLICY = "implementation/p07/P07-02_LATEX_ADAPTER_POLICY.md"
REPORT = "implementation/p07/P07-02_LATEX_ADAPTER_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md",
    "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
}
EXPECTED_FEATURES = [
    "EQ-003",
    "EQ-009",
    "EQ-010",
    "EQ-011",
    "EQ-012",
    "EQ-013",
    "EQ-014",
    "EQ-015",
    "EQ-016",
    "EQ-017",
    "EQ-018",
    "EQ-019",
    "EQ-020",
    "EQ-024",
    "EQ-025",
    "EQ-026",
]
EXPECTED_LIMITS = {
    "source_bytes": 1_048_576,
    "input_tokens": 16_384,
    "expanded_tokens": 32_768,
    "parse_depth": 128,
    "macro_definitions": 64,
    "macro_parameters": 4,
    "macro_expansion_depth": 16,
    "macro_expansions": 4_096,
    "macro_replacement_bytes": 65_536,
    "total_macro_bytes": 1_048_576,
    "ambiguity_sites": 64,
    "ambiguity_candidates": 4,
    "serialized_bytes": 8_388_608,
}
EXPECTED_ADMITTED = {
    "literals": "exact_decimal_unicode_alphabetic_identifier_non_nested_text",
    "operators": "explicit_arithmetic_relation_logic_set_factorial_subscript_superscript",
    "structures": "fraction_root_function_delimiter_accent_large_operator_derivative_binomial_set_builder",
    "symbols": "p07_01_greek_and_fixed_symbol_set",
    "styles": "semantic_safe_math_variant_hints_only",
    "derivative_source": "adapter_versioned_dv_or_pdv_optional_positive_order_expression_variable",
    "tier_b_c": "unsupported_until_separate_corpus_and_adapter_evidence",
}
EXPECTED_AMBIGUITY = {
    "kinds": [
        "implicit_multiplication",
        "bare_multi_letter_identifier",
        "function_application",
        "unary_minus_power",
    ],
    "site_identity": "kind_start_byte_end_byte",
    "candidate_strategy": ["conventional_latex", "literal_adjacency"],
    "confidence_millionths": [600_000, 400_000],
    "confidence_basis": "deterministic_syntax_preference_not_empirical_probability",
    "automatic_selection": False,
}
EXPECTED_MACROS = {
    "name": "one_to_thirty_two_ascii_letters_non_reserved",
    "parameters": "zero_to_four_grouped_arguments_with_hash_one_to_hash_four",
    "span_binding": "replacement_tokens_bind_to_exact_invocation_span",
    "recursion": "direct_and_indirect_rejected",
    "limits": "definition_parameter_replacement_aggregate_depth_expansion_and_token_bounds",
}
EXPECTED_NOT_CLAIMED = {
    "full_latex": False,
    "full_tier_a_b_c_corpus": False,
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
    "adapter_schema_version",
    "parser_version",
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
    "admitted_profile",
    "ambiguity",
    "macro_sandbox",
    "default_limits",
    "failure_policy",
    "not_claimed",
    "gate_decision",
}
IMPLEMENTATION_MARKERS = {
    "Cargo.toml": ('"crates/equation-engine"',),
    "Cargo.lock": ('name = "equation-engine"',),
    "crates/equation-engine/Cargo.toml": (
        'name = "equation-engine"',
        'domain-ir = { path = "../domain-ir" }',
    ),
    "crates/equation-engine/src/lib.rs": (
        "mod latex;",
        "LATEX_ADAPTER_SCHEMA_VERSION",
        "LatexParseOutcome",
    ),
    "crates/equation-engine/src/latex.rs": (
        'LATEX_ADAPTER_SCHEMA_VERSION: &str = "hwpx-agent.latex-adapter/v1"',
        'LATEX_PARSER_VERSION: &str = "hwpx-agent.latex-parser/tier-a-v1"',
        "pub struct LatexAdapterLimits",
        "fn expand_sequence",
        "MacroRecursion",
        "pub enum LatexAmbiguityKind",
        "deterministic_syntax_preference_not_empirical_probability",
        "pub fn canonical_json",
    ),
    "crates/equation-engine/tests/latex_adapter.rs": (
        "explicit_tier_a_corpus_has_no_silent_ambiguity_or_approximation",
        "ambiguous_sources_return_two_candidates_without_selecting_one",
        "macro_conflict_recursion_parameter_and_expansion_limits_fail_closed",
        "strict_json_rejects_duplicates_unknown_fields_and_wrong_versions",
        "canonical_result_and_debug_are_deterministic_bounded_and_redacted",
    ),
    POLICY: (
        "component_only / unit_passed",
        "Two deterministic whole-source candidates",
        "P07-08 owns the later complete A/B/C corpus Gate",
        "false` / `not_run",
    ),
    REPORT: (
        "component_pass",
        "11/11 PASS",
        "44/44 PASS",
        "P07 remains in progress",
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
        "schema_version": "hwpx-agent.latex-adapter-contract/v1",
        "adapter_schema_version": "hwpx-agent.latex-adapter/v1",
        "parser_version": "hwpx-agent.latex-parser/tier-a-v1",
        "model_schema_version": "hwpx-agent.math-ast/v1",
        "normalization_version": "hwpx-agent.math-ast-normalization/v1",
        "scope": "p07_02_finite_latex_to_math_ast_local_component",
        "task": "P07-02",
        "feature_boundary": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    for key, expected in (
        ("admitted_profile", EXPECTED_ADMITTED),
        ("ambiguity", EXPECTED_AMBIGUITY),
        ("macro_sandbox", EXPECTED_MACROS),
        ("default_limits", EXPECTED_LIMITS),
        ("not_claimed", EXPECTED_NOT_CLAIMED),
        ("gate_decision", EXPECTED_GATE),
    ):
        if contract.get(key) != expected:
            add_error(errors, key)
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 16
        or len(set(failure_policy)) != len(failure_policy)
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        add_error(errors, "failure_policy")
    if contract.get("implementation_files") != list(IMPLEMENTATION_MARKERS):
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
        "hwpx-agent.latex-adapter/v1",
        "There is no stored v0 adapter result",
        "MUST NOT select the preferred candidate automatically",
        "separate P07 Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-latex-adapter-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "task": "P07-02",
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
        "P07_LATEX_ADAPTER_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
