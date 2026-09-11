#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p07-equation-layout-v1.json"
MIGRATION = "protocol/migrations/p07-equation-layout-v0-to-v1.md"
POLICY = "implementation/p07/P07-07_EQUATION_LAYOUT_POLICY.md"
REPORT = "implementation/p07/P07-07_EQUATION_LAYOUT_REPORT.md"
QUALIFICATION = "implementation/p07/evidence/p07-07-equation-layout-source-qualification.current-2020.v1.json"
SOURCES = {
    "WORK_BREAKDOWN_STRUCTURE.csv", "README.md", "docs/03_document_model/07_equation_model.md",
    "docs/04_feature_catalog/08_eq.md", "docs/04_feature_catalog/contracts/08_eq_contracts.md",
    "docs/09_roadmap/P07_native_equation_engine.md",
    "docs/12_implementation_guides/06_native_equation_pipeline.md",
    "implementation/p07/P07-05_NATIVE_EQUATION_HWPX_POLICY.md",
    "implementation/p07/P07-06_EQUATION_AUTOMATION_REPORT.md",
}
LIMITS = {
    "qualification_bytes": 4_194_304, "samples": 4_096, "base_unit": 100_000,
    "extent_hwpunit": 10_000_000, "metric_units": 1_000_000, "page_pixels": 100_000,
    "serialized_bytes": 4_194_304,
}
NOT_CLAIMED = {
    "actual_target_layout_calibration": False, "verified_estimator_active": False,
    "baseline_visual": False, "ink_box_visual": False, "render": False,
    "p07_08_corpus": False, "p07_09_editor_smoke": False, "other_hangul_versions": False,
    "p07_complete": False, "production_ready": False, "product_complete": False,
}
GATE = {
    "component": "pass", "direct_stage": "unit_passed", "target_qualification": "not_run",
    "actual_hangul": False, "render": False, "p07_07": "in_progress",
    "p07": "in_progress", "product_complete": False,
}
MARKERS = {
    "crates/equation-engine/src/lib.rs": ("mod layout;", "EquationLayoutEstimator"),
    "crates/equation-engine/src/layout.rs": (
        'EQUATION_LAYOUT_SCHEMA_VERSION: &str = "hwpx-agent.equation-layout/v1"',
        "EquationLayoutSource", "from_qualification_json", "measure_node",
        "FailedVisualQualification", "finish_non_exhaustive",
    ),
    "crates/equation-engine/tests/equation_layout.rs": (
        "unqualified_estimates_are_conservative_provisional_and_render_required",
        "exact_sample_uses_target_readback_without_recomputing_extent",
        "qualified_model_is_used_only_inside_its_complete_envelope",
        "qualification_digest_schema_visual_and_sample_tamper_fail_closed",
    ),
    "crates/hwpx-package/src/equation.rs": (
        "from_layout_estimate", "from_draft_with_layout_estimate",
        "estimate.semantic_sha256() != semantic_sha256",
    ),
    "crates/hwpx-package/tests/equation_hwpx.rs": (
        "opaque_layout_estimate_is_bound_to_semantic_layout_style_and_extent",
    ),
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


def digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)
    exact = {
        "schema_version": "hwpx-agent.equation-layout-contract/v1",
        "estimate_schema_version": "hwpx-agent.equation-layout/v1",
        "qualification_schema_version": "hwpx-agent.equation-layout-qualification/v1",
        "profile_id": "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "task": "P07-07",
        "scope": "typed_structural_equation_extent_baseline_estimator_and_hwpx_binding",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION, "target_qualification": None,
        "migration": MIGRATION, "policy": POLICY, "report": REPORT,
        "implementation_files": list(MARKERS), "default_limits": LIMITS,
        "not_claimed": NOT_CLAIMED, "gate_decision": GATE,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    if set(contract) != {
        *exact, "source_locks", "estimation_order", "qualification", "binding", "failure_policy"
    }:
        errors.append("contract_keys")
    if contract.get("estimation_order") != {
        "exact": "trusted_semantic_layout_base_unit_target_readback_sample",
        "model": "trusted_fixed_point_font_model_inside_complete_structural_envelope",
        "fallback": "conservative_provisional_without_evidence_and_render_required",
    }:
        errors.append("estimation_order")
    if contract.get("qualification") != {
        "minimum_inline_samples": 4, "minimum_display_samples": 4,
        "maximum_extent_error_hwpunit": 150,
        "maximum_baseline_error_hwpunit": 50, "maximum_ink_overflow_count": 0,
        "maximum_clipping_count": 0, "maximum_overlap_count": 0,
        "maximum_silent_fallback_count": 0, "all_pages_inspected": True,
        "trusted_exact_byte_sha_required": True,
    }:
        errors.append("qualification")
    if contract.get("binding") != {
        "semantic": "normalized_math_ast_semantic_sha", "layout": "inline_or_display",
        "style": "base_unit_and_baseline_percent",
        "extent": "width_height_source_evidence_and_render_required",
        "hwpx": "opaque_estimate_required_for_target_readback_or_validated_estimator",
    }:
        errors.append("binding")
    failure = contract.get("failure_policy")
    if not isinstance(failure, list) or len(failure) != 11 or len(set(failure)) != 11:
        errors.append("failure_policy")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_markers(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


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


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    target = value.get("target")
    observations = value.get("available_nonqualifying_observations")
    target_run = value.get("dedicated_target_calibration")
    claims = value.get("claims")
    if value.get("schema_version") != "hwpx-agent.equation-layout-source-qualification/v1" or value.get("task") != "P07-07" or value.get("recorded_date") != "2026-09-11":
        errors.append("qualification_identity")
    if target != {"product": "Hangul 2020", "version": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR", "font_name": "HancomEQN", "other_versions": "not_qualified"}:
        errors.append("qualification_target")
    if not isinstance(observations, dict) or observations.get("display_native_readback_samples") != 2 or observations.get("inline_native_readback_samples") != 0 or observations.get("ink_box_samples") != 0 or observations.get("can_qualify_model") is not False:
        errors.append("qualification_observations")
    if not isinstance(target_run, dict) or target_run.get("state") != "not_run" or any(value is not None for key, value in target_run.items() if key != "state"):
        errors.append("qualification_target_run")
    if claims != {"typed_layout_model": True, "provisional_fallback": True, "trusted_qualification_loader": True, "actual_target_layout_calibration": False, "verified_estimator_active": False, "baseline_visual": False, "ink_box_visual": False, "p07_07_complete": False, "product_complete": False}:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "opaque estimator result"),
        POLICY: ("unit_passed / target_not_run", "at least four inline", "Raw extent JSON cannot promote"),
        REPORT: ("8/8 PASS", "13/13 PASS", "zero inline ink-box measurements"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-layout-validation/v1",
        "state": "pass" if not unique else "fail", "errors": unique,
        "source_locks": sources, "implementation_files": implementation,
        "source_qualification_verified": qualification, "task": "P07-07",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "target_qualification": "not_run", "actual_hangul": False, "render": False,
        "p07": "in_progress", "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(f"P07_EQUATION_LAYOUT_CONTRACT_PASS source_locks={value['source_locks']} implementation_files={value['implementation_files']} target_qualification=not_run")
