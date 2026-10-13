from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from reference_conformance import (
    DEFERRED_P11,
    MATRIX,
    ROOT,
    TARGET,
    ConformanceError,
    build_matrix,
    canonical_bytes,
    load_json,
    normalized_sha256,
)


CONTRACT = Path("protocol/private/p09-reference-conformance-v1.json")
QUALIFICATION = Path(
    "implementation/p09/evidence/"
    "p09-11-reference-conformance-source-qualification.v1.json"
)

EXPECTED_SOURCE_LOCKS = {
    "docs/04_feature_catalog/10_ref.md": "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4",
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29",
    "docs/09_roadmap/P09_fields_forms_notes_references.md": "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55",
    "specs/feature-coverage-matrix.json": "a3fa1cd5c5b0b0e09bc93354f724ed3516bdb987f1c171cc27d7564dc6390950",
    "specs/capability-contracts.generated.json": "b25b5300f605c7da4ed8552ef0f7405251582601f32a420f884cd91a256bb306",
    "specs/work-breakdown-structure.json": "56b5f9fe1279a15e7262d2dbb2c60c372f3bc9ad33acb418e1c905f2a731f2b2",
    "tools/p09/reference_conformance.py": "a6a560618a4019d506c1b2b25bd17e8ea7c52998176fff831693b3f66e517208",
    "implementation/p09/evidence/conformance/p09-reference-conformance.current-2020.v1.json": "1ac344338c2e1728706e81f72590b4a6ffaee68194c0b1e669ad5190242f36d1",
}

EXPECTED_SUMMARY = {
    "required_rows": 53,
    "p09_owned_rows": 46,
    "p11_deferred_rows": 7,
    "component_covered_rows": 46,
    "component_stage_counts": {
        "cataloged": 7,
        "unit_passed": 35,
        "integration_passed": 11,
        "oracle_verified": 0,
    },
    "direct_hwpx_implemented_rows": 11,
    "actual_hwpx_rows": 0,
    "actual_hangul_rows": 0,
    "render_verified_rows": 0,
    "automation_verified_rows": 0,
    "differential_passed_rows": 0,
    "green_rows": 0,
    "non_green_rows": 53,
    "required_matrix": "non_green",
}

EXPECTED_CLAIMS = {
    "matrix_implemented": True,
    "component_inventory_complete_for_p09_owned_rows": True,
    "component_or_synthetic_rows": 46,
    "direct_hwpx": False,
    "actual_hwpx": False,
    "actual_hangul": False,
    "semantic_reopen": False,
    "field_readback": False,
    "reference_update": False,
    "hancom_open": False,
    "render": False,
    "automation": False,
    "differential": False,
    "p09_complete": False,
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
    "tools/p09/validate_field_core_contract.py",
    "tools/p09/validate_form_control_contract.py",
    "tools/p09/validate_note_engine_contract.py",
    "tools/p09/validate_comment_model_contract.py",
    "tools/p09/validate_link_reference_contract.py",
    "tools/p09/validate_cross_reference_contract.py",
    "tools/p09/validate_toc_index_contract.py",
    "tools/p09/validate_citation_contract.py",
    "tools/p09/validate_mail_merge_contract.py",
    "tools/p09/validate_reference_auxiliary_contract.py",
    "tools/p09/validate_form_control_hwpx_contract.py",
    "tools/p09/validate_bookmark_hwpx_contract.py",
    "tools/p09/validate_note_hwpx_contract.py",
    "tools/p09/validate_hyperlink_hwpx_contract.py",
    "tools/p09/validate_field_auto_number_hwpx_contract.py",
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
            "expected_current_summary",
            "source_lock_canonicalization",
            "source_locks",
            "upstream_contract_validators",
            "claims",
            "privacy",
        },
        "root",
    )
    if contract["schema_version"] != "hwpx-agent.p09-reference-conformance-contract/v1":
        raise ConformanceError("contract_version")
    if (
        contract["scope"]
        != "p09_11_current_pc_component_inventory_and_fail_closed_matrix"
        or contract["target"] != TARGET
    ):
        raise ConformanceError("contract_target")
    expected_row_policy = {
        "feature_ids": "exactly_REF_001_through_REF_053_once_in_order",
        "all_rows_required": 53,
        "p09_owned_rows": 46,
        "p11_deferred_rows": 7,
        "p11_deferred_feature_ids": sorted(DEFERRED_P11),
        "component_or_synthetic_evidence": "never_actual_target_or_release_green",
        "missing_direct_evidence": "not_run_non_green",
        "missing_automation_binding": "not_run_non_green",
        "missing_differential": "not_run_non_green",
    }
    if contract["row_policy"] != expected_row_policy:
        raise ConformanceError("row_policy")
    expected_green = [
        "support_specific_backend_oracle_verified",
        "all_contract_validations_passed",
        "all_required_fixture_classes_passed",
        "negative_passed",
        "rollback_or_retry_passed",
        "current_target_runtime_and_readback_verified_when_required",
        "render_threshold_calibrated_and_passed_when_required",
        "direct_automation_differential_passed",
    ]
    if contract["green_rule"] != expected_green:
        raise ConformanceError("green_rule")
    if contract["expected_current_summary"] != EXPECTED_SUMMARY:
        raise ConformanceError("summary_contract")
    if contract["source_lock_canonicalization"] != "utf8_text_crlf_to_lf_sha256":
        raise ConformanceError("source_lock_mode")
    locks = contract["source_locks"]
    if (
        not isinstance(locks, list)
        or any(
            not isinstance(lock, dict) or set(lock) != {"path", "sha256"}
            for lock in locks
        )
    ):
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
    if [row["feature_id"] for row in matrix["rows"]] != [
        f"REF-{number:03d}" for number in range(1, 54)
    ]:
        raise ConformanceError("matrix_sequence")
    if any(row["gate_state"] != "non_green" or not row["blockers"] for row in matrix["rows"]):
        raise ConformanceError("matrix_false_green")
    expected_static = {
        "REF-018",
        "REF-019",
        "REF-021",
        "REF-022",
        "REF-031",
        "REF-032",
        "REF-033",
        "REF-034",
        "REF-006",
        "REF-008",
        "REF-009",
    }
    if any(
        row["direct_hwpx"]["implementation_state"]
        != (
            "static_section_integration_passed"
            if row["feature_id"] in expected_static
            else "not_run"
        )
        or row["differential_state"] != "not_run"
        for row in matrix["rows"]
    ):
        raise ConformanceError("matrix_target_promotion")
    serialized = canonical_bytes(matrix).decode("utf-8")
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise ConformanceError("private_path_leak")


