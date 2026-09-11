#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-mathml-adapter-v1.json"
MIGRATION = "protocol/migrations/p07-mathml-adapter-v0-to-v1.md"
POLICY = "implementation/p07/P07-03_MATHML_ADAPTER_POLICY.md"
REPORT = "implementation/p07/P07-03_MATHML_ADAPTER_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md",
    "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
    "implementation/p03/P03-03_SAFE_XML_POLICY.md",
}
EXPECTED_FEATURES = [
    "EQ-004",
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
    "EQ-021",
    "EQ-025",
    "EQ-026",
]
EXPECTED_XML_POLICY = {
    "encoding": "utf8_xml_1_0_only",
    "namespace": "every_element_exact_mathml_uri_prefix_independent",
    "entities": "five_predefined_and_valid_numeric_xml_scalar_only",
    "forbidden": "dtd_custom_entity_pi_cdata_comment_foreign_namespace_or_attribute",
    "resolver": "no_filesystem_network_process_or_application_resolver",
}
EXPECTED_PRESENTATION = {
    "tokens": "mn_mi_mo_mtext_with_exact_unicode_operator_and_symbol_allowlists",
    "structures": "row_fraction_root_script_fenced_accent_annotation_style_matrix_large_operator",
    "multiplication": "explicit_operator_or_u2062_required",
    "function_application": "u2061_required",
    "ambiguity": "adjacency_ordinary_function_form_relation_chain_rejected",
    "styles": "typed_mathvariant_and_hex_rgb_only",
}
EXPECTED_CONTENT = {
    "literals": "cn_exact_decimal_ci_identifier_cs_text_and_fixed_constants",
    "apply": "bounded_exact_operator_function_arity",
    "structures": "fraction_script_root_large_operator_derivative_matrix_set_builder",
    "qualifiers": "exact_degree_lowlimit_uplimit_bvar_condition_cardinality",
    "extensions": "unknown_csymbol_semantics_units_interval_vector_piecewise_aligned_unsupported",
}
EXPECTED_SELECTION = {
    "basis": "direct_root_child_element_family",
    "mixed_profiles": "rejected",
    "content_root_count": 1,
    "silent_inference": False,
}
EXPECTED_ROUNDTRIP = {
    "pair_count": 17,
    "comparison": "normalized_math_ast_semantic_equality",
    "mathml_serialization": False,
    "native_roundtrip": False,
}
EXPECTED_LIMITS = {
    "source_bytes": 1_048_576,
    "events": 65_536,
    "elements": 8_192,
    "depth": 128,
    "text_bytes": 65_536,
    "total_text_bytes": 1_048_576,
    "attributes_per_element": 8,
    "attribute_bytes": 65_536,
    "namespace_bindings": 2_048,
    "children_per_element": 512,
    "parser_depth": 128,
    "serialized_bytes": 8_388_608,
}
EXPECTED_NOT_CLAIMED = {
    "full_mathml_3_or_4": False,
    "full_content_or_presentation_mathml": False,
    "full_tier_a_b_c_corpus": False,
    "mathml_serializer": False,
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
    "profile_version",
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
    "xml_policy",
    "presentation_profile",
    "content_profile",
    "profile_selection",
    "roundtrip_corpus",
    "default_limits",
    "failure_policy",
    "not_claimed",
    "gate_decision",
}
IMPLEMENTATION_MARKERS = {
    "Cargo.toml": ('"crates/equation-engine"', 'quick-xml = { version = "=0.42.0"'),
    "Cargo.lock": ('name = "equation-engine"', 'name = "quick-xml"'),
    "crates/equation-engine/Cargo.toml": (
        'name = "equation-engine"',
        "quick-xml.workspace = true",
    ),
    "crates/equation-engine/src/lib.rs": (
        "mod mathml;",
        "MATHML_ADAPTER_SCHEMA_VERSION",
        "MathMlSourceProfile",
    ),
    "crates/equation-engine/src/mathml.rs": (
        'MATHML_NAMESPACE: &str = "http://www.w3.org/1998/Math/MathML"',
        'MATHML_ADAPTER_SCHEMA_VERSION: &str = "hwpx-agent.mathml-adapter/v1"',
        'MATHML_PROFILE_VERSION: &str = "hwpx-agent.mathml-profile/finite-v1"',
        "Event::DocType(_) => return Err(MathMlAdapterError::DtdForbidden)",
        "Event::GeneralRef(reference)",
        "fn classify_profile",
        "AmbiguousPresentation",
        "pub fn canonical_json",
    ),
    "crates/equation-engine/tests/mathml_adapter.rs": (
        "presentation_and_content_roundtrip_corpus_is_semantically_exact",
        "namespace_declaration_and_entity_security_fail_closed",
        "mixed_unsupported_ambiguous_and_malformed_shapes_fail_closed",
        "finite_xml_resource_limits_are_enforced",
        "finite_tree_parser_and_output_limits_are_enforced",
        "canonical_result_is_deterministic_bounded_and_debug_redacted",
    ),
    POLICY: (
        "component_only / unit_passed",
        "U+2062 INVISIBLE TIMES",
        "17 presentation and content documents",
        "false` / `not_run",
    ),
    REPORT: (
        "component_pass",
        "10/10 PASS",
        "17/17",
        "P07 or product PASS",
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
        "schema_version": "hwpx-agent.mathml-adapter-contract/v1",
        "adapter_schema_version": "hwpx-agent.mathml-adapter/v1",
        "profile_version": "hwpx-agent.mathml-profile/finite-v1",
        "model_schema_version": "hwpx-agent.math-ast/v1",
        "normalization_version": "hwpx-agent.math-ast-normalization/v1",
        "scope": "p07_03_finite_namespace_strict_mathml_to_math_ast_component",
        "task": "P07-03",
        "feature_boundary": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    expected_objects = (
        ("xml_policy", EXPECTED_XML_POLICY),
        ("presentation_profile", EXPECTED_PRESENTATION),
        ("content_profile", EXPECTED_CONTENT),
        ("profile_selection", EXPECTED_SELECTION),
        ("roundtrip_corpus", EXPECTED_ROUNDTRIP),
        ("default_limits", EXPECTED_LIMITS),
        ("not_claimed", EXPECTED_NOT_CLAIMED),
        ("gate_decision", EXPECTED_GATE),
    )
    for key, expected in expected_objects:
        if contract.get(key) != expected:
            add_error(errors, key)
    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 17
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
        "hwpx-agent.mathml-adapter/v1",
        "There is no stored v0 adapter result",
        "MUST NOT insert invisible multiplication",
        "separate P07 Gates",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-mathml-adapter-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "task": "P07-03",
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
        "P07_MATHML_ADAPTER_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
