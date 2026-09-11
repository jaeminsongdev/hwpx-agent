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
TARGET_EVIDENCE = (
    "implementation/p07/evidence/target/"
    "p07-05-native-equation.current-2020.attempt01.v1.json"
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
    "editor_smoke": False,
    "native_equation_automation_binding": False,
    "differential": False,
    "other_hangul_versions": False,
    "p07_complete": False,
    "production_ready": False,
    "product_complete": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "direct_stage": "oracle_verified",
    "synthetic_closed_hwpx": True,
    "actual_hangul": True,
    "save_reopen": True,
    "native_semantic_readback": True,
    "render": True,
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
        "saved_target_line_cache_is_admitted_without_weakening_equation_shape",
    ),
    "crates/hwpx-package/tests/id_index.rs": (
        "equation_v4_adds_native_equation_ids_without_weakening_formula_v3",
    ),
    "crates/hwpx-package/examples/p07_05_equation_target_fixture.rs": (
        "EquationHwpxLowerer::lower",
        "AtomicPackagePublisher::publish",
        '"actual_hangul_2020": false',
    ),
    "crates/hwpx-package/examples/p07_05_equation_target_oracle.rs": (
        "EquationHwpxReader::read_in_package",
        "current_hancom_2020_equation_v4",
        '"object_id_remapped"',
    ),
    "implementation/p07/tools/run-hancom-2020-equation-target-readback.ps1": (
        "invoke-hancom-2020-bounded-readback.ps1",
        "EQUATION_TARGET_READBACK",
    ),
}
EXPECTED_KEYS = {
    "schema_version", "request_schema_version", "profile_id", "id_profile", "task", "scope",
    "feature_boundary", "source_lock_canonicalization", "source_locks", "source_qualification",
    "target_evidence",
    "migration", "policy", "report", "implementation_files", "binding", "native_profile",
    "preservation", "target_readback", "default_limits", "failure_policy", "not_claimed",
    "gate_decision",
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
        "scope": "typed_math_ast_to_native_equation_hwpx_exact_current_target",
        "feature_boundary": EXPECTED_FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "target_evidence": TARGET_EVIDENCE,
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
            "layout": "inline_has_other_visible_run_display_has_dedicated_run_saved_line_cache_separate",
            "extent": "provisional_only_without_evidence_digest_and_render_required_true",
            "fallback": "no_raw_xml_plain_text_image_or_partial_object",
        },
        "preservation": {
            "mutation": "one_validated_fragment_before_exact_empty_text_node",
            "native_readback": "strict_attributes_ordered_children_eqedit_parse_math_ast_compare",
            "byte_proof": "remove_inserted_exact_span_equals_source_section",
            "package": "exactly_one_changed_part_all_other_expanded_sha_equal_writer_reopens_with_patch_id_profile",
        },
        "target_readback": {
            "lifecycle": "licensed_open_read_save_close_reopen_read_pdf_close_quit_all_pass",
            "identity": "trace_bound_output_sha_package_equation_v4_unique_nonzero_saved_object_id",
            "semantic": "exact_eqedit_script_sha_and_math_ast_semantic_sha_preserved",
            "normalization": "hangul_object_id_remap_and_paragraph_line_cache_recorded_not_source_identity",
            "render": "one_a4_page_original_detail_legible_no_clip_overlap_blank_or_black_box",
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
    target_ok = validate_target_evidence(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok, target_ok)


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


def validate_target_evidence(root: Path, errors: list[str]) -> bool:
    try:
        value = load_json(root, TARGET_EVIDENCE)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add(errors, "target_evidence_json_or_path")
        return False
    if set(value) != {
        "schema_version", "evidence_id", "scope", "target", "fixture", "lifecycle",
        "saved_hwpx", "native_oracle", "render_review", "diagnostic_history", "claims",
    }:
        add(errors, "target_evidence_keys")
    if (
        value.get("schema_version")
        != "hwpx-agent.p07-05-native-equation-current-2020-evidence/v1"
        or value.get("evidence_id")
        != "p07.native-equation.current-2020.attempt01.20260911"
        or value.get("scope")
        != "exact_current_pc_lowerer_output_save_reopen_pdf_and_native_semantic_oracle"
    ):
        add(errors, "target_evidence_identity")
    target = value.get("target")
    if target != {
        "product": "Hancom Hangul 2020",
        "prog_id": "HWPFrame.HwpObject.2",
        "registry_view": "Registry32",
        "client": "windows_powershell_x86_sta",
        "build": "11.0.0.9136",
        "architecture": "x86",
        "locale": "ko-KR",
        "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
    }:
        add(errors, "target_evidence_target")
    fixture = value.get("fixture")
    if not isinstance(fixture, dict) or any(
        fixture.get(key) != expected
        for key, expected in {
            "input_sha256": "a420d8a0078b4f83f16512ed030cfafbffd81ea96f1a9e4c497ffbd35de41e18",
            "input_bytes": 7730,
            "input_section_sha256": "8fd307055568c2a6e10642f48fcb7a95cbf6729f1bfbc2680e42b611b3f5150e",
            "input_unchanged": True,
            "source_object_id": 2_200_000_001,
            "semantic_sha256": "959ece9e281c2f318903a441ba2732c1ff9ee27a26ec0567465278e2d1533986",
            "script_sha256": "d6e25c88dbf7c63ae2b16142fa8cabf70968b2772ff03d685fc4f09cfb681596",
            "preservation_verified": True,
            "native_readback_verified": True,
            "render_required": True,
        }.items()
    ):
        add(errors, "target_evidence_fixture")
    lifecycle = value.get("lifecycle")
    phases = lifecycle.get("phases") if isinstance(lifecycle, dict) else None
    expected_phases = {
        "com_create", "open_input", "read_input", "save_as_hwpx", "close_input",
        "reopen_output", "read_output", "export_pdf", "close_output", "quit",
    }
    if (
        not isinstance(lifecycle, dict)
        or not isinstance(phases, dict)
        or set(phases) != expected_phases
        or set(phases.values()) != {"pass"}
    ):
        add(errors, "target_evidence_lifecycle")
    elif any(
        lifecycle.get(key) != expected
        for key, expected in {
            "trace_sha256": "f040c3842501328be5a906a5ecbcda4e85cb7c305a8245d90af30651beb0dd6a",
            "progress_sha256": "43cfa1de90186e6eae6dae0c07864f59519c855ab2a661edc9b95f77de8598de",
            "progress_events": 21,
            "progress_terminal": "pass",
            "input_text_sha256": "04249e6765e5a09e85ae897e652b65d77f86ce464e012c1d6d3c420eb0526cd3",
            "output_text_sha256": "04249e6765e5a09e85ae897e652b65d77f86ce464e012c1d6d3c420eb0526cd3",
            "timed_out": False,
            "remaining_hwp_process_count": 0,
            "computer_use_click_or_type_invoked": False,
        }.items()
    ):
        add(errors, "target_evidence_lifecycle")
    saved = value.get("saved_hwpx")
    if not isinstance(saved, dict) or any(
        saved.get(key) != expected
        for key, expected in {
            "sha256": "f4aa7a95fb5cc4cc21062f0a6d8dbaa50de404936c6746c34b21e0c6cf8b5263",
            "bytes": 14744,
            "section_sha256": "debd4db3f935d0b4bd1259dffa67ff1bccd32313d4ac35c031da09a33adaad41",
            "package_parts": 11,
            "id_declarations": 75,
            "id_references": 175,
        }.items()
    ):
        add(errors, "target_evidence_saved_hwpx")
    oracle = value.get("native_oracle")
    if not isinstance(oracle, dict) or any(
        oracle.get(key) != expected
        for key, expected in {
            "state": "pass",
            "native_object_count": 1,
            "layout": "display",
            "source_object_id": 2_200_000_001,
            "saved_object_id": 1_192_003_081,
            "object_id_remapped_by_hangul": True,
            "semantic_sha256": "959ece9e281c2f318903a441ba2732c1ff9ee27a26ec0567465278e2d1533986",
            "script_sha256": "d6e25c88dbf7c63ae2b16142fa8cabf70968b2772ff03d685fc4f09cfb681596",
            "base_unit": 1000,
            "baseline_percent": 85,
            "text_color": "#000000",
            "width_hwpunit": 17000,
            "height_hwpunit": 6000,
            "character_anchor_and_zero_margins": True,
            "saved_line_cache_admitted_separately": True,
            "input_unchanged_during_oracle": True,
        }.items()
    ):
        add(errors, "target_evidence_oracle")
    render = value.get("render_review")
    if not isinstance(render, dict) or any(
        render.get(key) != expected
        for key, expected in {
            "state": "pass",
            "pdf_sha256": "4a08c5dae29bae792b3868e55eaf726b148007e786c328173b45f2f8bec4a851",
            "pages": 1,
            "pixel_size": [1488, 2103],
            "all_pages_inspected": True,
            "equation_legible": True,
            "clipping": False,
            "overlap": False,
            "blank_pages": [],
            "black_boxes": False,
        }.items()
    ):
        add(errors, "target_evidence_render")
    diagnostic = value.get("diagnostic_history")
    if not isinstance(diagnostic, dict) or any(
        diagnostic.get(key) != expected
        for key, expected in {
            "initial_oracle_state": "failed",
            "initial_oracle_error": "equation_hwpx_readback_mismatch",
            "same_saved_hwpx_reused_after_correction": True,
            "failed_result_not_promoted": True,
        }.items()
    ):
        add(errors, "target_evidence_diagnostic")
    claims = value.get("claims")
    if claims != {
        "new_lowerer_actual_hangul_execution": True,
        "new_lowerer_save_reopen": True,
        "native_semantic_readback": True,
        "render": True,
        "editor_smoke": False,
        "native_equation_automation_binding": False,
        "differential": False,
        "other_hangul_versions": False,
        "p07_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        add(errors, "target_evidence_claims")
    return not any(error.startswith("target_evidence_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT import raw XML", "separate P07 Gates"),
        POLICY: ("pass / oracle_verified", "provisional", "failed diagnostic history"),
        REPORT: ("11/11 PASS", "8/8 PASS", "Licensed Hangul 2020 target evidence"),
    }.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add(errors, "document_path")
            continue
        if any(marker not in text for marker in markers):
            add(errors, "document_marker")


def result(
    errors: list[str],
    source_locks: int,
    implementation_files: int,
    qualification: bool,
    target_evidence: bool = False,
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "installed_source_qualified": qualification,
        "target_evidence_verified": target_evidence,
        "task": "P07-05",
        "direct_stage": "oracle_verified" if not unique and target_evidence else "not_proven",
        "synthetic_closed_hwpx": not unique,
        "actual_hangul": not unique and target_evidence,
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
        f"installed_source_qualified={str(validation['installed_source_qualified']).lower()} "
        f"target_evidence_verified={str(validation['target_evidence_verified']).lower()}"
    )