def _validate_qualification(qualification: dict[str, Any]) -> None:
    _exact_keys(
        qualification,
        {
            "schema_version",
            "task",
            "base_commit",
            "scope",
            "source_sha256",
            "implementation_sha256",
            "claims",
        },
        "qualification",
    )
    if (
        qualification["schema_version"]
        != "hwpx-agent.p09-reference-conformance-source-qualification/v1"
        or qualification["task"] != "P09-11"
        or qualification["base_commit"] != "5a1a178"
        or qualification["scope"]
        != "current_pc_component_inventory_and_phase_ownership_only"
    ):
        raise ConformanceError("qualification_identity")
    source_paths = list(EXPECTED_SOURCE_LOCKS)[:6]
    if qualification["source_sha256"] != {
        path: EXPECTED_SOURCE_LOCKS[path] for path in source_paths
    }:
        raise ConformanceError("qualification_source_set")
    expected_implementation_paths = {
        "tools/p09/reference_conformance.py",
        "tools/p09/validate_reference_conformance_contract.py",
        "tools/p09/tests/test_reference_conformance_contract.py",
        "implementation/p09/evidence/conformance/p09-reference-conformance.current-2020.v1.json",
        "protocol/private/p09-reference-conformance-v1.json",
        "protocol/migrations/p09-reference-conformance-v0-to-v1.md",
        "implementation/p09/P09-11_REFERENCE_CONFORMANCE_POLICY.md",
        "implementation/p09/P09-11_REFERENCE_CONFORMANCE_REPORT.md",
    }
    implementation = qualification["implementation_sha256"]
    if not isinstance(implementation, dict) or set(implementation) != expected_implementation_paths:
        raise ConformanceError("qualification_implementation_set")
    for path, expected in implementation.items():
        if normalized_sha256(Path(path)) != expected:
            raise ConformanceError(f"qualification_implementation_drift:{path}")
    expected_claims = {
        "source_qualification_only": True,
        "matrix_implemented": True,
        "required_rows": 53,
        "p09_owned_rows": 46,
        "p11_deferred_rows": 7,
        "component_covered_rows": 46,
        "green_rows": 0,
        "direct_hwpx": False,
        "actual_hwpx": False,
        "actual_hangul": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p09_complete": False,
        "production_ready": False,
        "product_complete": False,
    }
    if qualification["claims"] != expected_claims:
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
        if payload is None or payload.get("state") != "pass":
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
        "schema_version": "hwpx-agent.p09-reference-conformance-validation/v1",
        "state": "pass",
        "task": "P09-11",
        "target_profile_id": TARGET["profile_id"],
        "required_rows": 53,
        "p09_owned_rows": 46,
        "p11_deferred_rows": 7,
        "component_covered_rows": 46,
        "component_stage_counts": EXPECTED_SUMMARY["component_stage_counts"],
        "green_rows": 0,
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09": "in_progress",
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
