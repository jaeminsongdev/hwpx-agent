from __future__ import annotations

import argparse
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
QUALIFICATION = Path(
    "implementation/p08/evidence/p08-09-object-conformance-source-qualification.v1.json"
)
SOURCE_PATHS = (
    "docs/04_feature_catalog/09_obj.md",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md",
    "docs/08_testing/03_feature_conformance.md",
    "docs/08_testing/05_layout_table_visual.md",
    "docs/12_implementation_guides/08_validation_oracle_visual_diff.md",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md",
    "specs/feature-coverage-matrix.json",
    "specs/capability-contracts.generated.json",
    "specs/work-breakdown-structure.json",
)
IMPLEMENTATION_PATHS = (
    "implementation/p08/p08-09-current-2020-direct-evidence.json",
    "implementation/p08/p08-09-current-2020-automation-projection.json",
    "implementation/p08/p08-09-threshold-policy.v1.json",
    "implementation/p08/evidence/conformance/p08-object-conformance.current-2020.v1.json",
    "tools/p08/object_conformance.py",
    "tools/p08/tests/test_object_conformance_contract.py",
    "implementation/p08/evidence/p08-20-object-target-qualification.current-2020.v1.json",
    "implementation/p08/evidence/p08-21-aspect-lock-negative-qualification.current-2020.v1.json",
    "implementation/p08/evidence/p08-24-object-shape-canary.current-2020.v1.json",
    "implementation/p02/evidence/bindings/p08-object-automation-binding-overlay.2020.v1.json",
    "implementation/p02/evidence/bindings/p08-object-automation-binding-overlay.2020.v2.qualified.json",
    "implementation/p08/evidence/p08-25-object-automation-v2-qualification.current-2020.v1.json",
    "protocol/private/p08-object-automation-v2-qualification-v1.json",
    "tools/p08/finalize_object_automation_v2_qualification.py",
    "tools/p08/validate_object_automation_v2_qualification.py",
    "tools/p08/tests/test_object_automation_v2_qualification.py",
    "crates/hwpx-package/tests/object_common_properties_hwpx.rs",
    "tools/p08/tests/test_object_target_oracle.py",
    "implementation/p08/P08-09_OBJECT_CONFORMANCE_POLICY.md",
    "implementation/p08/P08-09_OBJECT_CONFORMANCE_REPORT.md",
    "implementation/p08/P08-25_OBJECT_AUTOMATION_V2_POLICY.md",
    "implementation/p08/P08-25_OBJECT_AUTOMATION_V2_REPORT.md",
)

