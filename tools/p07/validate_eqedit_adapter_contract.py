#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-eqedit-adapter-v1.json"
MIGRATION = "protocol/migrations/p07-eqedit-adapter-v0-to-v1.md"
POLICY = "implementation/p07/P07-04_EQEDIT_POLICY.md"
REPORT = "implementation/p07/P07-04_EQEDIT_REPORT.md"
QUALIFICATION = (
    "implementation/p07/evidence/"
    "p07-04-eqedit-source-qualification.current-2020.v1.json"
)
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "README.md",
    "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md",
    "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
    "implementation/p06/P06-07_TARGET_READBACK_REPORT.md",
    "crates/hwpx-package/examples/p06_07_table_pagination_target_fixture.rs",
}
EXPECTED_FEATURES = [
    "EQ-005",
    "EQ-006",
    *[f"EQ-{value:03d}" for value in range(9, 27)],
    "EQ-032",
]
EXPECTED_PARSER = {
    "atoms": "decimal_identifier_quoted_text_group_greek_fixed_symbol",
    "operators": "explicit_precedence_arithmetic_relation_set_logic_factorial_script_and_sup",
    "structures": "fraction_root_function_accent_annotation_large_operator_derivative_matrix_cases_aligned_binomial_set_builder_delimiter",
    "adjacency": "ordered_math_ast_row_never_inferred_multiplication_or_function_application",
    "delimiters": "matched_raw_parenthesis_bracket_or_canonical_left_right_including_bars",
    "derivative": "canonical_grouped_quotient_pattern_with_exact_positive_order_sum_only",
    "legacy": "from_to_scale_phantom_rejected_as_removed_in_current_help",
    "unmodeled_controls": "backslash_tilde_backtick_and_bare_vertical_bars_rejected",
}
EXPECTED_COMPILER = {
    "serialization": "deterministic_fully_grouped_current_profile",
    "roundtrip": "every_output_reparsed_and_semantically_equal_before_return",
    "distinct_semantics": "fraction_vs_divide_script_power_vs_apply_power_integral_cardinality_and_contour",
    "identifiers": "one_to_nine_ascii_alphanumeric_leading_letter_non_reserved",
    "text": "nonempty_without_undocumented_escape_or_structure_characters",
    "fallback": "no_partial_script_text_substitution_raw_xml_or_image",
    "unsupported": "typed_style_named_function_double_bar_matrix_permutation_payload_annotation_set_difference",
}
EXPECTED_QUALIFICATION_BOUNDARY = {
    "target": "licensed_hangul_2020_11_0_0_9136_x86_ko_kr_current_pc_only",
    "method": "read_only_installed_artifact_hashing_and_disposable_help_decompile",
    "p06_predecessor": "one_exact_script_has_independent_native_save_reopen_evidence",
    "new_engine_native_execution": False,
    "full_eqedit": False,
}
EXPECTED_CORPUS = {
    "focused_test_groups": 12,
    "comparison": "normalized_math_ast_semantic_equality",
    "cross_adapter_sources": ["latex", "mathml", "eqedit"],
    "native_roundtrip": False,
}
EXPECTED_LIMITS = {
    "source_bytes": 1_048_576,
    "tokens": 32_768,
    "token_bytes": 65_536,
    "parse_depth": 128,
    "compile_depth": 128,
    "script_bytes": 4_194_304,
    "serialized_bytes": 8_388_608,
}
EXPECTED_NOT_CLAIMED = {
    "full_eqedit": False,
    "legacy_eqedit_preservation": False,
    "equation_node_integration": False,
    "direct_hwpx_adapter": False,
    "package_mutation_or_preservation": False,
    "native_object_or_semantic_readback": False,
    "new_engine_hangul_2020_execution": False,
    "save_reopen_or_editor_smoke": False,
    "page_layout_or_render": False,
    "automation_or_differential": False,
    "other_hangul_versions": False,
    "p07_complete": False,
    "production_ready": False,
    "product_complete": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "direct_stage": "unit_passed",
    "installed_source_qualified": True,
    "actual_hwpx": False,
    "actual_hangul": False,
    "p07": "in_progress",
    "product_complete": False,
}
EXPECTED_KEYS = {
    "schema_version",
    "adapter_schema_version",
    "profile_version",
    "parser_version",
    "compiler_version",
    "model_schema_version",
    "normalization_version",
    "scope",
    "task",
    "feature_boundary",
    "source_lock_canonicalization",
    "source_locks",
    "source_qualification",
    "migration",
    "policy",
    "report",
    "implementation_files",
    "parser_profile",
    "compiler_profile",
    "qualification_boundary",
    "semantic_corpus",
    "default_limits",
    "failure_policy",
    "not_claimed",
    "gate_decision",
}
IMPLEMENTATION_MARKERS = {
    "Cargo.toml": ('"crates/equation-engine"',),
    "Cargo.lock": ('name = "equation-engine"',),
    "crates/equation-engine/Cargo.toml": ('name = "equation-engine"',),
    "crates/equation-engine/src/lib.rs": (
        "mod eqedit;",
        "EQEDIT_ADAPTER_SCHEMA_VERSION",
        "EqEditEngine",
    ),
    "crates/equation-engine/src/eqedit.rs": (
        'EQEDIT_ADAPTER_SCHEMA_VERSION: &str = "hwpx-agent.eqedit-adapter/v1"',
        'EQEDIT_PROFILE_VERSION: &str = "hwpx-agent.eqedit-profile/hangul-2020-canonical-v1"',
        "fn tokenize",
        "fn parse_word",
        "fn compile_node",
        'MathOperator::Power => Some("SUP")',
        "RoundTripMismatch",
        "canonical profile therefore requires LEFT/RIGHT for bars",
    ),
    "crates/equation-engine/tests/eqedit_adapter.rs": (
        "documented_precedence_fraction_script_root_and_function_are_typed",
        "exact_p06_hangul_2020_saved_script_is_admitted_without_native_promotion",
        "symbols_accents_large_operators_and_relations_roundtrip_semantically",
        "matrix_cases_aligned_set_and_derivative_roundtrip_semantically",
        "current_profile_commands_and_removed_legacy_forms_are_distinct",
        "finite_source_token_depth_compile_and_serialized_limits_are_enforced",
        "deterministic_generated_ast_script_roundtrip_property_corpus",
        "unsupported_ast_shapes_never_degrade_to_approximate_eqedit",
        "deterministic_receipts_and_debug_surfaces_are_bounded_and_redacted",
    ),
    POLICY: (
        "component_only / unit_passed",
        "11.0.0.9136",
        "Adjacent primaries are retained as an ordered `MathAst::Row`",
        "false` / `not_run",
    ),
    REPORT: (
        "component_pass",
        "12/12 PASS",
        "33/33 PASS",
        "not a P07, production or",
    ),
    QUALIFICATION: (
        '"schema_version": "hwpx-agent.eqedit-source-qualification/v1"',
        '"version": "11.0.0.9136"',
        '"actual_hangul_engine_execution": false',
        '"product_complete": false',
    ),
}
EXPECTED_ARTIFACTS = [
    ("Hwp.exe", 2_321_432, "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce", "11.0.0.9136"),
    ("Hwp.chm (ko-KR resource)", 9_628_648, "a38290fe91bfe4888f503f8fb906ce563241479a722162aa2ea571eed03afbc1", "not_applicable"),
    ("EqEditor.dll", 71_192, "146de2f857e3496ef9fc9d94eacb7b28a6f12985159650d4edba4771587385d9", "1.0.0.0"),
    ("eqeditor_commands.xml", 10_594, "04161f3919f1c71a4bf8bfc1fb34f95d488ee2c11f8c6a659510b018181fd183", "not_applicable"),
    ("eqeditor_data_sources.xml", 16_496, "776f261182125b2a11a22cdedd6c6bcc1ae2d10c133dd4cd06699d808db6564a", "not_applicable"),
]
EXPECTED_HELP = [
    ("equation(script).htm", 3_024, "2a2e3da93959f70e4778f73088d14c0de10a855048aa5c3f83a26755f3b69554"),
    ("equation(explanation).htm", 9_423, "ba00f92916494f8c42f69291d7111a6af0d2217a48238e9e352c3c5f6c57e242"),
    ("equation(rule).htm", 3_346, "c7bc18ce1b63049c838c4bc39e7f980278f73498e65f259a7c678d7ee1d9cb92"),
    ("equation(font).htm", 2_659, "2c473b347f8b16db8b6af0ef689b4ff841d0f04c2b58e3b4a5ecd0b6e2249261"),
]
EXPECTED_PUBLIC_SOURCES = [
    {
        "kind": "help",
        "url": "https://help.hancom.com/hoffice/multi/ko_kr/hwp/insert/equation/equation(explanation).htm",
    },
    {
        "kind": "equation_format_revision_1_2",
        "url": "https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D_%EC%88%98%EC%8B%9D_revision1.2.pdf",
    },
    {
        "kind": "open_format_download_page",
        "url": "https://swlab.hancom.com/support/downloadCenter/hwpOwpml",
    },
]
EXPECTED_OBSERVATIONS = {
    "grouping": "braces_group_quote_groups_long_text_hash_rows_ampersand_columns",
    "visual_spacing": "tilde_and_backtick_are_unmodeled_and_rejected",
    "font_switch": "backslash_is_unmodeled_and_rejected",
    "current_command_families": "fraction_root_script_function_symbol_accent_large_operator_matrix_cases_pile_binomial_delimiter",
    "integral_tokens": ["INT", "DINT", "TINT", "OINT", "ODINT", "OTINT"],
    "removed_legacy_commands": ["FROM", "TO", "SCALE", "PHANTOM"],
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


def load_json(root: Path, relative: str, maximum: int = 256_000) -> dict[str, Any]:
    value = json.loads(
        bounded_file(root, relative, maximum).read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )
    if not isinstance(value, dict):
        raise ValueError("JSON root")
    return value


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
        contract = load_json(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)

    if set(contract) != EXPECTED_KEYS:
        add_error(errors, "contract_keys")
    expected_scalars = {
        "schema_version": "hwpx-agent.eqedit-adapter-contract/v1",
        "adapter_schema_version": "hwpx-agent.eqedit-adapter/v1",
        "profile_version": "hwpx-agent.eqedit-profile/hangul-2020-canonical-v1",
        "parser_version": "hwpx-agent.eqedit-parser/hangul-2020-v1",
        "compiler_version": "hwpx-agent.eqedit-compiler/hangul-2020-v1",
        "model_schema_version": "hwpx-agent.math-ast/v1",
        "normalization_version": "hwpx-agent.math-ast-normalization/v1",
        "scope": "p07_04_finite_current_pc_hangul_2020_eqedit_math_ast_component",
        "task": "P07-04",
        "feature_boundary": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    for key, expected in (
        ("parser_profile", EXPECTED_PARSER),
        ("compiler_profile", EXPECTED_COMPILER),
        ("qualification_boundary", EXPECTED_QUALIFICATION_BOUNDARY),
        ("semantic_corpus", EXPECTED_CORPUS),
        ("default_limits", EXPECTED_LIMITS),
        ("not_claimed", EXPECTED_NOT_CLAIMED),
        ("gate_decision", EXPECTED_GATE),
    ):
        if contract.get(key) != expected:
            add_error(errors, key)
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 18
        or len(set(failure_policy)) != len(failure_policy)
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        add_error(errors, "failure_policy")
    if contract.get("implementation_files") != list(IMPLEMENTATION_MARKERS):
        add_error(errors, "implementation_files")

    source_count = validate_source_locks(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_migration(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


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


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load_json(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "qualification_json_or_path")
        return False
    expected_keys = {
        "schema_version", "task", "scope", "recorded_date", "target", "collection",
        "installed_artifacts", "extracted_help_members", "official_public_sources",
        "observations", "predecessor_fixture", "claims",
    }
    if set(value) != expected_keys:
        add_error(errors, "qualification_keys")
    if value.get("schema_version") != "hwpx-agent.eqedit-source-qualification/v1":
        add_error(errors, "qualification_version")
    if value.get("recorded_date") != "2026-09-11":
        add_error(errors, "qualification_date")
    if value.get("task") != "P07-04" or value.get("scope") != (
        "current_pc_installed_hangul_2020_eqedit_vocabulary_source_qualification_only"
    ):
        add_error(errors, "qualification_scope")
    if value.get("target") != {
        "product": "Hangul 2020", "version": "11.0.0.9136", "architecture": "x86",
        "locale": "ko-KR", "other_versions": "not_qualified",
    }:
        add_error(errors, "qualification_target")
    installed = value.get("installed_artifacts")
    if not isinstance(installed, list) or any(
        not isinstance(item, dict)
        or set(item) != {"name", "bytes", "sha256", "file_version"}
        for item in installed
    ):
        add_error(errors, "qualification_artifact_shape")
        installed = []
    observed_artifacts = [
        (item.get("name"), item.get("bytes"), item.get("sha256"), item.get("file_version"))
        for item in installed
    ]
    if observed_artifacts != EXPECTED_ARTIFACTS:
        add_error(errors, "qualification_artifacts")
    help_members = value.get("extracted_help_members")
    if not isinstance(help_members, list) or any(
        not isinstance(item, dict) or set(item) != {"name", "bytes", "sha256"}
        for item in help_members
    ):
        add_error(errors, "qualification_help_shape")
        help_members = []
    observed_help = [
        (item.get("name"), item.get("bytes"), item.get("sha256"))
        for item in help_members
    ]
    if observed_help != EXPECTED_HELP:
        add_error(errors, "qualification_help")
    if value.get("official_public_sources") != EXPECTED_PUBLIC_SOURCES:
        add_error(errors, "qualification_public_sources")
    if value.get("observations") != EXPECTED_OBSERVATIONS:
        add_error(errors, "qualification_observations")
    collection = value.get("collection")
    if not isinstance(collection, dict) or collection != {
        "installation_modified": False,
        "help_extraction": "hh.exe_-decompile_to_disposable_temporary_directory",
        "temporary_output_is_contract_input": False,
        "user_document_opened_or_modified": False,
        "network_or_application_resolver": False,
    }:
        add_error(errors, "qualification_collection")
    predecessor = value.get("predecessor_fixture")
    if not isinstance(predecessor, dict) or predecessor != {
        "fixture_path": "crates/hwpx-package/examples/p06_07_table_pagination_target_fixture.rs",
        "report_path": "implementation/p06/P06-07_TARGET_READBACK_REPORT.md",
        "script_sha256": "a25940543dddf8e6a34d6dd80b1f03aea0821e44ea668514bafc8f02f8167dcf",
        "licensed_hangul_2020_save_reopen_predecessor": True,
        "new_engine_executed_in_predecessor": False,
    }:
        add_error(errors, "qualification_predecessor")
    claims = value.get("claims")
    expected_claims = {
        "installed_source_qualification": True,
        "finite_profile_only": True,
        "full_eqedit": False,
        "actual_hwpx": False,
        "actual_hangul_engine_execution": False,
        "native_equation_readback": False,
        "save_reopen": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p07_complete": False,
        "production_ready": False,
        "product_complete": False,
    }
    if claims != expected_claims:
        add_error(errors, "qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_migration(root: Path, errors: list[str]) -> None:
    try:
        text = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "migration_path")
        return
    for marker in (
        "hwpx-agent.eqedit-adapter/v1",
        "There is no stored v0 EqEdit adapter request",
        "MUST NOT rewrite, escape, infer multiplication",
        "separate P07 Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(
    errors: list[str], source_locks: int, implementation_files: int, qualification: bool
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-eqedit-adapter-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "installed_source_qualified": qualification,
        "task": "P07-04",
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
        "P07_EQEDIT_ADAPTER_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']} "
        f"installed_source_qualified={str(validation['installed_source_qualified']).lower()}"
    )
