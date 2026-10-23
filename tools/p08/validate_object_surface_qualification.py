from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-23-object-surface.current-2020.v1.json"
)
WRAPPER = Path("implementation/p08/tools/run-hancom-2020-object-surface-batch.ps1")
CHILD = Path("implementation/p08/tools/run-hancom-2020-object-surface-batch-child.ps1")
DIGEST = re.compile(r"[0-9a-f]{64}")
EXPECTED_IDENTITIES = {
    "binding_overlay_sha256": "8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f",
    "binding_public_contract_sha256": "9a01ba026c858c9ebdad9bbe1762b74295a112faed028aba47906567bc53c52d",
    "fixture_manifest_sha256": "2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b",
    "progress_sha256": "7fb85250d3384a02f97e3513d16f5b69461245824c6a906152c245b4140b2dfe",
    "private_trace_sha256": "9fe392bcdcbcc67538f8c22de138ed361f8c835d21a7e27cd29d90958ecbc42e",
    "runtime_receipt_sha256": "61a700e7d7cd8789aa5f4b7e6a4c24c3d004071ac743a58e5cd8888503eb50bc",
    "wrapper_sha256": "e92532c70aba40575bea5f46c65266e79bd5cd0f08fbe92c6d902d70a22bcf71",
    "child_sha256": "13d4c73b1256a900ed3664de72c69c6ca2585de99518f96a673a633e6d3e0be4",
}


class QualificationError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise QualificationError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load(path: Path = QUALIFICATION, *, root: Path = ROOT) -> dict[str, Any]:
    data = (root / path).read_bytes()
    if not data or len(data) > 1024 * 1024:
        raise QualificationError("qualification_size")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError("qualification_json") from error
    if not isinstance(value, dict):
        raise QualificationError("qualification_shape")
    return value


