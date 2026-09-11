#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-equation-hwpx-v1.json"
MIGRATION = "protocol/migrations/p07-equation-hwpx-v0-to-v1.md"
POLICY = "implementation/p07/P07-05_NATIVE_EQUATION_HWPX_POLICY.md"
REPORT = "implementation/p07/P07-05_NATIVE_EQUATION_HWPX_REPORT.md"
QUALIFICATION = (
    "implementation/p07/evidence/"
    "p07-05-native-equation-hwpx-source-qualification.current-2020.v1.json"
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
    "implementation/p07/P07-04_EQEDIT_REPORT.md",
}
EXPECTED_FEATURES = ["EQ-001", *[f"EQ-{value:03d}" for value in range(6, 31)], "EQ-032"]
EXPECTED_LIMITS = {
    "section_bytes": 33_554_432,
    "elements": 1_000_000,
    "equations": 65_536,
    "script_bytes": 4_194_304,
    "serialized_bytes": 16_777_216,
    "extent_hwpunit": 10_000_000,
    "object_id": 4_294_967_294,
}
EXPECTED_NOT_CLAIMED = {
    "arbitrary_existing_document_profile": False,
    "verified_layout_extent": False,
    "new_lowerer_actual_hangul_execution": False,
    "new_lowerer_save_reopen": False,
    "editor_smoke": False,
    "render": False,
    "automation": False,
    "differential": False,
    "other_hangul_versions": False,
    "p07_complete": False,
    "production_ready": False,
    "product_complete": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "direct_stage": "integration_passed",
    "synthetic_closed_hwpx": True,
    "actual_hangul": False,
    "p07": "in_progress",
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "Cargo.lock": ('name = "hwpx-package"', '"equation-engine"'),
    "crates/hwpx-package/Cargo.toml": ('equation-engine = { version = "0.1.0"',),
    "crates/hwpx-package/src/lib.rs": ("mod equation;", "EquationHwpxLowerer"),
    "crates/hwpx-package/src/equation.rs": (
        'EQUATION_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.equation-hwpx/v1"',
        "EquationHwpxBuilder",
        "EquationHwpxLowerer",
        "read_equation_shape",
        "package_object_ids",
        "restored != bound.bytes",
        "EquationExtentSource::Provisional",
        "finish_non_exhaustive",
    ),
    "crates/hwpx-package/src/id_index.rs": (
        "CurrentHancom2020EquationV4",
        "IdKind::Equation",
        "EQUATION_DECLARATION_RULES",
    ),
    "crates/hwpx-package/src/patch.rs": ("pub(crate) profile: IdRuleProfile",),
    "crates/hwpx-package/src/writer.rs": ("patch.profile",),
    "crates/hwpx-package/tests/equation_hwpx.rs": (
        "display_ast_lowers_to_exact_native_object_and_closed_package",
        "inline_layout_is_structurally_distinct_and_semantically_read_back",
        "lowerer_rechecks_package_and_document_flow_drift",
        "tampered_native_shape_script_and_duplicate_ids_are_rejected",
    ),
    "crates/hwpx-package/tests/id_index.rs": (
        "equation_v4_adds_native_equation_ids_without_weakening_formula_v3",
    ),
}
EXPECTED_KEYS = {
    "schema_version", "request_schema_version", "profile_id", "id_profile", "task", "scope",
    "feature_boundary", "source_lock_canonicalization", "source_locks", "source_qualification",
    "migration", "policy", "report", "implementation_files", "binding", "native_profile",
    "preservation", "default_limits", "failure_policy", "not_claimed", "gate_decision",
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
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def add(errors: list[str], value: str) -> None:
    if value not in errors:
        errors.append(value)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)
    if set(contract) != EXPECTED_KEYS:
        add(errors, "contract_keys")
    expected_scalars = {
        "schema_version": "hwpx-agent.equation-hwpx-contract/v1",
        "request_schema_version": "hwpx-agent.equation-hwpx/v1",
        "profile_id": "hwpx-agent.equation-hwpx.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "id_profile": "hancom-2020-hwpml-2011-equation/v4",
        "task": "P07-05",
        "scope": "typed_math_ast_to_synthetic_closed_hwpx_native_equation_component",
        "feature_boundary": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "default_limits": EXPECTED_LIMITS,
        "not_claimed": EXPECTED_NOT_CLAIMED,
        "gate_decision": EXPECTED_GATE,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            add(errors, key)
    for key, expected in {
        "binding": {
            "source": "complete_expanded_package_graph_section_top_level_paragraph_direct_empty_run_package_object_ids",
            "flow": "distinct_exact_before_and_after_document_flow_sha256_checked_at_request_and_lower",
            "identity": "nonzero_bounded_package_wide_native_object_id_no_collision",
            "semantic": "normalized_math_ast_sha_eqedit_sha_and_compile_parse_semantic_equality",
        },
        "native_profile": {
            "object": "equation_version60_hancomeqn",
            "owned_state": "id_style_baseline_color_absolute_extent_character_anchor_zero_margin_script",
            "layout": "inline_has_other_visible_run_display_has_dedicated_run",
            "extent": "provisional_only_without_evidence_digest_and_render_required_true",
            "fallback": "no_raw_xml_plain_text_image_or_partial_object",
        },
        "preservation": {
            "mutation": "one_validated_fragment_before_exact_empty_text_node",
            "native_readback": "strict_attributes_ordered_children_eqedit_parse_math_ast_compare",
            "byte_proof": "remove_inserted_exact_span_equals_source_section",
            "package": "exactly_one_changed_part_all_other_expanded_sha_equal_writer_reopens_with_patch_id_profile",
        },
    }.items():
        if contract.get(key) != expected:
            add(errors, key)
    failure = contract.get("failure_policy")
    if not isinstance(failure, list) or len(failure) != 10 or len(set(failure)) != 10:
        add(errors, "failure_policy")
    if contract.get("implementation_files") != list(IMPLEMENTATION_MARKERS):
        add(errors, "implementation_files")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        add(errors, "source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            add(errors, "source_lock_shape")
            continue
        path, digest = item.get("path"), item.get("sha256")
        if not isinstance(path, str) or path in declared or not isinstance(digest, str) or len(digest) != 64:
            add(errors, "source_lock_identity")
            continue
        declared[path] = digest
        try:
            actual = canonical_sha256(bounded_file(root, path))
        except (OSError, UnicodeDecodeError, ValueError):
            add(errors, "source_lock_path")
            continue
        if actual != digest:
            add(errors, "source_lock_digest")
    if set(declared) != EXPECTED_SOURCE_PATHS:
        add(errors, "source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add(errors, "implementation_path")
            continue
        if any(marker not in text for marker in markers):
            add(errors, "implementation_marker")
    return len(IMPLEMENTATION_MARKERS)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load_json(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add(errors, "qualification_json_or_path")
        return False
    if value.get("schema_version") != "hwpx-agent.native-equation-hwpx-source-qualification/v1":
        add(errors, "qualification_version")
    if value.get("task") != "P07-05" or value.get("recorded_date") != "2026-09-11":
        add(errors, "qualification_identity")
    target = value.get("target")
    if target != {"product": "Hangul 2020", "version": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR", "other_versions": "not_qualified"}:
        add(errors, "qualification_target")
    claims = value.get("claims")
    if not isinstance(claims, dict) or claims.get("new_lowerer_actual_hangul_execution") is not False or claims.get("product_complete") is not False or claims.get("predecessor_actual_hangul_save_reopen") is not True:
        add(errors, "qualification_claims")
    component = value.get("component_evidence")
    if not isinstance(component, dict) or set(component.values()) != {True}:
        add(errors, "qualification_component")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT import raw XML", "separate P07 Gates"),
        POLICY: ("component_pass / integration_passed", "provisional", "false` / `not_run"),
        REPORT: ("10/10 PASS", "8/8 PASS", "Actual new-lowerer Hangul execution"),
    }.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add(errors, "document_path")
            continue
        if any(marker not in text for marker in markers):
            add(errors, "document_marker")


def result(errors: list[str], source_locks: int, implementation_files: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "installed_source_qualified": qualification,
        "task": "P07-05",
        "direct_stage": "integration_passed" if not unique else "not_proven",
        "synthetic_closed_hwpx": not unique,
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
        "P07_EQUATION_HWPX_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']} "
        f"installed_source_qualified={str(validation['installed_source_qualified']).lower()}"
    )
