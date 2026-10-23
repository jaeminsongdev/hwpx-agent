#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from tools.p08 import finalize_object_automation_v2_qualification as finalizer
except ModuleNotFoundError:
    import finalize_object_automation_v2_qualification as finalizer  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]


class ValidationError(ValueError):
    pass


def _validate_receipt(receipt: Any) -> None:
    if not isinstance(receipt, dict) or receipt.get("schema_version") \
            != finalizer.RECEIPT_SCHEMA:
        raise ValidationError("receipt_schema")
    if receipt.get("target") != finalizer.TARGET:
        raise ValidationError("receipt_target")
    summary = receipt.get("summary")
    if summary != {
        "p08_rows": 42,
        "direct_oracle_verified": 41,
        "target_capability_unavailable": 1,
        "automation_runtime_verified": 34,
        "automation_unavailable_with_reason": 8,
        "differential_exact_match": 34,
        "differential_not_applicable_fallback_unavailable": 7,
        "differential_not_applicable_target_unavailable": 1,
        "routing_enabled": 34,
        "p08_green_rows": 41,
        "p08_phase_gate": "pass_with_target_unavailable",
    }:
        raise ValidationError("receipt_summary")
    rows = receipt.get("rows")
    if not isinstance(rows, list) or len(rows) != 42:
        raise ValidationError("receipt_rows")
    ids = [row.get("feature_id") for row in rows if isinstance(row, dict)]
    expected = sorted(set(finalizer.VERIFIED_IDS) | set(finalizer.UNAVAILABLE_REASONS))
    if ids != expected:
        raise ValidationError("receipt_row_sequence")
    for row in rows:
        feature_id = row["feature_id"]
        runtime = row.get("automation_runtime", {})
        differential = row.get("differential", {})
        if feature_id in finalizer.VERIFIED_IDS:
            if runtime.get("state") != "verified_current_target" \
                    or runtime.get("semantic_effect_observed") is not True \
                    or runtime.get("document_save_count") != 0 \
                    or runtime.get("rollback_verified") is not True \
                    or differential.get("state") != "exact_match" \
                    or row.get("direct_oracle_basis_sha256") is None:
                raise ValidationError(f"verified_row:{feature_id}")
        elif feature_id == "OBJ-044":
            if runtime.get("state") != "target_capability_unavailable" \
                    or differential.get("state") \
                    != "not_applicable_target_capability_unavailable" \
                    or row.get("direct_oracle_basis_sha256") is not None:
                raise ValidationError("obj044_state")
        elif runtime.get("state") != "unavailable_with_reason" \
                or differential.get("state") != "not_applicable_fallback_unavailable" \
                or row.get("direct_oracle_basis_sha256") is None:
            raise ValidationError(f"unavailable_row:{feature_id}")
    if receipt.get("safety") != {
        "user_document_opened": False,
        "opened_files_scope": "project_owned_p08_20_readback_fixtures_only",
        "document_saved": False,
        "external_network_invoked": False,
        "registry_or_system_setting_changed": False,
        "computer_use_click_or_type_invoked": False,
        "remaining_owned_hwp_processes": 0,
    }:
        raise ValidationError("receipt_safety")
    serialized = finalizer.canonical_bytes(receipt).decode("utf-8")
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise ValidationError("private_path_leak")


def _validate_projection(projection: Any, receipt_sha256: str, overlay_sha256: str) -> None:
    if not isinstance(projection, dict) \
            or projection.get("schema_version") != finalizer.PROJECTION_SCHEMA \
            or projection.get("target_profile_id") != finalizer.TARGET["profile_id"]:
        raise ValidationError("projection_identity")
    if tuple(projection.get("verified_current_target", ())) != finalizer.VERIFIED_IDS \
            or projection.get("unavailable_with_reason") != finalizer.UNAVAILABLE_REASONS \
            or tuple(projection.get("candidate_unverified", ())) != finalizer.P11_CANDIDATES \
            or tuple(projection.get("denied_by_policy", ())) != finalizer.P11_DENIED \
            or tuple(projection.get("unbound_unavailable", ())) != finalizer.P11_UNAVAILABLE:
        raise ValidationError("projection_coverage")
    if projection.get("qualification_receipt_sha256") != receipt_sha256 \
            or projection.get("qualified_overlay_sha256") != overlay_sha256 \
            or projection.get("runtime_support_state") \
            != "partially_verified_current_target" \
            or projection.get("routing_enabled_count") != 34 \
            or projection.get("actual_target_profile") is not True \
            or projection.get("raw_action_identifiers") is not False \
            or projection.get("raw_parameter_identifiers") is not False:
        raise ValidationError("projection_state")


def validate(
    *,
    receipt_override: dict[str, Any] | None = None,
    projection_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        expected = finalizer.build_outputs(ROOT)
    except finalizer.QualificationError as error:
        raise ValidationError(str(error)) from error
    actual = {
        "receipt": receipt_override
        if receipt_override is not None
        else finalizer.load_json(finalizer.PUBLIC_RECEIPT, root=ROOT),
        "qualified_overlay": finalizer.load_json(finalizer.QUALIFIED_OVERLAY, root=ROOT),
        "projection": projection_override
        if projection_override is not None
        else finalizer.load_json(finalizer.PUBLIC_PROJECTION, root=ROOT),
        "contract": finalizer.load_json(finalizer.PUBLIC_CONTRACT, root=ROOT),
    }
    for key, value in actual.items():
        if value != expected[key]:
            raise ValidationError(f"deterministic_output_drift:{key}")
    _validate_receipt(actual["receipt"])
    receipt_sha256 = finalizer.digest_value(actual["receipt"])
    overlay_sha256 = finalizer.digest_value(actual["qualified_overlay"])
    _validate_projection(actual["projection"], receipt_sha256, overlay_sha256)
    contract = actual["contract"]
    if contract.get("phase_gate") != {
        "p08_supported_rows": 41,
        "p08_green_rows": 41,
        "p08_target_unavailable_rows": 1,
        "state": "pass_with_target_unavailable",
        "p11_rows_deferred": 16,
    }:
        raise ValidationError("contract_phase_gate")
    return {
        "schema_version": "hwpx-agent.p08-object-automation-v2-validation/v1",
        "state": "pass",
        "task": "P08-25",
        "target_profile_id": finalizer.TARGET["profile_id"],
        "p08_rows": 42,
        "automation_runtime_verified": 34,
        "automation_unavailable_with_reason": 8,
        "p08_green_rows": 41,
        "p08_phase_gate": "pass_with_target_unavailable",
    }


def main() -> int:
    try:
        result = validate()
    except (ValidationError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
