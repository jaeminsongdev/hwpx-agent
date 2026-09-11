#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p07 import build_equation_automation_probe as probe_builder


CONTRACT = "protocol/private/p07-equation-automation-v1.json"
MIGRATION = "protocol/migrations/p07-equation-automation-v0-to-v1.md"
POLICY = "implementation/p07/P07-06_EQUATION_AUTOMATION_POLICY.md"
REPORT = "implementation/p07/P07-06_EQUATION_AUTOMATION_REPORT.md"
QUALIFICATION = (
    "implementation/p07/evidence/"
    "p07-06-equation-automation-source-qualification.current-2020.v1.json"
)
TARGET_EVIDENCE = (
    "implementation/p07/evidence/target/"
    "p07-06-equation-automation.current-2020.attempt03.v1.json"
)
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "README.md",
    "docs/04_feature_catalog/08_eq.md",
    "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
    "implementation/p02/P02-07_REPORT.md",
    "implementation/p02/evidence/bindings/automation-bindings.2020.v1.final.json",
    "implementation/p07/P07-05_NATIVE_EQUATION_HWPX_REPORT.md",
}
EXPECTED_CAPABILITIES = [
    "eq.edit_native",
    "eq.insert_native",
    "eq.roundtrip_readback",
]
EXPECTED_LIMITS = {
    "request_bytes": 8_388_608,
    "revision_bytes": 512,
    "serialized_bytes": 16_777_216,
    "probe_source_bytes": 16_777_216,
    "probe_script_bytes": 1_048_576,
    "probe_output_bytes": 4_194_304,
    "target_timeout_seconds": 180,
}
EXPECTED_NOT_CLAIMED = {
    "layout_estimator_visual": False,
    "editor_double_click_smoke": False,
    "render": False,
    "differential": False,
    "p02_registry_promoted": False,
    "p10_05_security_module": False,
    "p10_06_production_executor": False,
    "other_hangul_versions": False,
    "p07_complete": False,
    "production_ready": False,
    "product_complete": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "direct_stage": "oracle_verified",
    "actual_hangul": True,
    "native_insert": True,
    "native_edit": True,
    "in_session_script_readback": True,
    "save_reopen": True,
    "native_hwpx_oracle": True,
    "render": False,
    "p07": "in_progress",
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    ".gitignore": ("/implementation/p07/evidence/private/",),
    "crates/equation-engine/src/lib.rs": ("mod automation;", "EquationAutomationPlanner"),
    "crates/equation-engine/src/automation.rs": (
        'EQUATION_AUTOMATION_SCHEMA_VERSION: &str = "hwpx-agent.equation-automation/v1"',
        "EquationAutomationOperationDraft",
        "SourceStateDrift",
        "EffectNotProven",
        "finish_non_exhaustive",
    ),
    "crates/equation-engine/tests/equation_automation.rs": (
        "insert_builds_typed_plan_and_requires_mutation_receipt",
        "edit_requires_exact_selected_object_and_semantic_state",
        "readback_requires_complete_nonmutating_state",
        "request_and_build_both_reject_source_or_selection_drift",
        "receipt_tamper_failure_unknown_effect_and_wrong_object_fail",
        "debug_redacts_source_binding_object_semantic_and_script",
    ),
    "crates/equation-engine/examples/p07_06_equation_automation_program.rs": (
        "EqEditEngine",
        '"hwpx-agent.p07-06-equation-automation-program/v1"',
    ),
    "crates/hwpx-package/src/lib.rs": (
        "EQUATION_AUTOMATION_HWPX_PROFILE_ID",
        "EquationHwpxReader",
    ),
    "crates/hwpx-package/src/equation.rs": (
        'EQUATION_AUTOMATION_HWPX_PROFILE_ID: &str =',
        "AutomationCurrent2020",
        "read_automation_in_package",
        "AUTOMATION_SHAPE_COMMENT_SHA256",
    ),
    "crates/hwpx-package/tests/equation_hwpx.rs": (
        "automation_native_profile_is_distinct_strict_and_semantically_read_back",
        "q:shapeComment",
    ),
    "crates/hwpx-package/examples/p07_06_equation_automation_oracle.rs": (
        "EquationHwpxReader::read_automation_in_package",
        '"hwpx-agent.p07-06-equation-automation-oracle/v1"',
    ),
    "tools/p07/build_equation_automation_probe.py": (
        "EXPECTED_SOURCE_RECORDS_SHA256",
        "resolve_bindings",
        "require_private_output",
        "publish_no_overwrite",
    ),
    "implementation/p07/tools/run-hancom-2020-equation-automation-probe.ps1": (
        "Registry32",
        "expected_executable_sha256",
        "remaining_hwp_process_count",
    ),
    "implementation/p07/tools/run-hancom-2020-equation-automation-probe-child.ps1": (
        "Resolve-ParameterSetObject",
        "insert_readback",
        "edit_readback",
        "reopen_close",
    ),
}
PUBLIC_P07_06_FILES = [
    CONTRACT,
    MIGRATION,
    POLICY,
    REPORT,
    QUALIFICATION,
    TARGET_EVIDENCE,
    *IMPLEMENTATION_MARKERS,
]
EXPECTED_KEYS = {
    "schema_version", "request_schema_version", "receipt_schema_version", "profile_id",
    "task", "scope", "capabilities", "source_lock_canonicalization", "source_locks",
    "source_qualification", "target_evidence", "migration", "policy", "report",
    "implementation_files", "binding", "operations", "target_probe", "p02_boundary",
    "default_limits", "failure_policy", "not_claimed", "gate_decision",
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey(key)
        value[key] = item
    return value


def load_json(root: Path, relative: str) -> Any:
    raw = bounded_file(root, relative).read_bytes()
    return json.loads(raw, object_pairs_hook=reject_duplicate_keys)


def bounded_file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    metadata = path.stat()
    if not path.is_file() or path.is_symlink() or metadata.st_size <= 0 or metadata.st_size > maximum:
        raise ValueError("invalid bounded file")
    return path


def canonical_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def add(errors: list[str], value: str) -> None:
    errors.append(value)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False, False)
    if not isinstance(contract, dict) or set(contract) != EXPECTED_KEYS:
        add(errors, "contract_keys")
    for key, expected in {
        "schema_version": "hwpx-agent.equation-automation-contract/v1",
        "request_schema_version": "hwpx-agent.equation-automation/v1",
        "receipt_schema_version": "hwpx-agent.equation-automation-receipt/v1",
        "profile_id": "hwpx-agent.equation-automation.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "task": "P07-06",
        "scope": "typed_native_equation_insert_edit_readback_with_exact_current_target_probe",
        "capabilities": EXPECTED_CAPABILITIES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "target_evidence": TARGET_EVIDENCE,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "default_limits": EXPECTED_LIMITS,
        "not_claimed": EXPECTED_NOT_CLAIMED,
        "gate_decision": EXPECTED_GATE,
    }.items():
        if contract.get(key) != expected:
            add(errors, key)
    expected_nested = {
        "binding": {
            "source_state": "revision_package_graph_document_flow_anchor_selected_native_equation_semantic",
            "drift_checks": "request_and_build_repeat_exact_complete_state_comparison",
            "semantic": "normalized_math_ast_eqedit_compile_parse_equality",
            "installed_binding": "hash_pinned_private_source_shape_types_and_opaque_binding_set_sha",
            "raw_identifiers": "private_probe_only_never_public_plan_receipt_or_evidence",
        },
        "operations": {
            "insert": "requires_no_selected_equation_and_mutates_graph_and_flow",
            "edit": "requires_exact_selected_object_and_semantic_and_mutates_graph_and_flow",
            "readback": "requires_exact_selected_object_and_semantic_and_preserves_graph_and_flow",
        },
        "target_probe": {
            "document": "disposable_blank_only",
            "runtime": "registry32_x86_sta_exact_build_executable_and_harness_hashes",
            "selection": "exact_source_derived_reverse_control_selection",
            "readback": "edit_default_without_execute_exact_script_hash",
            "lifecycle": "insert_readback_save_edit_readback_save_close_reopen_quit",
            "oracle": "strict_automation_native_profile_on_both_immutable_saved_hwpx",
        },
        "p02_boundary": {
            "frozen_registry_status": "unavailable_with_reason",
            "reason": "no_reviewed_action_mapping",
            "routing_enabled": False,
            "runtime_support_state": "unverified",
            "mutated_or_promoted_by_p07": False,
        },
    }
    for key, expected in expected_nested.items():
        if contract.get(key) != expected:
            add(errors, key)
    failure = contract.get("failure_policy")
    if not isinstance(failure, list) or len(failure) != 11 or len(set(failure)) != 11:
        add(errors, "failure_policy")
    if contract.get("implementation_files") != list(IMPLEMENTATION_MARKERS):
        add(errors, "implementation_files")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    target_ok = validate_target_evidence(root, errors)
    validate_documents(root, errors)
    validate_public_privacy(root, errors)
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
        if not isinstance(path, str) or path in declared or not isinstance(digest, str) or not DIGEST.fullmatch(digest):
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
    if set(value) != {"schema_version", "task", "recorded_date", "target", "installed_source", "p02_registry_boundary", "claims"}:
        add(errors, "qualification_keys")
    if value.get("schema_version") != "hwpx-agent.equation-automation-source-qualification/v1" or value.get("task") != "P07-06" or value.get("recorded_date") != "2026-09-11":
        add(errors, "qualification_identity")
    if value.get("target") != {"product": "Hangul 2020", "version": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR", "other_versions": "not_qualified"}:
        add(errors, "qualification_target")
    source = value.get("installed_source")
    if source != {
        "source_lock_id": probe_builder.SOURCE_LOCK_ID,
        "records_sha256": probe_builder.EXPECTED_SOURCE_RECORDS_SHA256,
        "selected_action_records": 3,
        "selected_parameter_records": 8,
        "shape_and_type_checked": True,
        "raw_identifiers_public": False,
    }:
        add(errors, "qualification_source")
    registry = value.get("p02_registry_boundary")
    if registry != {
        "registry_sha256": "986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48",
        "capabilities": EXPECTED_CAPABILITIES,
        "status": "unavailable_with_reason",
        "unavailable_reason": "no_reviewed_action_mapping",
        "routing_enabled": False,
        "runtime_support_state": "unverified",
        "p07_probe_mutates_registry": False,
    }:
        add(errors, "qualification_registry")
    claims = value.get("claims")
    if claims != {
        "source_identity_qualified": True,
        "source_shape_and_types_qualified": True,
        "current_target_probe_binding_qualified": True,
        "p02_registry_promoted": False,
        "p10_production_executor": False,
        "other_versions": False,
        "product_complete": False,
    }:
        add(errors, "qualification_claims")
    try:
        raw, records = probe_builder.load_source_records(
            root / "implementation/p02/evidence/automation/automation-pdf.records.v1.json",
            probe_builder.EXPECTED_SOURCE_RECORDS_SHA256,
        )
        bindings = probe_builder.resolve_bindings(records)
        if hashlib.sha256(probe_builder.canonical_bytes(bindings)).hexdigest() != "3d8bbc9bebbfa44e048d70164bb6cdb1ac0c81c022c77e657863e232ac535cfb" or hashlib.sha256(raw).hexdigest() != probe_builder.EXPECTED_SOURCE_RECORDS_SHA256:
            add(errors, "qualification_binding_rebuild")
    except (OSError, ValueError, probe_builder.ProbeBuildError):
        add(errors, "qualification_binding_rebuild")
    return not any(error.startswith("qualification_") for error in errors)


def validate_target_evidence(root: Path, errors: list[str]) -> bool:
    try:
        value = load_json(root, TARGET_EVIDENCE)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add(errors, "target_evidence_json_or_path")
        return False
    if set(value) != {"schema_version", "evidence_id", "scope", "target", "source_and_binding", "program", "runtime", "inserted_hwpx", "edited_hwpx", "diagnostic_history", "claims"}:
        add(errors, "target_evidence_keys")
    if value.get("schema_version") != "hwpx-agent.p07-06-equation-automation-current-2020-evidence/v1" or value.get("evidence_id") != "p07.equation-automation.current-2020.attempt03.20260911" or value.get("scope") != "exact_current_pc_source_derived_insert_edit_in_session_readback_save_reopen_and_native_hwpx_oracle":
        add(errors, "target_evidence_identity")
    if value.get("target") != {
        "product": "Hancom Hangul 2020", "profile_id": "hancom-hangul-2020-secondary",
        "prog_id": "HWPFrame.HwpObject.2", "registry_view": "Registry32",
        "client": "windows_powershell_x86_sta", "build": "11.0.0.9136",
        "architecture": "x86", "locale": "ko-KR",
        "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
    }:
        add(errors, "target_evidence_target")
    source = value.get("source_and_binding")
    if source != {
        "source_lock_id": probe_builder.SOURCE_LOCK_ID,
        "source_records_sha256": probe_builder.EXPECTED_SOURCE_RECORDS_SHA256,
        "binding_set_sha256": "3d8bbc9bebbfa44e048d70164bb6cdb1ac0c81c022c77e657863e232ac535cfb",
        "action_binding_count": 3, "parameter_item_binding_count": 8,
        "raw_identifiers_present": False, "private_paths_present": False,
    }:
        add(errors, "target_evidence_source")
    program = value.get("program")
    if program != {
        "initial_script_sha256": "abfd983ec821dec01444c9d89e6393dd3032b92a1df84a3b30d6ce6dca94b8da",
        "initial_script_bytes": 9,
        "initial_semantic_sha256": "b50230ef0024d69c48cf74b46fc6bab4d48dbc5bee4d3cc646359a845373d06d",
        "edited_script_sha256": "a42f628f65aa16b4574414ffbe1d19bed3f19e9f7929bee29570ee4e168cf9d6",
        "edited_script_bytes": 17,
        "edited_semantic_sha256": "6ef88990833856e536970e238f6318561a8182f2a9070bd9bbbd3bb2672db51e",
        "semantic_changed": True, "script_values_present": False,
    }:
        add(errors, "target_evidence_program")
    runtime = value.get("runtime")
    phases = runtime.get("phases") if isinstance(runtime, dict) else None
    if not isinstance(phases, dict) or len(phases) != 16 or set(phases.values()) != {"pass"}:
        add(errors, "target_evidence_phases")
    runtime_expected = {
        "request_sha256": "419b23a950572db8ef3f540726e229c0ef5e31777be3d1bf72184d657db56068",
        "plan_receipt_sha256": "c4c4e4e78592642b881ff926db9dfb242a413423e39558b95b4cee899f3d4732",
        "trace_sha256": "b2c35c3b4b62b86c0b94d3ad905b22a4f86ed88c19e766723caa33862fd881f9",
        "runtime_receipt_sha256": "5586005251319edef53ed3de196fead237b0f0c2105d824e0dbf1e37ef12dfde",
        "parent_harness_sha256": "7be8ff0c0b9c9e78551f6cc3c6006800aaa5b200942e7fef90967ef9c0b3dccd",
        "child_harness_sha256": "985750a1cfcb40d396b8d3fabe7b6d6d7c47b5c2fc082c1d04c0ebc982274953",
        "parameter_set_resolution": "runtime_h_prefix", "all_action_return_kinds": "true",
        "initial_readback_exact": True, "edited_readback_exact": True,
        "timed_out": False, "child_exit_code": 0, "remaining_hwp_process_count": 0,
        "user_document_opened": False, "external_network_invoked": False,
        "registry_or_system_setting_changed": False, "computer_use_click_or_type_invoked": False,
    }
    if not isinstance(runtime, dict) or any(runtime.get(key) != expected for key, expected in runtime_expected.items()):
        add(errors, "target_evidence_runtime")
    validate_hwpx_evidence(value.get("inserted_hwpx"), False, errors)
    validate_hwpx_evidence(value.get("edited_hwpx"), True, errors)
    diagnostic = value.get("diagnostic_history")
    if not isinstance(diagnostic, list) or len(diagnostic) != 3 or diagnostic[0].get("state") != "failed" or diagnostic[1].get("state") != "failed" or diagnostic[2].get("initial_oracle_state") != "failed" or any(item.get("failed_evidence_promoted") is True or item.get("failed_result_promoted") is True for item in diagnostic):
        add(errors, "target_evidence_diagnostic")
    claims = value.get("claims")
    if claims != {
        "current_target_action_probes": True, "native_insert": True, "native_edit": True,
        "in_session_script_readback": True, "save_reopen": True,
        "product_native_hwpx_oracle": True, "editor_double_click_smoke": False,
        "render": False, "differential": False, "production_p10_executor": False,
        "p10_05_security_module": False, "p02_registry_promoted": False,
        "other_hangul_versions": False, "p07_complete": False,
        "production_ready": False, "product_complete": False,
    }:
        add(errors, "target_evidence_claims")
    return not any(error.startswith("target_evidence_") for error in errors)


def validate_hwpx_evidence(value: Any, edited: bool, errors: list[str]) -> None:
    common = {
        "oracle_state": "pass", "input_unchanged_during_oracle": True,
        "package_parts": 11, "id_declarations": 74, "id_references": 172,
        "native_object_count": 1, "object_id": 1_192_022_476, "layout": "display",
        "base_unit": 1000, "text_color": "#000000",
    }
    expected = common | ({
        "sha256": "ec935ef2aa94a2b4bddc67c2b207873b9a1567a3f85dcb7e9b4d906c2f079f2b",
        "bytes": 13_073, "object_id_stable_from_insert": True,
        "script_sha256": "a42f628f65aa16b4574414ffbe1d19bed3f19e9f7929bee29570ee4e168cf9d6",
        "semantic_sha256": "6ef88990833856e536970e238f6318561a8182f2a9070bd9bbbd3bb2672db51e",
        "baseline_percent": 89, "width_hwpunit": 2665, "height_hwpunit": 1163,
    } if edited else {
        "sha256": "4c908413fcf60c746bec04dec3a01ab90216455561fa2ea137887eba075cca61",
        "bytes": 13_024,
        "script_sha256": "abfd983ec821dec01444c9d89e6393dd3032b92a1df84a3b30d6ce6dca94b8da",
        "semantic_sha256": "b50230ef0024d69c48cf74b46fc6bab4d48dbc5bee4d3cc646359a845373d06d",
        "baseline_percent": 86, "width_hwpunit": 2230, "height_hwpunit": 975,
    })
    if value != expected:
        add(errors, "target_evidence_edited_hwpx" if edited else "target_evidence_inserted_hwpx")


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT import raw automation", "does not rewrite or\npromote"),
        POLICY: ("pass / oracle_verified", "Attempts 01 and 02 remain failed", "P10-06 production execution"),
        REPORT: ("8/8 PASS", "12/12 PASS", "5/5 PASS", "frozen P02 current registry"),
    }.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add(errors, "document_path")
            continue
        if any(marker not in text for marker in markers):
            add(errors, "document_marker")


