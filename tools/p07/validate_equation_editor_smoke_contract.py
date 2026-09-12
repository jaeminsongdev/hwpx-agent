#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-equation-editor-smoke-v3.json"
MIGRATION = "protocol/migrations/p07-equation-editor-smoke-v2-to-v3.md"
POLICY = "implementation/p07/P07-09_EQUATION_EDITOR_SMOKE_POLICY.md"
REPORT = "implementation/p07/P07-09_EQUATION_EDITOR_SMOKE_REPORT.md"
QUALIFICATION = "implementation/p07/evidence/p07-09-equation-editor-smoke-source-qualification.current-2020.v3.json"
TARGET_QUALIFICATION = "implementation/p07/evidence/p07-09-equation-editor-smoke-target-qualification.current-2020.v3.json"
PARENT = "implementation/p07/tools/run-hancom-2020-equation-editor-smoke.ps1"
CHILD = "implementation/p07/tools/run-hancom-2020-equation-editor-smoke-child.ps1"
FINALIZER = "implementation/p07/tools/finalize-hancom-2020-equation-editor-smoke.ps1"
TARGET_ORACLE = "crates/hwpx-package/examples/p07_09_equation_editor_oracle.rs"
PLAN_BUILDER = "crates/equation-engine/examples/p07_09_equation_editor_plan.rs"
EVIDENCE_ORACLE = "crates/equation-engine/examples/p07_09_equation_editor_evidence_oracle.rs"
PARENT_SHA256 = "7a88b709047435a9bb91f317fde71befa2e29841449bf30f9dfbabb045e87b4e"
CHILD_SHA256 = "9697d122425bc003bd45807ba1cabfa5137f957ab3dbb8772dc6a36fd6fb2992"
BUNDLE_SHA256 = "33e66a4a11ea762abddbe2fbaf7f1dc6e65fce9ca7b6a56d10ffd347e8825d50"
FINALIZER_SHA256 = "1db727324c010031cfb87ef0cc74c894f634c225dc1d71d9bc6304abffd1aec5"
TARGET_ORACLE_SHA256 = "3374c47a1fd18cb0929a2ef32abd984ab13babfb6ee26e6fc509fcdcd28f7cb8"
PLAN_BUILDER_SHA256 = "9e46c13276adb03c4fa09fd490bc6fb55617e6c02abd2f805460e7e3bd5fb008"
EVIDENCE_ORACLE_SHA256 = "7f232afc22e63ab04378162eed6e3e0c61efeb7b40e18a08264856d0922274c0"
EXECUTABLE_SHA256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv", "README.md", "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md", "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
    "implementation/p07/P07-06_EQUATION_AUTOMATION_REPORT.md",
    "implementation/p07/P07-08_EQUATION_CORPUS_REPORT.md",
}
HARNESSES = {
    "parent_path": PARENT, "parent_raw_sha256": PARENT_SHA256,
    "child_path": CHILD, "child_raw_sha256": CHILD_SHA256,
    "bundle_sha256": BUNDLE_SHA256,
    "finalizer_path": FINALIZER, "finalizer_raw_sha256": FINALIZER_SHA256,
    "target_oracle_path": TARGET_ORACLE, "target_oracle_raw_sha256": TARGET_ORACLE_SHA256,
    "plan_builder_path": PLAN_BUILDER, "plan_builder_raw_sha256": PLAN_BUILDER_SHA256,
    "evidence_oracle_path": EVIDENCE_ORACLE,
    "evidence_oracle_raw_sha256": EVIDENCE_ORACLE_SHA256,
}
LIMITS = {
    "request_bytes": 8_388_608, "evidence_bytes": 8_388_608, "revision_bytes": 512,
    "serialized_bytes": 16_777_216, "manual_timeout_seconds": 900,
}
NOT_CLAIMED = {
    "visual_oracle": False, "render": False, "direct_automation_differential": False,
    "p07_07_target_layout": False, "p07_08_tier_b_target": False,
    "other_hangul_versions": False, "p07_complete": False,
    "production_ready": False, "product_complete": False,
}
GATE = {
    "component": "pass", "direct_stage": "target_passed", "editor_target": "pass",
    "actual_hangul": True, "save_reopen": True, "visual_oracle": False, "render": False,
    "p07_09": "pass", "p07": "in_progress", "product_complete": False,
}
FAILURE_POLICY = [
    "zero_hard_ceiling_or_inconsistent_limits_rejected",
    "malformed_duplicate_unknown_oversized_or_untrusted_request_plan_evidence_rejected",
    "source_artifact_graph_flow_anchor_object_semantic_script_or_count_drift_rejected",
    "before_after_ast_must_compile_and_reparse_semantically",
    "canonical_before_after_scripts_must_change_exactly_one_equal_cardinality_token",
    "saved_native_after_script_must_parse_to_the_planned_after_semantics",
    "raw_native_serialization_is_not_used_as_the_user_token_delta_boundary",
    "private_plan_file_source_semantic_script_token_and_plan_hashes_recomputed",
    "failed_before_effect_and_effect_unknown_never_pass",
    "complete_plan_bound_user_attested_checklist_and_no_reported_anomaly_required",
    "photo_fields_are_not_evidence_and_unknown_fields_are_rejected",
    "computer_use_click_or_typing_rejected",
    "exact_target_native_before_saved_reopen_and_all_automation_phases_required",
    "native_object_replacement_semantic_graph_flow_reopen_or_fallback_drift_rejected",
]
MARKERS = {
    "crates/equation-engine/src/lib.rs": ("mod editor_smoke;", "EquationEditorSmokePlanner"),
    "crates/equation-engine/src/eqedit.rs": ("pub(crate) fn token_fingerprints",),
    "crates/equation-engine/src/editor_smoke.rs": (
        'EQUATION_EDITOR_SMOKE_SCHEMA_VERSION: &str = "hwpx-agent.equation-editor-smoke/v3"',
        "pub fn load_plan_json", "single_token_change", "pub fn verify_evidence_json",
        "saved_after_script", "EquationEditorManualAttestationState", "anomaly_reported",
        "computer_use_click_or_type_invoked", "FallbackDetected",
        "finish_non_exhaustive",
    ),
    "crates/equation-engine/tests/equation_editor_smoke.rs": (
        "exact_one_token_plan_and_combined_evidence_pass_deterministically",
        "private_plan_loader_recomputes_file_source_semantic_token_and_plan_hashes",
        "manual_automation_and_effect_proofs_are_all_mandatory",
        "v2_screenshot_evidence_cannot_be_relabeled_as_v3",
        "object_semantic_graph_flow_reopen_and_fallback_drift_fail",
    ),
    PLAN_BUILDER: ("before oracle is not a bounded regular file", "EquationEditorSmokePlanner"),
    EVIDENCE_ORACLE: ("load_plan_json", "verify_evidence_json", "read_exact"),
    TARGET_ORACLE: ("read_automation_in_package", "package_state_sha256", "flow_sha256"),
    PARENT: ("EDITOR_SMOKE_PREEXISTING_HWP_PROCESS", "operator_checklist_sha256", "visual_evidence = 'not_required'", "Invoke-Oracle"),
    CHILD: ("P07_EDITOR_SMOKE_ACCESS_OR_MANUAL_ACTION_REQUIRED", "$window.Visible = $true", "$safeToQuit = $false", "manual-checklist.json", "anomaly_reported"),
    FINALIZER: ("lifecycle-finalizer-trace/v4", "first_reopen", "second_reopen", "Wait-Sha256File", "EDITOR_FINALIZER_PREDECESSOR_MISMATCH"),
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey(key)
        value[key] = item
    return value


def file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load(root: Path, relative: str) -> Any:
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard)


