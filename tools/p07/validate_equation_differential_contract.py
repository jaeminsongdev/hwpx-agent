#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-equation-differential-v1.json"
MIGRATION = "protocol/migrations/p07-equation-differential-v0-to-v1.md"
REPORT = "implementation/p07/P07_GATE_DIFFERENTIAL_REPORT.md"
ORACLE = "crates/hwpx-package/examples/p07_phase_equation_differential.rs"
ORACLE_SHA256 = "44e54af33d79d9840725638faef92636cc3370e042db4519c50387cd24903244"
QUALIFICATION = "implementation/p07/evidence/p07-equation-differential.current-2020.v1.json"
QUALIFICATION_SHA256 = "1632774d0b783fb23ae9e9e7e0c7d5db32932b26230db4c629dd1e1f2aa76918"
DIRECT_TARGET = "implementation/p07/evidence/target/p07-05-native-equation.current-2020.attempt01.v1.json"
DIRECT_TARGET_SHA256 = "58d6a3599492d57cc873d9c80f83f606aa32aae38f9c514cdcec7eb00fe12a5f"
PROFILE = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
TARGET_EXE_SHA256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv": "3a115b34b4bb57d50ac3899aee7d8155e69a6290c524b976e9b65b848efad444",
    "docs/09_roadmap/P07_native_equation_engine.md": "5e2f87f8b568cc60023b9571ddace660f10189eefa6fa6f348be94ac54ea803f",
    "implementation/p07/P07-05_NATIVE_EQUATION_HWPX_REPORT.md": "7636f9842f7d9522255c0bacd00b1c5c42e039ccab8a93fe29e84c2c1867f57b",
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


