from __future__ import annotations

import json
from typing import Any

from build_object_automation_binding_overlay import (
    PUBLIC_CONTRACT,
    PUBLIC_PROJECTION,
    PRIVATE_REVIEW,
    ROOT,
    OverlayError,
    _canonical_bytes,
    _load,
    build_bundle,
)


def validate(review_override: dict[str, Any] | None = None) -> dict[str, Any]:
    contract, _overlay, projection = build_bundle(review_override=review_override)
    actual_contract, _ = _load(PUBLIC_CONTRACT, 2 * 1024 * 1024)
    if actual_contract != contract:
        raise OverlayError("public_contract_drift")
    # P08-22 owns the immutable source-candidate contract and v1 overlay. The
    # current public projection is intentionally superseded by P08-25 v2 and is
    # validated by validate_object_automation_v2_qualification.py.
    if contract["coverage"] != {
        "p08_rows": 42,
        "candidate_unverified": 40,
        "unavailable_with_reason": 2,
        "runtime_verified": 0,
        "routing_enabled": 0,
        "modal_risk_counts": {"none_expected": 14, "must_probe": 24, "known_modal": 2},
    }:
        raise OverlayError("coverage_drift")
    if len(contract["mappings"]) != 40 or [item["feature_id"] for item in contract["unavailable"]] != ["OBJ-044", "OBJ-046"]:
        raise OverlayError("mapping_or_unavailable_drift")
    if contract["not_claimed"] != {
        "runtime_qualification": False,
        "routing_support": False,
        "direct_automation_differential": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        raise OverlayError("claim_promotion")
    serialized = _canonical_bytes(contract).decode("utf-8")
    private_review, _ = _load(PRIVATE_REVIEW, 1024 * 1024)
    raw_names = {
        item["source_name"]
        for item in private_review["items"]
        if item["source_name"] is not None
    }
    if any(name in serialized for name in raw_names):
        raise OverlayError("raw_source_identifier_leak")
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise OverlayError("private_path_leak")
    return {
        "schema_version": "hwpx-agent.p08-object-automation-binding-overlay-validation/v1",
        "state": "pass",
        "task": "P08-22",
        "p08_rows": 42,
        "candidate_unverified": 40,
        "unavailable_with_reason": 2,
        "known_modal": 2,
        "must_probe": 24,
        "none_expected": 14,
        "runtime_verified": 0,
        "routing_enabled": 0,
        "differential": "not_run",
        "p08": "in_progress",
        "product_complete": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OverlayError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