def canonical_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode()).hexdigest()


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False, False, False)
    exact = {
        "schema_version": "hwpx-agent.equation-editor-smoke-contract/v3",
        "request_schema_version": "hwpx-agent.equation-editor-smoke/v3",
        "evidence_schema_version": "hwpx-agent.equation-editor-smoke-evidence/v3",
        "receipt_schema_version": "hwpx-agent.equation-editor-smoke-receipt/v3",
        "profile_id": "hwpx-agent.equation-editor-smoke.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "task": "P07-09",
        "scope": "one_token_double_click_native_equation_edit_with_user_attested_checklist_and_automated_save_reopen_evidence",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION, "target_qualification": TARGET_QUALIFICATION,
        "migration": MIGRATION, "policy": POLICY, "report": REPORT,
        "harness_sources": HARNESSES, "implementation_files": list(MARKERS),
        "default_limits": LIMITS, "not_claimed": NOT_CLAIMED, "gate_decision": GATE,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {*exact, "source_locks", "workflow", "failure_policy"}:
        errors.append("contract_keys")
    if contract.get("workflow") != {
        "plan": "complete_source_state_plus_canonical_before_after_one_token_delta_plus_exact_saved_native_after_script",
        "manual": "plan_bound_user_attested_checklist_without_photo_or_visual_oracle",
        "automation": "exact_target_preflight_immutable_input_native_before_after_reopen_readback_save_close_reopen",
        "oracle": "strict_automation_native_hwpx_reader_id_index_package_state_equation_flow_and_plan_evidence_recheck",
        "computer_use": "no_click_or_typing_capture_optional",
        "visual_evidence": "not_required_and_not_a_visual_oracle",
    }:
        errors.append("workflow")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_markers(root, errors)
    harness_ok = validate_harnesses(root, errors)
    qualification_ok = validate_qualification(root, errors)
    target_qualification_ok = validate_target_qualification(root, errors)
    validate_documents(root, errors)
    return result(
        errors, source_count, implementation_count, harness_ok,
        qualification_ok, target_qualification_ok,
    )


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        path, expected = item.get("path"), item.get("sha256")
        if not isinstance(path, str) or path in declared or not isinstance(expected, str) or not DIGEST.fullmatch(expected):
            errors.append("source_lock_identity")
            continue
        declared[path] = expected
        try:
            if canonical_digest(file(root, path)) != expected:
                errors.append("source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_path")
    if set(declared) != SOURCES:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_markers(root: Path, errors: list[str]) -> int:
    for relative, markers in MARKERS.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(MARKERS)


def validate_harnesses(root: Path, errors: list[str]) -> bool:
    expected = {
        PARENT: PARENT_SHA256, CHILD: CHILD_SHA256, FINALIZER: FINALIZER_SHA256,
        TARGET_ORACLE: TARGET_ORACLE_SHA256,
        PLAN_BUILDER: PLAN_BUILDER_SHA256, EVIDENCE_ORACLE: EVIDENCE_ORACLE_SHA256,
    }
    try:
        for relative, digest in expected.items():
            if raw_digest(file(root, relative)) != digest:
                errors.append("harness_digest")
        bundle = hashlib.sha256(f"{PARENT_SHA256}:{CHILD_SHA256}".encode()).hexdigest()
        if bundle != BUNDLE_SHA256:
            errors.append("harness_bundle")
    except (OSError, ValueError):
        errors.append("harness_path")
    return not any(error.startswith("harness_") for error in errors)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if set(value) != {"schema_version", "task", "recorded_date", "target", "harness_sources",
                      "component_execution", "target_execution", "claims"}:
        errors.append("qualification_keys")
    if value.get("schema_version") != "hwpx-agent.equation-editor-smoke-source-qualification/v3" or value.get("task") != "P07-09" or value.get("recorded_date") != "2026-09-12":
        errors.append("qualification_identity")
    if value.get("target") != {"product": "Hangul 2020", "prog_id": "HWPFrame.HwpObject.2",
                                   "version": "11.0.0.9136", "executable_sha256": EXECUTABLE_SHA256,
                                   "architecture": "x86", "locale": "ko-KR",
                                   "other_versions": "not_qualified"}:
        errors.append("qualification_target")
    if value.get("harness_sources") != HARNESSES:
        errors.append("qualification_harness")
    if value.get("component_execution") != {"state": "pass", "rust_tests_passed": 12,
                                                "powershell_scripts_parsed": 3,
                                                "single_token_planner": "pass",
                                                "saved_native_script_binding": "pass",
                                                "private_plan_reload": "pass",
                                                "combined_evidence_verifier": "pass",
                                                "native_hwpx_oracle_build": "pass",
                                                "silent_fallback_count": 0}:
        errors.append("qualification_component")
    try:
        target_qualification_sha256 = raw_digest(file(root, TARGET_QUALIFICATION))
    except (OSError, ValueError):
        target_qualification_sha256 = None
    target = value.get("target_execution")
    if target != {"state": "pass", "latest_attempt": "p07-09-20260912-attempt14",
                  "exact_target_preflight_observed": True, "immutable_input_observed": True,
                  "saved_native_readback_observed": True,
                  "user_checklist_state": "user_attested",
                  "photo_evidence_requirement": "not_required",
                  "automated_save_reopen_complete": True,
                  "native_object_identity_preserved": True,
                  "silent_fallback_count": 0,
                  "target_qualification_sha256": target_qualification_sha256}:
        errors.append("qualification_target_run")
    if value.get("claims") != {"implementation_ready": True,
                                    "canonical_single_token_change_enforced": True,
                                    "saved_native_script_semantics_enforced": True,
                                    "manual_and_automation_required": True,
                                    "computer_use_no_click_or_typing_enforced": True,
                                    "photo_evidence_required": False,
                                    "visual_oracle": False,
                                    "target_editor_smoke": True, "actual_hangul_gate": True,
                                    "save_reopen": True, "render": False,
                                    "p07_09_complete": True, "p07_complete": False,
                                    "product_complete": False}:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_target_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, TARGET_QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("target_qualification_json_or_path")
        return False
    if set(value) != {"schema_version", "task", "recorded_date", "attempt_id", "target",
                      "identities", "manual", "automation", "native_readback", "claims"}:
        errors.append("target_qualification_keys")
    if value.get("schema_version") != "hwpx-agent.equation-editor-smoke-target-qualification/v3" or value.get("task") != "P07-09" or value.get("recorded_date") != "2026-09-12" or value.get("attempt_id") != "p07-09-20260912-attempt14":
        errors.append("target_qualification_identity")
    if value.get("target") != {"product": "Hangul 2020", "prog_id": "HWPFrame.HwpObject.2",
                                "version": "11.0.0.9136", "executable_sha256": EXECUTABLE_SHA256,
                                "architecture": "x86", "locale": "ko-KR"}:
        errors.append("target_qualification_target")
    identities = value.get("identities")
    required_identities = {"plan_file_sha256", "plan_sha256", "before_artifact_sha256",
                           "after_artifact_sha256", "manual_checklist_sha256",
                           "child_trace_sha256", "lifecycle_finalizer_trace_sha256",
                           "oracle_receipt_sha256", "evidence_sha256",
                           "runtime_receipt_sha256", "verified_receipt_sha256"}
    if not isinstance(identities, dict) or set(identities) != required_identities or any(
        not isinstance(item, str) or not DIGEST.fullmatch(item) for item in identities.values()
    ):
        errors.append("target_qualification_digests")
    elif identities["before_artifact_sha256"] == identities["after_artifact_sha256"]:
        errors.append("target_qualification_artifact_change")
    elif identities["child_trace_sha256"] == identities["lifecycle_finalizer_trace_sha256"]:
        errors.append("target_qualification_distinct_evidence")
    if value.get("manual") != {"state": "user_attested", "checklist_items": 8,
                                "anomaly_reported": False,
                                "computer_use_click_or_type_invoked": False,
                                "photo_evidence": "not_required",
                                "visual_oracle": False}:
        errors.append("target_qualification_manual")
    if value.get("automation") != {"state": "pass", "exact_target_preflight": "passed",
                                    "immutable_input": "passed", "initial_native_readback": "passed",
                                    "saved_native_readback": "passed", "save": "passed",
                                    "close": "passed", "reopen": "passed",
                                    "reopen_native_readback": "passed", "all_phases": "passed"}:
        errors.append("target_qualification_automation")
    if value.get("native_readback") != {"object_identity_preserved": True,
                                         "native_object_count": 1,
                                         "semantic_change_verified": True,
                                         "saved_and_reopen_equal": True,
                                         "input_immutable": True,
                                         "silent_fallback_count": 0}:
        errors.append("target_qualification_native")
    if value.get("claims") != {"target_editor_smoke": True, "actual_hangul": True,
                                "save_reopen": True, "visual_oracle": False,
                                "render": False, "p07_09_complete": True,
                                "p07_complete": False, "product_complete": False}:
        errors.append("target_qualification_claims")
    return not any(error.startswith("target_qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("user_attested", "V2 plans and evidence do not migrate", "visual oracle"),
        POLICY: ("target_pass_v3 / p07_in_progress", "exactly one differing", "user_attested"),
        REPORT: ("12/12 PASS", "Attempt 14", "editor_target_state=pass"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, harness: bool,
           qualification: bool, target_qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-editor-smoke-validation/v3",
        "state": "pass" if not unique else "fail", "errors": unique,
        "source_locks": sources, "implementation_files": implementation,
        "harness_sources_verified": harness, "source_qualification_verified": qualification,
        "target_qualification_verified": target_qualification,
        "task": "P07-09", "direct_stage": "target_passed" if not unique else "not_proven",
        "editor_target": "pass" if not unique else "not_proven",
        "actual_hangul": not unique, "save_reopen": not unique,
        "visual_oracle": False, "render": False, "p07": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(f"P07_EQUATION_EDITOR_SMOKE_CONTRACT_PASS source_locks={value['source_locks']} implementation_files={value['implementation_files']} editor_target=pass")
