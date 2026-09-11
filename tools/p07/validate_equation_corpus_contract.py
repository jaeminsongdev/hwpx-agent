#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-equation-corpus-v1.json"
MIGRATION = "protocol/migrations/p07-equation-corpus-v0-to-v1.md"
POLICY = "implementation/p07/P07-08_EQUATION_CORPUS_POLICY.md"
REPORT = "implementation/p07/P07-08_EQUATION_CORPUS_REPORT.md"
QUALIFICATION = "implementation/p07/evidence/p07-08-equation-corpus-source-qualification.current-2020.v1.json"
MANIFEST = "implementation/p07/fixtures/p07-08-equation-corpus.current-2020.v1.json"
MANIFEST_SHA256 = "8893bd3169f40a5b49472cbb6c2dd4a578202b338d47d49270d237084ad6bd3f"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv", "README.md", "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md", "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
    "implementation/p07/P07-04_EQEDIT_POLICY.md",
    "implementation/p07/P07-07_EQUATION_LAYOUT_REPORT.md",
}
LIMITS = {
    "manifest_bytes": 8_388_608, "cases": 8_192, "case_id_bytes": 128,
    "source_bytes": 1_048_576, "legacy_bytes": 4_194_304,
    "serialized_bytes": 4_194_304,
}
NOT_CLAIMED = {
    "tier_b_target_execution": False, "actual_hangul": False, "save_reopen": False,
    "render": False, "editor_smoke": False, "automation_parity": False,
    "differential": False, "other_hangul_versions": False, "p07_complete": False,
    "production_ready": False, "product_complete": False,
}
GATE = {
    "component": "pass", "direct_stage": "unit_passed", "tier_a_component": "pass",
    "tier_b_component": "pass", "tier_b_target": "not_run", "tier_c_component": "pass",
    "actual_hangul": False, "render": False, "p07_08": "in_progress",
    "p07": "in_progress", "product_complete": False,
}
MARKERS = {
    "crates/equation-engine/src/lib.rs": ("mod corpus;", "EquationCorpusRunner", "LegacyEquationScript"),
    "crates/equation-engine/src/corpus.rs": (
        'EQUATION_CORPUS_SCHEMA_VERSION: &str = "hwpx-agent.equation-corpus/v1"',
        "pub fn run_json", "fn semantic_roundtrip", "fn preserve_exact", "fn reject_exact",
        "SilentApproximation", "finish_non_exhaustive",
    ),
    "crates/equation-engine/tests/equation_corpus.rs": (
        "hash_pinned_current_manifest_passes_all_component_tiers",
        "manifest_hash_and_strict_json_tampering_fail_closed",
        "negative_cases_require_the_exact_rejection_without_silent_acceptance",
        "legacy_boundary_preserves_exact_bytes_and_redacts_debug",
    ),
    "crates/hwpx-package/tests/equation_hwpx.rs": (
        "unrelated_same_part_edit_preserves_unsupported_legacy_script_byte_exactly",
        "record.output_sha256()",
    ),
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")
CASE_ID = re.compile(r"^[a-z0-9-]+$")


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


def digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False, False)
    exact = {
        "schema_version": "hwpx-agent.equation-corpus-contract/v1",
        "manifest_schema_version": "hwpx-agent.equation-corpus/v1",
        "receipt_schema_version": "hwpx-agent.equation-corpus-receipt/v1",
        "profile_id": "hwpx-agent.equation-corpus.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "task": "P07-08",
        "scope": "hash_pinned_tier_a_b_c_semantic_negative_and_legacy_preservation_corpus",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION, "target_qualification": None,
        "migration": MIGRATION, "policy": POLICY, "report": REPORT,
        "implementation_files": list(MARKERS), "default_limits": LIMITS,
        "not_claimed": NOT_CLAIMED, "gate_decision": GATE,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {*exact, "source_locks", "manifest", "tier_policy", "failure_policy"}:
        errors.append("contract_keys")
    expected_manifest = {
        "path": MANIFEST, "raw_sha256": MANIFEST_SHA256, "total_cases": 64,
        "tier_a_semantic": 44, "tier_b_semantic": 14, "tier_c_preserve": 2,
        "tier_c_reject": 4,
    }
    if contract.get("manifest") != expected_manifest:
        errors.append("contract_manifest")
    if contract.get("tier_policy") != {
        "minimum_tier_a_semantic": 40, "minimum_tier_b_semantic": 10,
        "minimum_tier_c_preserve": 2, "minimum_tier_c_reject": 2,
        "positive_check": "declared_adapter_to_math_ast_to_eqedit_to_math_ast_semantic_equality",
        "legacy_check": "opaque_utf8_bytes_and_sha256_preserved_exactly",
        "negative_check": "exact_stable_error_and_success_is_silent_approximation",
    }:
        errors.append("tier_policy")
    failure = contract.get("failure_policy")
    if not isinstance(failure, list) or len(failure) != 10 or len(set(failure)) != 10:
        errors.append("failure_policy")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_markers(root, errors)
    manifest_ok = validate_manifest(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, manifest_ok, qualification_ok)


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
            if digest(file(root, path)) != expected:
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


def validate_manifest(root: Path, errors: list[str]) -> bool:
    try:
        path = file(root, MANIFEST, LIMITS["manifest_bytes"])
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=duplicate_guard)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("manifest_json_or_path")
        return False
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        errors.append("manifest_digest")
    if not isinstance(value, dict) or set(value) != {"schema_version", "profile_version", "cases"}:
        errors.append("manifest_shape")
        return False
    if value.get("schema_version") != "hwpx-agent.equation-corpus/v1" or value.get("profile_version") != "hwpx-agent.equation-corpus.hangul-2020-11.0.0.9136-x86-ko-KR/v1":
        errors.append("manifest_identity")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 64:
        errors.append("manifest_cases")
        return False
    ids: set[str] = set()
    counts = {"a_semantic_roundtrip": 0, "b_semantic_roundtrip": 0,
              "c_preserve_exact": 0, "c_reject": 0}
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "tier", "source_kind", "source", "expectation", "expected_error_code"}:
            errors.append("manifest_case_shape")
            continue
        identity, tier, kind = case.get("id"), case.get("tier"), case.get("source_kind")
        source, expectation, code = case.get("source"), case.get("expectation"), case.get("expected_error_code")
        if not isinstance(identity, str) or not CASE_ID.fullmatch(identity) or identity in ids or len(identity) > 128:
            errors.append("manifest_case_id")
        else:
            ids.add(identity)
        if kind not in {"latex", "mathml", "eqedit", "legacy_eqedit"} or not isinstance(source, str) or not source or "\x00" in source or len(source.encode()) > LIMITS["source_bytes"]:
            errors.append("manifest_case_source")
        key = f"{tier}_{expectation}"
        if key not in counts:
            errors.append("manifest_case_policy")
        else:
            counts[key] += 1
        if expectation == "semantic_roundtrip" and (kind == "legacy_eqedit" or code is not None):
            errors.append("manifest_positive_policy")
        elif expectation == "preserve_exact" and (kind != "legacy_eqedit" or code is not None):
            errors.append("manifest_preserve_policy")
        elif expectation == "reject" and (kind == "legacy_eqedit" or not isinstance(code, str) or not re.fullmatch(r"[a-z0-9_]+", code)):
            errors.append("manifest_reject_policy")
    if counts != {"a_semantic_roundtrip": 44, "b_semantic_roundtrip": 14,
                   "c_preserve_exact": 2, "c_reject": 4}:
        errors.append("manifest_counts")
    return not any(error.startswith("manifest_") for error in errors)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if value.get("schema_version") != "hwpx-agent.equation-corpus-source-qualification/v1" or value.get("task") != "P07-08" or value.get("recorded_date") != "2026-09-11":
        errors.append("qualification_identity")
    target = value.get("target")
    if target != {"product": "Hangul 2020", "version": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR", "other_versions": "not_qualified"}:
        errors.append("qualification_target")
    if value.get("manifest") != {"path": MANIFEST, "raw_sha256": MANIFEST_SHA256,
                                  "total_cases": 64, "tier_a_semantic": 44,
                                  "tier_b_semantic": 14, "tier_c_preserve": 2,
                                  "tier_c_reject": 4}:
        errors.append("qualification_manifest")
    component = value.get("component_execution")
    if component != {"state": "pass", "tier_a_passed": 44, "tier_b_passed": 14,
                      "tier_c_preserve_passed": 2, "tier_c_negative_passed": 4,
                      "semantic_roundtrip_failures": 0, "legacy_preservation_failures": 0,
                      "negative_failures": 0, "silent_approximation_count": 0,
                      "synthetic_hwpx_same_part_preserve": "pass"}:
        errors.append("qualification_component")
    target_run = value.get("tier_b_target_execution")
    if not isinstance(target_run, dict) or target_run.get("state") != "not_run" or any(item is not None for key, item in target_run.items() if key != "state"):
        errors.append("qualification_target_run")
    claims = value.get("claims")
    if claims != {"tier_a_component_complete": True, "tier_b_component_complete": True,
                   "tier_c_component_complete": True, "legacy_synthetic_preservation": True,
                   "tier_b_target_complete": False, "actual_hangul": False, "render": False,
                   "p07_08_complete": False, "p07_complete": False, "product_complete": False}:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "never count as semantic success"),
        POLICY: ("unit_passed / tier_b_target_not_run", "64 cases", "component evidence only"),
        REPORT: ("10/10 PASS", "44/44", "14/14", "actual_hangul=false"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, manifest: bool, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-corpus-validation/v1",
        "state": "pass" if not unique else "fail", "errors": unique,
        "source_locks": sources, "implementation_files": implementation,
        "manifest_verified": manifest, "source_qualification_verified": qualification,
        "task": "P07-08", "direct_stage": "unit_passed" if not unique else "not_proven",
        "tier_b_target": "not_run", "actual_hangul": False, "render": False,
        "p07": "in_progress", "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(f"P07_EQUATION_CORPUS_CONTRACT_PASS source_locks={value['source_locks']} implementation_files={value['implementation_files']} tier_b_target=not_run")
