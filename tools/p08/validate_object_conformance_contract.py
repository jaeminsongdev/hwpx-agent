from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from object_conformance import (
    MATRIX,
    ROOT,
    TARGET,
    ConformanceError,
    build_matrix,
    canonical_bytes,
    load_json,
    normalized_sha256,
)


CONTRACT = Path("protocol/private/p08-object-conformance-v1.json")
QUALIFICATION = Path("implementation/p08/evidence/p08-09-object-conformance-source-qualification.v1.json")

EXPECTED_SOURCE_LOCKS = {
    "docs/04_feature_catalog/09_obj.md": "e3c4c71e8d8c608c8e403404c1cf7767bbd91bdfd93dbcdb07f2e91e90c785e8",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md": "e1274922109762ab3de1b7118e954510f37d1f0686b9b0c5fc1152936983bec2",
    "docs/08_testing/03_feature_conformance.md": "5ec281c468d266038ddbd6a8247ee092fadea7d0b5bd0fae966ebc53d243f24b",
    "docs/08_testing/05_layout_table_visual.md": "6534f39de2c37d95f0926aa74a61431be9a09813ff4b19fe84569979ab558740",
    "docs/12_implementation_guides/08_validation_oracle_visual_diff.md": "13bd9b84ddf0684fbb8892a6eaa14957af85e2d218c0f5cd438d57e71acdb426",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "specs/feature-coverage-matrix.json": "a3fa1cd5c5b0b0e09bc93354f724ed3516bdb987f1c171cc27d7564dc6390950",
    "specs/capability-contracts.generated.json": "b25b5300f605c7da4ed8552ef0f7405251582601f32a420f884cd91a256bb306",
    "specs/work-breakdown-structure.json": "56b5f9fe1279a15e7262d2dbb2c60c372f3bc9ad33acb418e1c905f2a731f2b2",
    "implementation/p08/p08-09-current-2020-direct-evidence.json": "3a8a0f3cd0fb96001aceaecbd5567d3c40369e348a1db14535727cfd2a7d0026",
    "implementation/p08/p08-09-current-2020-automation-projection.json": "f8c06f206c29eb7aa77b845fd1afa1ff09535145584f5f9fff83fdc679f1cd12",
    "implementation/p08/p08-09-threshold-policy.v1.json": "0f4856e81edc012ed80608fddea6a2be98286ca772127c5b1316f3e2ed890d0c",
    "implementation/p08/evidence/conformance/p08-object-conformance.current-2020.v1.json": "b467d8e87cd6455f57ddf1cb45ff645a8f6ec4c4cad49aa1931257d07b979e65",
    "tools/p08/object_conformance.py": "852c8f7ba1d34606de8cbaeb47062dd13a1085e3ca58cc0219f9856a410aded4",
}

EXPECTED_SUMMARY = {
    "required_rows": 58,
    "implementation_covered_rows": 53,
    "green_rows": 0,
    "non_green_rows": 58,
    "direct_stage_counts": {
        "cataloged": 5,
        "unit_passed": 19,
        "integration_passed": 34,
        "oracle_verified": 0,
    },
    "automation_binding_counts": {
        "candidate_unverified": 9,
        "denied_by_policy": 2,
        "unavailable_with_reason": 47,
    },
    "phase_counts": {"P08": 42, "P11": 16},
    "support_level_counts": {
        "HYBRID": 42,
        "AUTOMATION_FULL": 11,
        "OPTIONAL_EXTERNAL": 3,
        "PRESERVE_ONLY": 2,
    },
    "asset_threshold_required_rows": 44,
    "render_threshold_required_rows": 53,
    "render_threshold_calibrated_rows": 0,
    "differential_counts": {"not_run": 58},
    "required_matrix": "non_green",
}

EXPECTED_CLAIMS = {
    "matrix_implemented": True,
    "threshold_definitions_complete": True,
    "component_or_synthetic_rows": 53,
    "static_section_hwpx": True,
    "actual_hwpx": False,
    "actual_hangul": False,
    "save_reopen": False,
    "render": False,
    "automation": False,
    "differential": False,
    "p08_09_green": False,
    "p08_complete": False,
    "production_ready": False,
    "product_complete": False,
}

EXPECTED_PRIVACY = {
    "absolute_private_paths": False,
    "document_content": False,
    "raw_action_identifiers": False,
    "raw_parameter_identifiers": False,
    "raw_probe_values": False,
}