# Replaced only through an explicit source-lock refresh after the complete validator suite passes.
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
    "implementation/p08/p08-09-current-2020-direct-evidence.json": "180a435145dd8c748247215bee25ce120afc43a1c4341558bc97b1a71dae21cb",
    "implementation/p08/p08-09-current-2020-automation-projection.json": "6fd0970efb15fd60242f4195116f640c81b4a1f5c959be5e46bc116c81bdd4a8",
    "implementation/p08/p08-09-threshold-policy.v1.json": "023578823ebc1884042f55f881d876cf16a9fad0e596eea2d1e7cf8eaf75ae62",
    "implementation/p08/evidence/conformance/p08-object-conformance.current-2020.v1.json": "d9fd4ca435f556e798d435f960d30c9a6151a5bbc5c0798076dee6bf836ddaba",
    "tools/p08/object_conformance.py": "8f086eab46ee23dfaa34038c90b42b0164302fa9fecf9620b0268df26af74227",
    "tools/p08/tests/test_object_conformance_contract.py": "540a670cceb76cb56817651eb8ae0bdf6d42fa244b3041c5c1592c58b4467e4f",
    "implementation/p08/evidence/p08-20-object-target-qualification.current-2020.v1.json": "2043c20e403ec02dd6a7ec66a013cfab2fbb4663d2eb9324d8fed51547001011",
    "implementation/p08/evidence/p08-21-aspect-lock-negative-qualification.current-2020.v1.json": "32786401698aab8f5defb2a348c5f6407eae7b5313dd2668e2f2a4f8374ad0b9",
    "implementation/p08/evidence/p08-24-object-shape-canary.current-2020.v1.json": "46a0d154a807d807c9653e1d42b25796254806e088f12966c8476c09dd43ef3c",
    "implementation/p02/evidence/bindings/p08-object-automation-binding-overlay.2020.v1.json": "8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f",
    "implementation/p02/evidence/bindings/p08-object-automation-binding-overlay.2020.v2.qualified.json": "8df22939d7a5b821855dd7bb1223e42c3f81bdac81c1a0b37308a43449cff5b8",
    "implementation/p08/evidence/p08-25-object-automation-v2-qualification.current-2020.v1.json": "61fd27e435782aa321172fa654ec1988626a8ba0d466f4fadb853795e4bd1520",
    "protocol/private/p08-object-automation-v2-qualification-v1.json": "aeaa942fe79562fd3b5dfdf50f359671a8d0c53871a75bf21b39472beae63b2d",
    "tools/p08/finalize_object_automation_v2_qualification.py": "d9676bba05672da5a426692679423d7405687ed5de6265cfb0f17fade097b5e0",
    "tools/p08/validate_object_automation_v2_qualification.py": "44e12e706eb29f56cf7a54166d88c64116b34bf9c411dd6d147f57c8cd943955",
    "tools/p08/tests/test_object_automation_v2_qualification.py": "8db6926c36027eabf98804bd07131d19da687ded4993061e91713ac24e1e672e",
    "crates/hwpx-package/tests/object_common_properties_hwpx.rs": "94c2a449c151214c50778b752fe59c92e2b28e5748ed692d4f08feb4c465d956",
    "tools/p08/tests/test_object_target_oracle.py": "da1bbc42abd6b5d9344769d00ed27b802c26e9768e2b94dd5a61ec270b350714",
    "implementation/p08/P08-09_OBJECT_CONFORMANCE_POLICY.md": "55c49e9f03fb854d97e980f9eb5a4591f1e5d29b02b64c5f91b9f446fdcf17fe",
    "implementation/p08/P08-09_OBJECT_CONFORMANCE_REPORT.md": "1c084b9b12e5bd586988f60674d71f8a2b9d2bf6aa8864ebaabe302796ae9cf7",
    "implementation/p08/P08-25_OBJECT_AUTOMATION_V2_POLICY.md": "8777be63b660bfabbfd1cecfb384d39af460bd2395404c7b2509e28f754752b7",
    "implementation/p08/P08-25_OBJECT_AUTOMATION_V2_REPORT.md": "92a55f58183de77e98b6192e7aa4168037b9bb29a91ca5db0784d23c22f23390",
}