def file(root: Path, relative: str, maximum: int = 16 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load(root: Path, relative: str) -> Any:
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard)


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, False, False, False)
    exact = {
        "schema_version": "hwpx-agent.p07-equation-differential-contract/v1",
        "qualification_schema_version": "hwpx-agent.p07-equation-differential-qualification/v1",
        "receipt_schema_version": "hwpx-agent.p07-equation-differential-receipt/v1",
        "profile_id": PROFILE,
        "task": "P07-GATE",
        "scope": "matched_direct_component_and_exact_target_automation_semantic_script_layout_parity",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "oracle": {"path": ORACLE, "raw_sha256": ORACLE_SHA256},
        "qualification": {"path": QUALIFICATION, "raw_sha256": QUALIFICATION_SHA256},
        "direct_target_evidence": {"path": DIRECT_TARGET, "raw_sha256": DIRECT_TARGET_SHA256},
        "migration": MIGRATION,
        "report": REPORT,
        "comparison_policy": {
            "required_cases": 8, "required_inline": 4, "required_display": 4,
            "equal_fields": ["normalized_semantic_sha256", "canonical_eqedit_script_sha256", "layout"],
            "normalized_nonidentity_fields": ["zip_bytes", "native_object_id", "extent", "line_cache"],
            "maximum_silent_fallback_count": 0,
            "direct_exact_target_compatibility_required": True,
            "automation_exact_target_execution_required": True,
        },
        "failure_policy": [
            "malformed_duplicate_unknown_oversized_or_untrusted_contract_rejected",
            "source_or_oracle_qualification_and_direct_target_digest_drift_rejected",
            "missing_duplicate_or_wrong_mode_case_count_rejected",
            "semantic_script_or_layout_mismatch_rejected",
            "silent_fallback_or_missing_route_target_boundary_rejected",
            "byte_object_id_extent_or_line_cache_nonidentity_is_not_semantic_failure",
            "private_scripts_paths_and_raw_documents_are_not_published",
        ],
        "not_claimed": {
            "byte_identity": False, "object_id_identity": False, "extent_identity": False,
            "render": False, "other_hangul_versions": False, "p07_complete": False,
            "production_ready": False, "product_complete": False,
        },
        "gate_decision": {
            "component": "pass", "direct_target_compatibility": "pass",
            "automation_target_execution": "pass", "matched_differential": "pass",
            "actual_hangul": True, "render": False, "p07": "in_progress",
            "product_complete": False,
        },
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {*exact, "source_locks"}:
        errors.append("contract_keys")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    oracle_ok = validate_oracle(root, errors)
    qualification_ok = validate_qualification(root, errors)
    direct_target_ok = validate_direct_target(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, oracle_ok, qualification_ok, direct_target_ok)


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
        if (not isinstance(path, str) or path in declared or not isinstance(expected, str)
                or not DIGEST.fullmatch(expected)):
            errors.append("source_lock_identity")
            continue
        declared[path] = expected
        try:
            if text_digest(file(root, path)) != expected:
                errors.append("source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_path")
    if declared != SOURCES:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_oracle(root: Path, errors: list[str]) -> bool:
    try:
        path = file(root, ORACLE)
        text = path.read_text(encoding="utf-8")
        if raw_digest(path) != ORACLE_SHA256:
            errors.append("oracle_digest")
        for marker in (
            "direct_and_automation_semantic_equal", "direct_and_automation_script_equal",
            "direct_and_automation_layout_equal", "artifact changed during differential read",
            "direct_exact_target_compatibility", "byte_identity_required",
        ):
            if marker not in text:
                errors.append("oracle_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("oracle_path")
    return not any(error.startswith("oracle_") for error in errors)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        path = file(root, QUALIFICATION)
        value = json.loads(path.read_bytes(), object_pairs_hook=duplicate_guard)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if raw_digest(path) != QUALIFICATION_SHA256:
        errors.append("qualification_digest")
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "task", "recorded_date", "target", "identities", "comparison", "claims"
    }:
        errors.append("qualification_shape")
        return False
    if (value.get("schema_version") != "hwpx-agent.p07-equation-differential-qualification/v1"
            or value.get("task") != "P07-GATE" or value.get("recorded_date") != "2026-09-14"):
        errors.append("qualification_identity")
    if value.get("target") != {
        "product": "Hangul 2020", "prog_id": "HWPFrame.HwpObject.2",
        "version": "11.0.0.9136", "executable_sha256": TARGET_EXE_SHA256,
        "architecture": "x86", "locale": "ko-KR",
    }:
        errors.append("qualification_target")
    if value.get("identities") != {
        "oracle_raw_sha256": ORACLE_SHA256,
        "plan_file_sha256": "7244cf6c336533763918b44280129ab10f07f0c6279e8416f706e4a9058e5cc8",
        "automation_target_evidence_sha256": "f0c4088efe397e792399913fc14ed01d6a37de29c3910b667bed9ccf7525e048",
        "direct_target_evidence_sha256": DIRECT_TARGET_SHA256,
        "differential_receipt_sha256": "a214cdacfa2f78c4f530d9a1d0d314c317526f7992872bc35fab4270f4d81713",
    }:
        errors.append("qualification_identities")
    if value.get("comparison") != {
        "state": "pass", "case_count": 8, "inline_case_count": 4,
        "display_case_count": 4, "semantic_equal_count": 8, "script_equal_count": 8,
        "layout_equal_count": 8, "silent_fallback_count": 0,
        "direct_component_generation": True, "direct_exact_target_compatibility": True,
        "automation_exact_target_execution": True, "byte_identity_required": False,
        "object_id_identity_required": False,
    }:
        errors.append("qualification_comparison")
    if value.get("claims") != {
        "scoped_direct_automation_differential": True, "actual_hangul": True,
        "render": False, "other_hangul_versions": False, "p07_complete": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_direct_target(root: Path, errors: list[str]) -> bool:
    try:
        path = file(root, DIRECT_TARGET)
        value = json.loads(path.read_bytes(), object_pairs_hook=duplicate_guard)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("direct_target_json_or_path")
        return False
    if raw_digest(path) != DIRECT_TARGET_SHA256:
        errors.append("direct_target_digest")
    if (value.get("schema_version") != "hwpx-agent.p07-05-native-equation-current-2020-evidence/v1"
            or value.get("target", {}).get("executable_sha256") != TARGET_EXE_SHA256):
        errors.append("direct_target_identity")
    claims = value.get("claims", {})
    if any(claims.get(key) is not True for key in (
        "new_lowerer_actual_hangul_execution", "new_lowerer_save_reopen",
        "native_semantic_readback", "render",
    )):
        errors.append("direct_target_claims")
    return not any(error.startswith("direct_target_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT relabel", "ZIP bytes"),
        REPORT: ("scoped differential `pass`", "inline and four display", "zero silent fallback"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(
    errors: list[str], sources: int, oracle: bool, qualification: bool, direct_target: bool,
) -> dict[str, Any]:
    unique = sorted(set(errors))
    passed = not unique
    return {
        "schema_version": "hwpx-agent.p07-equation-differential-validation/v1",
        "state": "pass" if passed else "fail", "errors": unique,
        "source_locks": sources, "oracle_verified": oracle,
        "qualification_verified": qualification, "direct_target_evidence_verified": direct_target,
        "task": "P07-GATE", "matched_cases": 8 if passed else 0,
        "differential": "pass" if passed else "not_proven",
        "actual_hangul": passed, "render": False, "p07": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(f"P07_EQUATION_DIFFERENTIAL_CONTRACT_PASS matched_cases={value['matched_cases']}")