EXPECTED_UPSTREAM = [
    "tools/p08/validate_asset_pipeline_contract.py",
    "tools/p08/validate_image_hwpx_contract.py",
    "tools/p08/validate_object_geometry_contract.py",
    "tools/p08/validate_basic_shape_contract.py",
    "tools/p08/validate_object_appearance_contract.py",
    "tools/p08/validate_object_composition_contract.py",
    "tools/p08/validate_chart_automation_contract.py",
    "tools/p08/validate_drawing_canvas_contract.py",
    "tools/p08/validate_active_content_contract.py",
    "tools/p08/validate_object_remainder_contract.py",
    "tools/p08/validate_object_hwpx_integration_contract.py",
    "tools/p08/validate_freeform_hwpx_integration_contract.py",
    "tools/p08/validate_textbox_properties_hwpx_contract.py",
    "tools/p08/validate_object_protect_hwpx_contract.py",
    "tools/p08/validate_object_hyperlink_hwpx_contract.py",
]


def _exact_keys(value: dict[str, Any], keys: set[str], context: str) -> None:
    if set(value) != keys:
        raise ConformanceError(f"contract_shape:{context}")


def _validate_contract(contract: dict[str, Any]) -> None:
    _exact_keys(
        contract,
        {
            "schema_version",
            "scope",
            "target",
            "row_policy",
            "green_rule",
            "threshold_policy",
            "expected_current_summary",
            "source_lock_canonicalization",
            "source_locks",
            "upstream_contract_validators",
            "claims",
            "privacy",
        },
        "root",
    )
    if contract["schema_version"] != "hwpx-agent.p08-object-conformance-contract/v1":
        raise ConformanceError("contract_version")
    if contract["scope"] != "p08_09_current_pc_hancom_2020_fail_closed_matrix" or contract["target"] != TARGET:
        raise ConformanceError("contract_target")
    row_policy = contract["row_policy"]
    if not isinstance(row_policy, dict) or row_policy != {
        "feature_ids": "exactly_OBJ_001_through_OBJ_058_once_in_order",
        "all_rows_required": 58,
        "p08_rows": 42,
        "p11_deferred_rows": 16,
        "missing_direct_evidence": "cataloged_non_green",
        "missing_automation_binding": "non_green",
        "missing_differential": "non_green",
        "synthetic_or_component_evidence": "never_actual_target_or_release_green",
    }:
        raise ConformanceError("row_policy")
    expected_green = [
        "support_level_specific_oracle_verified",
        "all_contract_validations_passed",
        "all_required_fixture_classes_passed",
        "negative_passed",
        "rollback_or_retry_passed",
        "current_target_binding_and_runtime_verified_when_executable",
        "direct_automation_or_provider_differential_passed",
        "asset_threshold_passed_when_required",
        "target_render_threshold_calibrated_and_passed_when_required",
    ]
    if contract["green_rule"] != expected_green:
        raise ConformanceError("green_rule")
    threshold = contract["threshold_policy"]
    if not isinstance(threshold, dict) or threshold != {
        "path": "implementation/p08/p08-09-threshold-policy.v1.json",
        "asset_required_rows": 44,
        "render_required_rows": 53,
        "render_calibrated_rows": 0,
        "unchanged_region_changed_pixels_max": 0,
        "structural_mismatches_max": 0,
        "missing_glyphs_max": 0,
        "global_unbound_pixel_tolerance": "forbidden",
    }:
        raise ConformanceError("threshold_contract")
    if contract["expected_current_summary"] != EXPECTED_SUMMARY:
        raise ConformanceError("summary_contract")
    if contract["source_lock_canonicalization"] != "utf8_text_crlf_to_lf_sha256":
        raise ConformanceError("source_lock_mode")
    locks = contract["source_locks"]
    if not isinstance(locks, list) or any(not isinstance(lock, dict) or set(lock) != {"path", "sha256"} for lock in locks):
        raise ConformanceError("source_lock_shape")
    lock_map = {lock["path"]: lock["sha256"] for lock in locks}
    if len(lock_map) != len(locks) or lock_map != EXPECTED_SOURCE_LOCKS:
        raise ConformanceError("source_lock_set")
    for path, expected in EXPECTED_SOURCE_LOCKS.items():
        if normalized_sha256(Path(path)) != expected:
            raise ConformanceError(f"source_lock_drift:{path}")
    if contract["upstream_contract_validators"] != EXPECTED_UPSTREAM:
        raise ConformanceError("upstream_validator_set")
    if contract["claims"] != EXPECTED_CLAIMS:
        raise ConformanceError("claim_promotion")
    if contract["privacy"] != EXPECTED_PRIVACY:
        raise ConformanceError("privacy_contract")


