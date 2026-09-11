#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-equation-editor-smoke-v1.json"
MIGRATION = "protocol/migrations/p07-equation-editor-smoke-v0-to-v1.md"
POLICY = "implementation/p07/P07-09_EQUATION_EDITOR_SMOKE_POLICY.md"
REPORT = "implementation/p07/P07-09_EQUATION_EDITOR_SMOKE_REPORT.md"
QUALIFICATION = "implementation/p07/evidence/p07-09-equation-editor-smoke-source-qualification.current-2020.v1.json"
PARENT = "implementation/p07/tools/run-hancom-2020-equation-editor-smoke.ps1"
CHILD = "implementation/p07/tools/run-hancom-2020-equation-editor-smoke-child.ps1"
TARGET_ORACLE = "crates/hwpx-package/examples/p07_09_equation_editor_oracle.rs"
PLAN_BUILDER = "crates/equation-engine/examples/p07_09_equation_editor_plan.rs"
EVIDENCE_ORACLE = "crates/equation-engine/examples/p07_09_equation_editor_evidence_oracle.rs"
PARENT_SHA256 = "47d27c123d4a2c0a0f830f263fd31e52db9bdeac4c160e578e0cbc1c9d3af2c1"
CHILD_SHA256 = "5950ea9a047b593f0a1216551de2de222379a7296a558957f233d093362d9569"
BUNDLE_SHA256 = "5d9f7502e821046c193f0d738469cb9a13e613e16f1b056dfc9ed58b16360068"
TARGET_ORACLE_SHA256 = "3374c47a1fd18cb0929a2ef32abd984ab13babfb6ee26e6fc509fcdcd28f7cb8"
PLAN_BUILDER_SHA256 = "2ed5abeca9e91bccb259cccdda9ed10cf3cb941f8266611535111818a043d753"
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
    "target_editor_smoke": False, "actual_hangul": False, "save_reopen": False,
    "render": False, "direct_automation_differential": False,
    "p07_07_target_layout": False, "p07_08_tier_b_target": False,
    "other_hangul_versions": False, "p07_complete": False,
    "production_ready": False, "product_complete": False,
}
GATE = {
    "component": "pass", "direct_stage": "unit_passed", "editor_target": "not_run",
    "actual_hangul": False, "save_reopen": False, "render": False,
    "p07_09": "in_progress", "p07": "in_progress", "product_complete": False,
}
MARKERS = {
    "crates/equation-engine/src/lib.rs": ("mod editor_smoke;", "EquationEditorSmokePlanner"),
    "crates/equation-engine/src/eqedit.rs": ("pub(crate) fn token_fingerprints",),
    "crates/equation-engine/src/editor_smoke.rs": (
        'EQUATION_EDITOR_SMOKE_SCHEMA_VERSION: &str = "hwpx-agent.equation-editor-smoke/v1"',
        "pub fn load_plan_json", "single_token_change", "pub fn verify_evidence_json",
        "computer_use_click_or_type_invoked", "FallbackDetected", "finish_non_exhaustive",
    ),
    "crates/equation-engine/tests/equation_editor_smoke.rs": (
        "exact_one_token_plan_and_combined_evidence_pass_deterministically",
        "private_plan_loader_recomputes_file_source_semantic_token_and_plan_hashes",
        "manual_automation_and_effect_proofs_are_all_mandatory",
        "object_semantic_graph_flow_reopen_and_fallback_drift_fail",
    ),
    PLAN_BUILDER: ("before oracle is not a bounded regular file", "EquationEditorSmokePlanner"),
    EVIDENCE_ORACLE: ("load_plan_json", "verify_evidence_json", "read_exact"),
    TARGET_ORACLE: ("read_automation_in_package", "package_state_sha256", "flow_sha256"),
    PARENT: ("EDITOR_SMOKE_PREEXISTING_HWP_PROCESS", "computer_use_click_or_type_invoked = $false", "Invoke-Oracle"),
    CHILD: ("P07_EDITOR_SMOKE_ACCESS_OR_MANUAL_ACTION_REQUIRED", "$window.Visible = $true", "$safeToQuit = $false"),
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
        return result(["contract_json_or_path"], 0, 0, False, False)
    exact = {
        "schema_version": "hwpx-agent.equation-editor-smoke-contract/v1",
        "request_schema_version": "hwpx-agent.equation-editor-smoke/v1",
        "evidence_schema_version": "hwpx-agent.equation-editor-smoke-evidence/v1",
        "receipt_schema_version": "hwpx-agent.equation-editor-smoke-receipt/v1",
        "profile_id": "hwpx-agent.equation-editor-smoke.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "task": "P07-09",
        "scope": "one_token_double_click_native_equation_edit_with_manual_and_automated_save_reopen_evidence",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION, "target_qualification": None,
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
        "plan": "complete_source_state_plus_two_roundtripping_math_ast_values_and_exactly_one_canonical_token_change",
        "manual": "user_double_click_editor_visibility_planned_token_commit_editor_close_and_four_distinct_screenshots",
        "automation": "exact_target_preflight_immutable_input_native_before_after_reopen_readback_save_close_reopen",
        "oracle": "strict_automation_native_hwpx_reader_id_index_package_state_equation_flow_and_plan_evidence_recheck",
        "computer_use": "screenshot_only_user_performs_all_clicks_and_typing",
    }:
        errors.append("workflow")
    failure = contract.get("failure_policy")
    if not isinstance(failure, list) or len(failure) != 12 or len(set(failure)) != 12:
        errors.append("failure_policy")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_markers(root, errors)
    harness_ok = validate_harnesses(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, harness_ok, qualification_ok)


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
        PARENT: PARENT_SHA256, CHILD: CHILD_SHA256, TARGET_ORACLE: TARGET_ORACLE_SHA256,
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
    if value.get("schema_version") != "hwpx-agent.equation-editor-smoke-source-qualification/v1" or value.get("task") != "P07-09" or value.get("recorded_date") != "2026-09-11":
        errors.append("qualification_identity")
    if value.get("target") != {"product": "Hangul 2020", "prog_id": "HWPFrame.HwpObject.2",
                                   "version": "11.0.0.9136", "executable_sha256": EXECUTABLE_SHA256,
                                   "architecture": "x86", "locale": "ko-KR",
                                   "other_versions": "not_qualified"}:
        errors.append("qualification_target")
    if value.get("harness_sources") != HARNESSES:
        errors.append("qualification_harness")
    if value.get("component_execution") != {"state": "pass", "rust_tests_passed": 10,
                                                "powershell_scripts_parsed": 2,
                                                "single_token_planner": "pass",
                                                "private_plan_reload": "pass",
                                                "combined_evidence_verifier": "pass",
                                                "native_hwpx_oracle_build": "pass",
                                                "silent_fallback_count": 0}:
        errors.append("qualification_component")
    target = value.get("target_execution")
    if not isinstance(target, dict) or target.get("state") != "not_run" or any(item is not None for key, item in target.items() if key != "state"):
        errors.append("qualification_target_run")
    if value.get("claims") != {"implementation_ready": True, "single_token_change_enforced": True,
                                    "manual_and_automation_required": True,
                                    "computer_use_screenshot_only_enforced": True,
                                    "target_editor_smoke": False, "actual_hangul": False,
                                    "save_reopen": False, "render": False,
                                    "p07_09_complete": False, "p07_complete": False,
                                    "product_complete": False}:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "Both are mandatory"),
        POLICY: ("implementation_ready / target_not_run", "exactly one differing token", "screenshot-only"),
        REPORT: ("10/10 PASS", "synthetic component evidence", "editor_target_state=not_run"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, harness: bool, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-editor-smoke-validation/v1",
        "state": "pass" if not unique else "fail", "errors": unique,
        "source_locks": sources, "implementation_files": implementation,
        "harness_sources_verified": harness, "source_qualification_verified": qualification,
        "task": "P07-09", "direct_stage": "unit_passed" if not unique else "not_proven",
        "editor_target": "not_run", "actual_hangul": False, "save_reopen": False,
        "render": False, "p07": "in_progress", "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(f"P07_EQUATION_EDITOR_SMOKE_CONTRACT_PASS source_locks={value['source_locks']} implementation_files={value['implementation_files']} editor_target=not_run")