def _sha256(path: Path, *, root: Path = ROOT) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def _exact_keys(value: Any, keys: set[str], context: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise QualificationError(f"shape_drift:{context}")


def validate(
    qualification_override: dict[str, Any] | None = None,
    *,
    verify_source_hashes: bool = True,
) -> dict[str, Any]:
    value = qualification_override if qualification_override is not None else load()
    _exact_keys(
        value,
        {
            "schema_version", "task", "recorded_date", "attempt_id", "state",
            "target", "identities", "execution", "predecessor_attempts", "cases",
            "boundaries", "claims", "privacy",
        },
        "root",
    )
    if (
        value["schema_version"] != "hwpx-agent.p08-object-surface-qualification/v1"
        or value["task"] != "P08-23"
        or value["recorded_date"] != "2026-09-15"
        or value["attempt_id"] != "p08-23-object-surface-20260915-06"
        or value["state"] != "pass"
    ):
        raise QualificationError("identity")
    if value["target"] != {
        "product": "Hancom Hangul 2020",
        "build": "11.0.0.9136",
        "architecture": "x86",
        "locale": "ko-KR",
        "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
    }:
        raise QualificationError("target")
    if value["identities"] != EXPECTED_IDENTITIES or any(
        DIGEST.fullmatch(item) is None for item in value["identities"].values()
    ):
        raise QualificationError("identities")
    if verify_source_hashes:
        if _sha256(WRAPPER) != EXPECTED_IDENTITIES["wrapper_sha256"]:
            raise QualificationError("source_drift:wrapper")
        if _sha256(CHILD) != EXPECTED_IDENTITIES["child_sha256"]:
            raise QualificationError("source_drift:child")
        child_text = (ROOT / CHILD).read_text(encoding="utf-8")
        if "$document.Open(" in child_text or ".Save" in child_text:
            raise QualificationError("hwp_file_io_source_boundary")
    if value["execution"] != {
        "candidate_count": 40,
        "probed_case_count": 38,
        "excluded_known_modal": ["OBJ-003", "OBJ-043"],
        "surface_present_count": 38,
        "action_created_count": 37,
        "method_present_count": 1,
        "enabled_in_blank_context_count": 10,
        "disabled_in_blank_context_count": 27,
        "set_created_count": 21,
        "get_default_passed_count": 10,
        "get_default_returned_false_count": 11,
        "get_default_not_applicable_count": 17,
        "action_execute_count": 0,
        "hwp_file_open_count": 0,
        "document_save_count": 0,
        "remaining_owned_hwp_processes": 0,
        "timed_out": False,
        "stalled": False,
    }:
        raise QualificationError("execution")
    if value["predecessor_attempts"] != [
        {"attempt_id": "p08-23-object-surface-20260915-01", "state": "failed"},
        {"attempt_id": "p08-23-object-surface-20260915-02", "state": "failed"},
        {"attempt_id": "p08-23-object-surface-20260915-03", "state": "failed"},
        {"attempt_id": "p08-23-object-surface-20260915-04", "state": "superseded_pass"},
        {"attempt_id": "p08-23-object-surface-20260915-05", "state": "superseded_pass"},
    ]:
        raise QualificationError("predecessor_attempts")
    cases = value["cases"]
    if not isinstance(cases, list) or len(cases) != 38:
        raise QualificationError("cases")
    feature_ids = [item.get("feature_id") for item in cases]
    if feature_ids != sorted(feature_ids) or len(set(feature_ids)) != 38:
        raise QualificationError("case_features")
    case_keys = {
        "feature_id", "capability_id", "surface_kind", "source_identifier_sha256",
        "modal_risk", "context", "surface_state", "is_action_enable",
        "action_created", "set_created", "get_default_state", "method_present",
    }
    for item in cases:
        _exact_keys(item, case_keys, f"case:{item.get('feature_id')}")
        if DIGEST.fullmatch(item["source_identifier_sha256"]) is None:
            raise QualificationError("case_identifier")
        if item["context"] != "one_shared_blank_disposable_document":
            raise QualificationError("case_context")
        if item["surface_kind"] == "automation_object":
            if (
                item["surface_state"] != "surface_present_method_not_invoked"
                or item["method_present"] is not True
            ):
                raise QualificationError("method_case")
        elif (
            item["surface_kind"] != "action_table"
            or item["action_created"] is not True
            or item["surface_state"] not in {
                "surface_present_enabled",
                "surface_present_disabled_in_blank_context",
            }
        ):
            raise QualificationError("action_case")
    if value["boundaries"] != {
        "one_shared_blank_disposable_document": True,
        "known_modal_executed": False,
        "candidate_action_executed": False,
        "automation_method_invoked": False,
        "fixture_or_user_document_opened_by_hwp": False,
        "document_saved": False,
        "effect_observed": False,
        "undo_verified": False,
        "differential_run": False,
    }:
        raise QualificationError("boundaries")
    if value["claims"] != {
        "exact_target_surface_inventory": True,
        "source_candidate_binding": True,
        "automation_runtime_support": False,
        "routing_enabled": False,
        "differential": False,
        "required_matrix_green": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        raise QualificationError("claims")
    if value["privacy"] != {
        "absolute_private_paths_present": False,
        "raw_action_identifiers_present": False,
        "raw_parameter_identifiers_present": False,
        "document_content_present": False,
        "user_document_scanned": False,
        "external_network_invoked": False,
        "registry_or_system_setting_changed": False,
        "computer_use_click_or_type_invoked": False,
    }:
        raise QualificationError("privacy")
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise QualificationError("private_path_leak")
    for raw in (
        "DrawObjCreatorRectangle", "InsertPicture(Method)", "ShapeObjDialog",
        "ShapeObjFillProperty", "DrawObjEditDetail",
    ):
        if raw in serialized:
            raise QualificationError("raw_identifier_leak")
    return {
        "schema_version": "hwpx-agent.p08-object-surface-qualification-validation/v1",
        "state": "pass",
        "task": "P08-23",
        "attempt_id": value["attempt_id"],
        "surface_present_count": 38,
        "excluded_known_modal_count": 2,
        "action_execute_count": 0,
        "hwp_file_open_count": 0,
        "document_save_count": 0,
        "automation_runtime": "not_run",
        "differential": "not_run",
        "p08": "in_progress",
        "product_complete": False,
    }


def main() -> int:
    try:
        result = validate()
    except (QualificationError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