EXPECTED_SUMMARY = {
    "required_rows": 58,
    "implementation_covered_rows": 53,
    "green_rows": 41,
    "non_green_rows": 17,
    "direct_stage_counts": {
        "cataloged": 5,
        "unit_passed": 10,
        "integration_passed": 2,
        "oracle_verified": 41,
    },
    "automation_binding_counts": {
        "verified_current_target": 34,
        "candidate_unverified": 9,
        "denied_by_policy": 2,
        "unavailable_with_reason": 13,
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
    "render_threshold_calibrated_rows": 41,
    "differential_counts": {
        "exact_match": 34,
        "not_applicable_fallback_unavailable": 7,
        "not_applicable_target_capability_unavailable": 1,
        "not_run": 16,
    },
    "p08_supported_rows": 41,
    "p08_green_rows": 41,
    "p08_target_unavailable_rows": 1,
    "p08_phase_gate": "pass_with_target_unavailable",
    "p11_green_rows": 0,
    "p11_phase_gate": "deferred",
    "required_matrix": "deferred_p11_non_green",
}

EXPECTED_CLAIMS = {
    "matrix_implemented": True,
    "threshold_definitions_complete": True,
    "component_or_synthetic_rows": 12,
    "target_oracle_rows": 41,
    "static_section_hwpx": True,
    "actual_hwpx": True,
    "actual_hangul": True,
    "save_reopen": True,
    "render": True,
    "obj044_exact_target_unavailable": True,
    "object_automation_source_candidates": 40,
    "object_automation_surface_present": 38,
    "object_automation_runtime_verified": 34,
    "object_automation_unavailable_with_reason": 8,
    "object_automation_routing_enabled": 34,
    "differential_exact_match": 34,
    "differential_not_applicable": 8,
    "p08_green_rows": 41,
    "p08_phase_gate": "pass_with_target_unavailable",
    "p08_09_green": True,
    "p08_complete_current_pc": True,
    "p11_complete": False,
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
    "tools/p08/validate_object_hyperlink_target_route_contract.py",
    "tools/p08/validate_object_remainder_hwpx_contract.py",
    "tools/p08/validate_object_target_qualification.py",
    "tools/p08/validate_aspect_lock_negative_qualification.py",
    "tools/p08/validate_object_automation_binding_overlay.py",
    "tools/p08/validate_object_surface_qualification.py",
    "tools/p08/validate_object_shape_canary_qualification.py",
    "tools/p08/validate_object_automation_v2_qualification.py",
]


def _exact_keys(value: dict[str, Any], keys: set[str], context: str) -> None:
    if set(value) != keys:
        raise ConformanceError(f"contract_shape:{context}")


def _expected_contract() -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p08-object-conformance-contract/v1",
        "scope": "p08_current_pc_phase_gate_with_p11_deferred",
        "target": TARGET,
        "row_policy": {
            "feature_ids": "exactly_OBJ_001_through_OBJ_058_once_in_order",
            "all_rows_required": 58,
            "p08_rows": 42,
            "p08_supported_rows": 41,
            "p08_target_unavailable_rows": 1,
            "p11_deferred_rows": 16,
            "preferred_direct_oracle_required_for_supported_p08": True,
            "unavailable_fallback_must_be_disabled": True,
            "p11_promotion_forbidden": True,
        },
        "green_rule": [
            "preferred_direct_oracle_verified",
            "all_contract_validations_passed",
            "all_required_fixture_classes_passed",
            "negative_passed",
            "rollback_or_retry_passed",
            "verified_fallback_requires_runtime_route_and_exact_semantic_contract_differential",
            "unavailable_fallback_requires_exact_reason_disabled_route_and_not_applicable_differential",
            "target_capability_unavailable_never_green",
            "asset_threshold_passed_when_required",
            "target_render_threshold_calibrated_and_passed_when_required",
        ],
        "threshold_policy": {
            "path": "implementation/p08/p08-09-threshold-policy.v1.json",
            "asset_required_rows": 44,
            "render_required_rows": 53,
            "render_calibrated_rows": 41,
            "unchanged_region_changed_pixels_max": 0,
            "structural_mismatches_max": 0,
            "missing_glyphs_max": 0,
            "global_unbound_pixel_tolerance": "forbidden",
        },
        "expected_current_summary": EXPECTED_SUMMARY,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_locks": [
            {"path": path, "sha256": EXPECTED_SOURCE_LOCKS[path]}
            for path in (*SOURCE_PATHS, *IMPLEMENTATION_PATHS)
        ],
        "upstream_contract_validators": EXPECTED_UPSTREAM,
        "claims": EXPECTED_CLAIMS,
        "privacy": EXPECTED_PRIVACY,
    }


def _expected_qualification() -> dict[str, Any]:
    validator_path = Path("tools/p08/validate_object_conformance_contract.py")
    implementation = {
        path: EXPECTED_SOURCE_LOCKS[path] for path in IMPLEMENTATION_PATHS
    }
    implementation[validator_path.as_posix()] = normalized_sha256(validator_path)
    return {
        "schema_version": "hwpx-agent.p08-object-conformance-source-qualification/v1",
        "task": "P08-09",
        "base_commit": "4bb130b",
        "scope": "current_pc_p08_41_green_one_target_unavailable_p11_deferred",
        "source_sha256": {path: EXPECTED_SOURCE_LOCKS[path] for path in SOURCE_PATHS},
        "implementation_sha256": implementation,
        "claims": {
            "source_qualification_only": True,
            **EXPECTED_CLAIMS,
            "required_rows": 58,
            "implementation_covered_rows": 53,
            "green_rows": 41,
        },
    }


def _validate_contract(contract: dict[str, Any]) -> None:
    expected = _expected_contract()
    if contract != expected:
        raise ConformanceError("contract_drift")
    if any(value == "TO_FILL" for value in EXPECTED_SOURCE_LOCKS.values()):
        raise ConformanceError("source_locks_not_finalized")
    for path, expected_sha256 in EXPECTED_SOURCE_LOCKS.items():
        if normalized_sha256(Path(path)) != expected_sha256:
            raise ConformanceError(f"source_lock_drift:{path}")