def validate_public_privacy(root: Path, errors: list[str]) -> None:
    try:
        _, records = probe_builder.load_source_records(
            root / "implementation/p02/evidence/automation/automation-pdf.records.v1.json",
            probe_builder.EXPECTED_SOURCE_RECORDS_SHA256,
        )
        bindings = probe_builder.resolve_bindings(records)
        forbidden = [item["action_id"] for item in bindings["actions"].values()]
        forbidden.append(bindings["selection"]["action_id"])
        for relative in PUBLIC_P07_06_FILES:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
            if any(value in text for value in forbidden):
                add(errors, "public_raw_action_identifier")
    except (OSError, UnicodeDecodeError, ValueError, probe_builder.ProbeBuildError):
        add(errors, "public_privacy_check")


def result(errors: list[str], source_locks: int, implementation_files: int, qualification: bool, target_evidence: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-automation-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "installed_source_qualified": qualification,
        "target_evidence_verified": target_evidence,
        "task": "P07-06",
        "direct_stage": "oracle_verified" if not unique and target_evidence else "not_proven",
        "actual_hangul": not unique and target_evidence,
        "render": False,
        "p07": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        sys.exit(1)
    print(
        "P07_EQUATION_AUTOMATION_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']} "
        f"installed_source_qualified={str(validation['installed_source_qualified']).lower()} "
        f"target_evidence_verified={str(validation['target_evidence_verified']).lower()}"
    )
