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
TARGET_QUALIFICATION = "implementation/p07/evidence/p07-07-equation-layout-target-qualification.current-2020.v1.json"
TARGET_QUALIFICATION_SHA256 = "dff15f942fceb3a4b4f967fe13de07c800768649c6e5f76342c6f3f98b729381"
GATE_PROFILE = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
CALIBRATION_MANIFEST = "implementation/p07/fixtures/p07-07-equation-layout-samples.current-2020.v1.json"
CALIBRATION_MANIFEST_SHA256 = "d689991e3c92fcd81aa21c64dde5cbff17a57f4a33b89976ef35058b08c76944"
PLAN_BUILDER = "crates/equation-engine/examples/p07_07_layout_target_plan.rs"
HWPX_ORACLE = "crates/hwpx-package/examples/p07_07_equation_layout_oracle.rs"
QUALIFICATION_ORACLE = "crates/equation-engine/examples/p07_07_layout_qualification_oracle.rs"
PARENT = "implementation/p07/tools/run-hancom-2020-equation-layout.ps1"
CHILD = "implementation/p07/tools/run-hancom-2020-equation-layout-child.ps1"
RASTER_VERIFIER = "implementation/p07/tools/verify-equation-layout-pdfs.py"
QUALIFICATION_BUILDER = "implementation/p07/tools/build-equation-layout-qualification.py"
TARGET_TOOLCHAIN = {
    "plan_schema_version": "hwpx-agent.p07-07-equation-layout-target-plan/v1",
    "target_evidence_schema_version": "hwpx-agent.p07-07-equation-layout-target-evidence/v1",
    "raster_evidence_schema_version": "hwpx-agent.p07-07-equation-layout-raster-evidence/v1",
    "manual_review_schema_version": "hwpx-agent.p07-07-equation-layout-manual-review/v1",
    "plan_builder_path": PLAN_BUILDER,
    "plan_builder_raw_sha256": "1062bcfacaa9bf5a1c84218f72cdd1dc10ee4d7f2bad3d064bcb552a75de2966",
    "hwpx_oracle_path": HWPX_ORACLE,
    "hwpx_oracle_raw_sha256": "adea0ddb0c4bb5905ffc419146f936bf2f3aebb59616d6ed8e54e769f8da305e",
    "qualification_oracle_path": QUALIFICATION_ORACLE,
    "qualification_oracle_raw_sha256": "da906746e63bd14c3a7a04aec853d1b9bf9474e80c24e114abc350891d646a7c",
    "parent_path": PARENT,
    "parent_raw_sha256": "90f3e1564ff6a92f60d3a366c5057f4ce4d41836da27a63665975bb36f3b9cee",
    "child_path": CHILD,
    "child_raw_sha256": "cfe69f59dcb56f8c73e47c58ac5547b0286019738ce257d8300b7082b60fef41",
    "harness_bundle_sha256": "b0deb368341245ce0e55ff3a63f470f0e7c7c3c9dfdbb5f342cc9244b6e55c47",
    "raster_verifier_path": RASTER_VERIFIER,
    "raster_verifier_raw_sha256": "1cfc9bb244b48089a516efa00bfe2a6367f322244150495039a8edbcb94d5eb7",
    "qualification_builder_path": QUALIFICATION_BUILDER,
    "qualification_builder_raw_sha256": "74c1829a33780f55a4d9d1a696930668399a5464d3aee11a68ffb860996bc854",
    "toolchain_bundle_sha256": "b374ca058c4ef21d78d2fbd8db89669220c12490ee7fc0f94e8eb01e3196ba66",
}
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
    "verified_estimator_active": False,
    "p07_08_corpus": False, "p07_09_editor_smoke": False, "other_hangul_versions": False,
    "p07_complete": False, "production_ready": False, "product_complete": False,
}
GATE = {
    "component": "pass", "direct_stage": "target_passed",
    "target_qualification": "pass_exact_samples_general_estimator_inactive",
    "actual_hangul": True, "render": True, "manual_review": "user_attested",
    "verified_estimator_active": False, "unknown_shapes": "render_required", "p07_07": "pass",
    "p07": "in_progress", "product_complete": False,
}
MARKERS = {
    "crates/equation-engine/src/lib.rs": ("mod layout;", "EquationLayoutEstimator", "EquationLayoutMetrics"),
    "crates/equation-engine/src/layout.rs": (
        'EQUATION_LAYOUT_SCHEMA_VERSION: &str = "hwpx-agent.equation-layout/v1"',
        "EquationLayoutSource", "from_qualification_json", "pub fn measure", "measure_node",
        "FailedVisualQualification", "finish_non_exhaustive",
    ),
    "crates/equation-engine/tests/equation_layout.rs": (
        "unqualified_estimates_are_conservative_provisional_and_render_required",
        "exact_sample_uses_target_readback_without_recomputing_extent",
        "qualified_model_is_used_only_inside_its_complete_envelope",
        "high_error_model_keeps_exact_samples_but_unknown_shapes_render_required",
        "qualification_digest_schema_visual_and_sample_tamper_fail_closed",
    ),
    "crates/hwpx-package/src/equation.rs": (
        "from_layout_estimate", "from_draft_with_layout_estimate",
        "estimate.semantic_sha256() != semantic_sha256",
    ),
    "crates/hwpx-package/tests/equation_hwpx.rs": (
        "opaque_layout_estimate_is_bound_to_semantic_layout_style_and_extent",
    ),
    PLAN_BUILDER: (
        "TARGET_PLAN_SCHEMA", "EquationLayoutEstimator::provisional", ".measure(draft)",
        "layout sample mode coverage is incomplete",
    ),
    HWPX_ORACLE: (
        "read_automation_in_package", "expected_layout", "native_readback_sha256",
        "layout oracle input changed during readback",
    ),
    QUALIFICATION_ORACLE: (
        "from_qualification_json", "qualification_schema_valid",
        "exact_sample_qualification", "verified_estimator_active",
        "actual_hangul_asserted_by_oracle", "product_complete",
    ),
    PARENT: (
        "LAYOUT_PREEXISTING_HWP_PROCESS", "Test-MetricsEqual",
        "pdf_exported_visual_not_run", "visual_state = 'not_run'",
    ),
    CHILD: (
        "P07_LAYOUT_SECURITY_MODULE_CALL_COMPLETED", "Insert-PlainText",
        "Set-ComProperty $ParameterSet 'LineMode'", "LAYOUT_REOPEN_READBACK_MISMATCH",
    ),
    RASTER_VERIFIER: (
        '"structural_pass_manual_not_run"', '"qualification_eligible": False',
        "INK_THRESHOLD", "LAYOUT_INK_BOX_TOUCHES_PAGE_EDGE",
    ),
    QUALIFICATION_BUILDER: (
        "validate_manual", "fit_linear", '"exact_sample_qualification_candidate": True',
        '"verified_estimator_candidate": (',
        '"actual_hangul_asserted_by_builder": False',
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


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False, False, False, False)
    exact = {
        "schema_version": "hwpx-agent.equation-layout-contract/v1",
        "estimate_schema_version": "hwpx-agent.equation-layout/v1",
        "qualification_schema_version": "hwpx-agent.equation-layout-qualification/v1",
        "profile_id": "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1",
        "task": "P07-07",
        "scope": "typed_structural_equation_extent_baseline_estimator_and_hwpx_binding",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "target_qualification": {
            "path": TARGET_QUALIFICATION, "raw_sha256": TARGET_QUALIFICATION_SHA256,
        },
        "calibration_manifest": {
            "path": CALIBRATION_MANIFEST, "raw_sha256": CALIBRATION_MANIFEST_SHA256,
            "sample_count": 8, "inline_samples": 4, "display_samples": 4,
            "source": "hash_pinned_p07_08_tier_b_target_plan",
        },
        "target_toolchain": TARGET_TOOLCHAIN,
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
        "model": "trusted_fixed_point_font_model_inside_complete_structural_envelope_only_when_error_thresholds_pass",
        "fallback": "conservative_provisional_without_evidence_and_render_required",
    }:
        errors.append("estimation_order")
    if contract.get("qualification") != {
        "minimum_inline_samples": 4, "minimum_display_samples": 4,
        "verified_estimator_maximum_extent_error_hwpunit": 150,
        "verified_estimator_maximum_baseline_error_hwpunit": 50,
        "maximum_ink_overflow_count": 0,
        "maximum_clipping_count": 0, "maximum_overlap_count": 0,
        "maximum_silent_fallback_count": 0, "all_pages_inspected": True,
        "trusted_exact_byte_sha_required": True,
        "model_error_threshold_scope": "verified_estimator_only_exact_samples_remain_admissible",
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
    if not isinstance(failure, list) or len(failure) != 12 or len(set(failure)) != 12:
        errors.append("failure_policy")
    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_markers(root, errors)
    calibration_ok = validate_calibration_manifest(root, errors)
    toolchain_ok = validate_target_toolchain(root, errors)
    qualification_ok = validate_qualification(root, errors)
    target_qualification_ok = validate_target_qualification(root, errors)
    validate_documents(root, errors)
    return result(
        errors, source_count, implementation_count, qualification_ok, target_qualification_ok,
        calibration_ok, toolchain_ok,
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


def validate_calibration_manifest(root: Path, errors: list[str]) -> bool:
    try:
        path = file(root, CALIBRATION_MANIFEST, 64 * 1024)
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=duplicate_guard)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("calibration_manifest_json_or_path")
        return False
    if hashlib.sha256(raw).hexdigest() != CALIBRATION_MANIFEST_SHA256:
        errors.append("calibration_manifest_digest")
    if not isinstance(value, dict) or set(value) != {"schema_version", "profile_version", "samples"}:
        errors.append("calibration_manifest_shape")
        return False
    samples = value.get("samples")
    if value.get("schema_version") != "hwpx-agent.p07-07-equation-layout-samples/v1" \
            or value.get("profile_version") != "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1" \
            or not isinstance(samples, list) or len(samples) != 8:
        errors.append("calibration_manifest_identity")
        return False
    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    modes = {"inline": 0, "display": 0}
    for index, sample in enumerate(samples):
        expected_mode = "inline" if index < 4 else "display"
        expected_id = f"{expected_mode}-{index % 4 + 1:03d}"
        if not isinstance(sample, dict) or set(sample) != {"id", "corpus_case_id", "layout"}:
            errors.append("calibration_manifest_sample_shape")
            continue
        identity, corpus, mode = sample.get("id"), sample.get("corpus_case_id"), sample.get("layout")
        if identity != expected_id or mode != expected_mode \
                or not isinstance(corpus, str) or not re.fullmatch(r"b-[0-9]{3}", corpus) \
                or identity in ids or (corpus, mode) in pairs:
            errors.append("calibration_manifest_sample_identity")
            continue
        ids.add(identity); pairs.add((corpus, mode)); modes[mode] += 1
    if modes != {"inline": 4, "display": 4}:
        errors.append("calibration_manifest_mode_coverage")
    return not any(error.startswith("calibration_manifest_") for error in errors)


def validate_target_toolchain(root: Path, errors: list[str]) -> bool:
    path_hashes = [
        (PLAN_BUILDER, TARGET_TOOLCHAIN["plan_builder_raw_sha256"]),
        (HWPX_ORACLE, TARGET_TOOLCHAIN["hwpx_oracle_raw_sha256"]),
        (QUALIFICATION_ORACLE, TARGET_TOOLCHAIN["qualification_oracle_raw_sha256"]),
        (PARENT, TARGET_TOOLCHAIN["parent_raw_sha256"]),
        (CHILD, TARGET_TOOLCHAIN["child_raw_sha256"]),
        (RASTER_VERIFIER, TARGET_TOOLCHAIN["raster_verifier_raw_sha256"]),
        (QUALIFICATION_BUILDER, TARGET_TOOLCHAIN["qualification_builder_raw_sha256"]),
    ]
    for relative, expected in path_hashes:
        try:
            if raw_digest(file(root, relative)) != expected:
                errors.append("target_toolchain_digest")
        except (OSError, ValueError):
            errors.append("target_toolchain_path")
    harness = hashlib.sha256((
        TARGET_TOOLCHAIN["parent_raw_sha256"] + ":" + TARGET_TOOLCHAIN["child_raw_sha256"]
    ).encode()).hexdigest()
    if harness != TARGET_TOOLCHAIN["harness_bundle_sha256"]:
        errors.append("target_toolchain_harness_bundle")
    all_hashes = [CALIBRATION_MANIFEST_SHA256, *(expected for _, expected in path_hashes)]
    if hashlib.sha256(":".join(all_hashes).encode()).hexdigest() \
            != TARGET_TOOLCHAIN["toolchain_bundle_sha256"]:
        errors.append("target_toolchain_bundle")
    return not any(error.startswith("target_toolchain_") for error in errors)


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
    if value.get("schema_version") != "hwpx-agent.equation-layout-source-qualification/v1" or value.get("task") != "P07-07" or value.get("recorded_date") != "2026-09-14":
        errors.append("qualification_identity")
    if target != {"product": "Hangul 2020", "version": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR", "font_name": "HancomEQN", "other_versions": "not_qualified"}:
        errors.append("qualification_target")
    if not isinstance(observations, dict) or observations.get("display_native_readback_samples") != 2 or observations.get("inline_native_readback_samples") != 0 or observations.get("ink_box_samples") != 0 or observations.get("can_qualify_model") is not False:
        errors.append("qualification_observations")
    if target_run != {
        "state": "pass_exact_samples_general_estimator_inactive",
        "tooling_state": "target_passed",
        "toolchain_bundle_sha256": TARGET_TOOLCHAIN["toolchain_bundle_sha256"],
        "plan_file_sha256": "7244cf6c336533763918b44280129ab10f07f0c6279e8416f706e4a9058e5cc8",
        "target_evidence_sha256": "f0c4088efe397e792399913fc14ed01d6a37de29c3910b667bed9ccf7525e048",
        "raster_evidence_sha256": "e5eff31859c7a083bd158f087668a09879c41443b82dea1419191d8106dc7ced",
        "manual_review_sha256": "8f42081b7251ab69b3a43cd1442ac3cfd3abd3d206d7d4fd6c09a3ce1e7158be",
        "qualification_sha256": TARGET_QUALIFICATION_SHA256,
        "evidence_sha256": "d434909f98b97de2d4ee1cc57323aab3690e35916187128986297949275c59d5",
        "font_metrics_sha256": "06c43b824ed05c442c81895a17126555a297ceae0e6f11565f01338eb1779202",
        "corpus_semantic_sha256": "240bf3cf8cc335c3237bcd99b5425bd18b7554fecb54dc28834808022500a248",
        "sample_count": 8, "inline_sample_count": 4, "display_sample_count": 4,
        "extent_max_error_hwpunit": 1868, "baseline_max_error_hwpunit": 105,
        "ink_box_overflow_count": 0, "clipping_count": 0, "overlap_count": 0,
        "silent_fallback_count": 0, "all_pages_inspected": True,
        "manual_review": "user_attested", "verified_estimator_active": False,
        "unknown_shapes": "render_required",
    }:
        errors.append("qualification_target_run")
    if claims != {"typed_layout_model": True, "provisional_fallback": True,
                   "trusted_qualification_loader": True,
                   "actual_target_layout_calibration": True,
                   "verified_estimator_active": False, "baseline_visual": True,
                   "ink_box_visual": True, "render": True,
                   "p07_07_complete": True, "product_complete": False}:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_target_qualification(root: Path, errors: list[str]) -> bool:
    try:
        path = file(root, TARGET_QUALIFICATION, 4 * 1024 * 1024)
        value = json.loads(path.read_bytes(), object_pairs_hook=duplicate_guard)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("target_qualification_json_or_path")
        return False
    if raw_digest(path) != TARGET_QUALIFICATION_SHA256:
        errors.append("target_qualification_digest")
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "profile_version", "target", "evidence_sha256",
        "font_metrics_sha256", "corpus_semantic_sha256", "model", "envelope",
        "validation", "exact_samples",
    }:
        errors.append("target_qualification_shape")
        return False
    if (value.get("schema_version") != "hwpx-agent.equation-layout-qualification/v1"
            or value.get("profile_version") != GATE_PROFILE
            or value.get("target") != {
                "build": "11.0.0.9136", "architecture": "x86",
                "locale": "ko-KR", "font_name": "HancomEQN",
            }):
        errors.append("target_qualification_identity")
    for key, expected in {
        "evidence_sha256": "d434909f98b97de2d4ee1cc57323aab3690e35916187128986297949275c59d5",
        "font_metrics_sha256": "06c43b824ed05c442c81895a17126555a297ceae0e6f11565f01338eb1779202",
        "corpus_semantic_sha256": "240bf3cf8cc335c3237bcd99b5425bd18b7554fecb54dc28834808022500a248",
    }.items():
        if value.get(key) != expected:
            errors.append("target_qualification_binding")
    validation = value.get("validation")
    if validation != {
        "sample_count": 8, "inline_sample_count": 4, "display_sample_count": 4,
        "extent_max_error_hwpunit": 1868, "baseline_max_error_hwpunit": 105,
        "ink_box_overflow_count": 0, "clipping_count": 0, "overlap_count": 0,
        "silent_fallback_count": 0, "all_pages_inspected": True,
    }:
        errors.append("target_qualification_validation")
    samples = value.get("exact_samples")
    if not isinstance(samples, list) or len(samples) != 8:
        errors.append("target_qualification_samples")
    else:
        for index, sample in enumerate(samples):
            expected_layout = "inline" if index < 4 else "display"
            if (not isinstance(sample, dict)
                    or sample.get("layout") != expected_layout
                    or sample.get("base_unit") != 1000
                    or not DIGEST.fullmatch(str(sample.get("semantic_sha256", "")))
                    or not DIGEST.fullmatch(str(sample.get("native_readback_sha256", "")))
                    or not DIGEST.fullmatch(str(sample.get("render_evidence_sha256", "")))):
                errors.append("target_qualification_samples")
                break
    if isinstance(validation, dict) and (
        validation.get("extent_max_error_hwpunit", 0) <= 150
        and validation.get("baseline_max_error_hwpunit", 0) <= 50
    ):
        errors.append("target_qualification_general_estimator_state")
    return not any(error.startswith("target_qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    for relative, markers in {
        MIGRATION: ("There is no stored v0", "MUST NOT be relabeled", "opaque estimator result"),
        POLICY: ("target_passed_exact_samples", "requires at least four", "Raw extent JSON cannot promote"),
        REPORT: ("target_passed_exact_samples", "User-attested manual review SHA-256", "general estimator"),
    }.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(
    errors: list[str], sources: int, implementation: int, qualification: bool,
    target_qualification: bool, calibration_manifest: bool, target_toolchain: bool,
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p07-equation-layout-validation/v1",
        "state": "pass" if not unique else "fail", "errors": unique,
        "source_locks": sources, "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "target_qualification_verified": target_qualification,
        "calibration_manifest_verified": calibration_manifest,
        "target_toolchain_verified": target_toolchain, "task": "P07-07",
        "direct_stage": "target_passed" if not unique else "not_proven",
        "target_qualification": "pass" if not unique else "not_proven",
        "manual_review": "user_attested" if not unique else "not_proven",
        "verified_estimator_active": False, "unknown_shapes": "render_required",
        "actual_hangul": not unique, "render": not unique,
        "p07": "in_progress", "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if value["state"] != "pass":
        sys.exit(1)
    print(f"P07_EQUATION_LAYOUT_CONTRACT_PASS source_locks={value['source_locks']} implementation_files={value['implementation_files']} target_qualification={value['target_qualification']}")