def _validate_matrix(matrix: dict[str, Any]) -> None:
    expected = build_matrix()
    if matrix != expected or canonical_bytes(matrix) != (ROOT / MATRIX).read_bytes():
        raise ConformanceError("matrix_drift")
    if matrix["summary"] != EXPECTED_SUMMARY or matrix["privacy"] != EXPECTED_PRIVACY:
        raise ConformanceError("matrix_claim_drift")
    ids = [row["feature_id"] for row in matrix["rows"]]
    if ids != [f"OBJ-{number:03d}" for number in range(1, 59)]:
        raise ConformanceError("matrix_sequence")
    p08 = [row for row in matrix["rows"] if row["catalog_phase"] == "P08"]
    p11 = [row for row in matrix["rows"] if row["catalog_phase"] == "P11"]
    green_ids = {row["feature_id"] for row in p08 if row["gate_state"] == "green"}
    expected_green = {
        feature_id for feature_id in ids
        if feature_id not in {"OBJ-004", "OBJ-005", "OBJ-006", "OBJ-008", "OBJ-009",
                              "OBJ-011", "OBJ-044", "OBJ-049", "OBJ-050", "OBJ-051",
                              "OBJ-052", "OBJ-053", "OBJ-054", "OBJ-055", "OBJ-056",
                              "OBJ-057", "OBJ-058"}
    }
    if green_ids != expected_green or len(p08) != 42 or len(green_ids) != 41:
        raise ConformanceError("p08_green_set")
    obj044 = next(row for row in p08 if row["feature_id"] == "OBJ-044")
    if obj044["gate_state"] != "non_green" \
            or obj044["phase_acceptance"] != "target_unavailable_accepted" \
            or "target_capability_unavailable" not in obj044["blockers"]:
        raise ConformanceError("obj044_false_promotion")
    if any(row["gate_state"] != "non_green" or row["phase_acceptance"] != "deferred" for row in p11):
        raise ConformanceError("p11_false_promotion")
    obj046 = next(row for row in p08 if row["feature_id"] == "OBJ-046")
    if "security" not in obj046["direct"]["fixture_classes_passed"] \
            or obj046["automation"]["routing_enabled"] is not False:
        raise ConformanceError("obj046_security_or_route")
    serialized = canonical_bytes(matrix).decode("utf-8")
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise ConformanceError("private_path_leak")


def _validate_qualification(qualification: dict[str, Any]) -> None:
    if qualification != _expected_qualification():
        raise ConformanceError("qualification_drift")
    for path, expected_sha256 in qualification["implementation_sha256"].items():
        if normalized_sha256(Path(path)) != expected_sha256:
            raise ConformanceError(f"qualification_implementation_drift:{path}")


def _run_upstream() -> None:
    for validator in EXPECTED_UPSTREAM:
        result = subprocess.run(
            [sys.executable, validator],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45,
            check=False,
        )
        if result.returncode != 0:
            raise ConformanceError(f"upstream_failed:{validator}:{result.stdout[-300:]}")
        payload = None
        for line in result.stdout.splitlines():
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                payload = candidate
        if payload is None or payload.get("state") != "pass":
            raise ConformanceError(f"upstream_not_pass:{validator}")


def _write_authorities() -> None:
    contract_path = ROOT / CONTRACT
    qualification_path = ROOT / QUALIFICATION
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    qualification_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_bytes(canonical_bytes(_expected_contract()))
    qualification_path.write_bytes(canonical_bytes(_expected_qualification()))


def validate(
    *,
    contract_override: dict[str, Any] | None = None,
    matrix_override: dict[str, Any] | None = None,
    run_upstream: bool = True,
) -> dict[str, Any]:
    contract = contract_override if contract_override is not None else load_json(CONTRACT)
    matrix = matrix_override if matrix_override is not None else load_json(MATRIX)
    qualification = load_json(QUALIFICATION)
    if not isinstance(contract, dict) or not isinstance(matrix, dict) \
            or not isinstance(qualification, dict):
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
        "green_rows": 41,
        "non_green_rows": 17,
        "direct_stage_counts": EXPECTED_SUMMARY["direct_stage_counts"],
        "asset_threshold_required_rows": 44,
        "render_threshold_required_rows": 53,
        "render_threshold_calibrated_rows": 41,
        "actual_hwpx": "pass",
        "actual_hangul": "pass",
        "save_reopen": "pass",
        "render": "pass",
        "obj044": "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        "automation": "34_verified_8_unavailable",
        "differential": "34_exact_8_not_applicable",
        "p08": "pass_with_target_unavailable",
        "p11": "deferred",
        "product_complete": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the P08 object conformance authority")
    parser.add_argument("--write-authorities", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write_authorities:
            _write_authorities()
            print(json.dumps({"state": "written", "task": "P08-09"}, sort_keys=True))
            return 0
        result = validate()
    except (ConformanceError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