def _validate_matrix(matrix: dict[str, Any]) -> None:
    expected = build_matrix()
    if matrix != expected or canonical_bytes(matrix) != (ROOT / MATRIX).read_bytes():
        raise ConformanceError("matrix_drift")
    if matrix["summary"] != EXPECTED_SUMMARY or matrix["privacy"] != EXPECTED_PRIVACY:
        raise ConformanceError("matrix_claim_drift")
    ids = [row["feature_id"] for row in matrix["rows"]]
    if ids != [f"OBJ-{number:03d}" for number in range(1, 59)]:
        raise ConformanceError("matrix_sequence")
    if any(row["gate_state"] != "non_green" or not row["blockers"] for row in matrix["rows"]):
        raise ConformanceError("matrix_false_green")
    serialized = canonical_bytes(matrix).decode("utf-8")
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise ConformanceError("private_path_leak")


def _validate_qualification(qualification: dict[str, Any]) -> None:
    _exact_keys(
        qualification,
        {"schema_version", "task", "base_commit", "scope", "source_sha256", "implementation_sha256", "claims"},
        "qualification",
    )
    if qualification["schema_version"] != "hwpx-agent.p08-object-conformance-source-qualification/v1" or qualification["task"] != "P08-09":
        raise ConformanceError("qualification_identity")
    if qualification["base_commit"] != "4bb130b" or qualification["scope"] != "current_pc_source_component_and_static_section_integration_evidence_only":
        raise ConformanceError("qualification_scope")
    expected_source_paths = list(EXPECTED_SOURCE_LOCKS)[:9]
    expected_source = {path: EXPECTED_SOURCE_LOCKS[path] for path in expected_source_paths}
    if qualification["source_sha256"] != expected_source:
        raise ConformanceError("qualification_source_set")
    implementation = qualification["implementation_sha256"]
    expected_implementation_paths = {
        "tools/p08/object_conformance.py",
        "tools/p08/validate_object_conformance_contract.py",
        "tools/p08/tests/test_object_conformance_contract.py",
        "implementation/p08/p08-09-current-2020-direct-evidence.json",
        "implementation/p08/p08-09-current-2020-automation-projection.json",
        "implementation/p08/p08-09-threshold-policy.v1.json",
        "implementation/p08/evidence/conformance/p08-object-conformance.current-2020.v1.json",
        "protocol/private/p08-object-conformance-v1.json",
        "protocol/migrations/p08-object-conformance-v0-to-v1.md",
        "implementation/p08/P08-09_OBJECT_CONFORMANCE_POLICY.md",
        "implementation/p08/P08-09_OBJECT_CONFORMANCE_REPORT.md",
    }
    if not isinstance(implementation, dict) or set(implementation) != expected_implementation_paths:
        raise ConformanceError("qualification_implementation_set")
    for path, expected in implementation.items():
        if normalized_sha256(Path(path)) != expected:
            raise ConformanceError(f"qualification_implementation_drift:{path}")
    if qualification["claims"] != {
        "source_qualification_only": True,
        "matrix_implemented": True,
        "required_rows": 58,
        "implementation_covered_rows": 53,
        "static_section_hwpx": True,
        "green_rows": 0,
        "actual_hwpx": False,
        "actual_hangul": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        raise ConformanceError("qualification_claim_promotion")


def _run_upstream() -> None:
    for validator in EXPECTED_UPSTREAM:
        result = subprocess.run(
            [sys.executable, validator],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            raise ConformanceError(f"upstream_failed:{validator}")
        payload = None
        for line in result.stdout.splitlines():
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                payload = candidate
        if payload is None:
            raise ConformanceError(f"upstream_output:{validator}")
        if payload.get("state") != "pass":
            raise ConformanceError(f"upstream_not_pass:{validator}")


def validate(
    *,
    contract_override: dict[str, Any] | None = None,
    matrix_override: dict[str, Any] | None = None,
    run_upstream: bool = True,
) -> dict[str, Any]:
    contract = contract_override if contract_override is not None else load_json(CONTRACT)
    matrix = matrix_override if matrix_override is not None else load_json(MATRIX)
    qualification = load_json(QUALIFICATION)
    if not isinstance(contract, dict) or not isinstance(matrix, dict) or not isinstance(qualification, dict):
        raise ConformanceError("document_shape")
    _validate_contract(contract)
    _validate_matrix(matrix)
    _validate_qualification(qualification)
    if run_upstream:
        _run_upstream()
    return {
        "schema_version": "hwpx-agent.p08-object-conformance-validation/v1",
        "state": "pass",
        "task": "P08-09",
        "target_profile_id": TARGET["profile_id"],
        "required_rows": 58,
        "implementation_covered_rows": 53,
        "green_rows": 0,
        "non_green_rows": 58,
        "direct_stage_counts": EXPECTED_SUMMARY["direct_stage_counts"],
        "asset_threshold_required_rows": 44,
        "render_threshold_required_rows": 53,
        "render_threshold_calibrated_rows": 0,
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p08": "in_progress",
        "product_complete": False,
    }


def main() -> int:
    try:
        result = validate()
    except (ConformanceError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
