from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-24-object-shape-canary.current-2020.v1.json"
)
WRAPPER = Path("implementation/p08/tools/run-hancom-2020-object-shape-canary.ps1")
CHILD = Path("implementation/p08/tools/run-hancom-2020-object-shape-canary-child.ps1")
DIGEST = re.compile(r"[0-9a-f]{64}")
FEATURE_ORDER = ["OBJ-026", "OBJ-033", "OBJ-038", "OBJ-045", "OBJ-013"]
EXPECTED_IDENTITIES = {
    "binding_overlay_sha256": "8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f",
    "progress_sha256": "21ef4916ac2b76e7c29d8e350e77932250cf9ce3eb2a8e7057894b38fc9653ba",
    "private_trace_sha256": "c327552c0077dbce523f2388fe18ea8d98380a9dd9d8778b18fc520658962628",
    "runtime_receipt_sha256": "3412306a0de52692b01c368e60734745049c258a2aa7439df34f3565614197b3",
    "wrapper_sha256": "0c858f7515330be5d14a815c46efe6d18e1515e4acad8b8c232ddfdcfcceaf4f",
    "child_sha256": "ec56a085af9684076543299e7c5ee6b6da1ab5aacc49ea3b744f1144519c0f89",
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
            "target", "identities", "execution", "normalization",
            "predecessor_attempts", "cases", "boundaries", "claims", "privacy",
        },
        "root",
    )
    if (
        value["schema_version"]
        != "hwpx-agent.p08-object-shape-canary-qualification/v1"
        or value["task"] != "P08-24"
        or value["recorded_date"] != "2026-09-15"
        or value["attempt_id"] != "p08-24-object-shape-canary-20260915-05"
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
        source = (ROOT / CHILD).read_text(encoding="utf-8")
        if "$document.Open(" in source or ".Save" in source:
            raise QualificationError("hwp_file_io_source_boundary")
    if value["execution"] != {
        "canary_case_count": 5,
        "candidate_execute_count": 5,
        "effect_observed_count": 5,
        "semantic_undo_verified_count": 5,
        "raw_undo_exact_count": 4,
        "serializer_default_normalized_count": 1,
        "context_setup_undo_verified_count": 1,
        "hwp_file_open_count": 0,
        "document_save_count": 0,
        "remaining_owned_hwp_processes": 0,
        "timed_out": False,
        "stalled": False,
    }:
        raise QualificationError("execution")
    if value["normalization"] != {
        "id": "hwpml2x-drawtext-empty-name-default/v1",
        "scope": "empty_Name_attribute_on_DRAWTEXT_only",
        "non_empty_names_remain_hash_significant": True,
        "geometry_style_text_remain_hash_significant": True,
        "raw_mismatch_preserved": True,
    }:
        raise QualificationError("normalization")
    if value["predecessor_attempts"] != [
        {"attempt_id": "p08-24-object-shape-canary-20260915-01", "state": "failed"},
        {"attempt_id": "p08-24-object-shape-canary-20260915-02", "state": "failed"},
        {"attempt_id": "p08-24-object-shape-canary-20260915-03", "state": "diagnostic_failed"},
        {"attempt_id": "p08-24-object-shape-canary-20260915-04", "state": "superseded_single_case_pass"},
    ]:
        raise QualificationError("predecessor_attempts")
    cases = value["cases"]
    if not isinstance(cases, list) or [item.get("feature_id") for item in cases] != FEATURE_ORDER:
        raise QualificationError("cases")
    case_keys = {
        "feature_id", "capability_id", "source_identifier_sha256", "context",
        "is_action_enable", "execute_return_advisory", "effect_observed",
        "undo_semantic_verified", "undo_raw_exact",
        "empty_name_normalization_counts", "context_setup_undo_verified", "state",
    }
    for item in cases:
        feature_id = item.get("feature_id")
        _exact_keys(item, case_keys, f"case:{feature_id}")
        if (
            DIGEST.fullmatch(item["source_identifier_sha256"]) is None
            or item["context"]
            != "two_rectangle_unsaved_blank_document_first_shape_selected"
            or item["is_action_enable"] is not True
            or item["effect_observed"] is not True
            or item["undo_semantic_verified"] is not True
            or item["state"] != "pass"
        ):
            raise QualificationError(f"case_state:{feature_id}")
        counts = item["empty_name_normalization_counts"]
        _exact_keys(counts, {"before", "after", "undo"}, f"normalization:{feature_id}")
        if feature_id == "OBJ-026":
            if item["undo_raw_exact"] is not False or counts != {
                "before": 0, "after": 1, "undo": 1
            }:
                raise QualificationError("shadow_raw_boundary")
        elif item["undo_raw_exact"] is not True or counts != {
            "before": 1, "after": 1, "undo": 1
        }:
            raise QualificationError(f"raw_boundary:{feature_id}")
        if (feature_id == "OBJ-038") != (item["context_setup_undo_verified"] is True):
            if feature_id == "OBJ-038" or item["context_setup_undo_verified"] is not None:
                raise QualificationError(f"context_undo:{feature_id}")
    if value["boundaries"] != {
        "one_session_one_unsaved_disposable_document": True,
        "setup_rectangle_count": 2,
        "known_modal_executed": False,
        "fixture_or_user_document_opened_by_hwp": False,
        "document_saved": False,
        "candidate_action_executed": True,
        "effect_observed": True,
        "undo_semantic_verified": True,
        "routing_enabled": False,
        "differential_run": False,
    }:
        raise QualificationError("boundaries")
    if value["claims"] != {
        "exact_target_selected_object_canary": True,
        "qualified_canary_case_count": 5,
        "automation_runtime_support_for_all_candidates": False,
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
        "DrawShapeObjShadow", "ShapeObjHorzFlip", "ShapeObjBringToFront",
        "ShapeObjLock", "ShapeObjAttachCaption",
    ):
        if raw in serialized:
            raise QualificationError("raw_identifier_leak")
    return {
        "schema_version": "hwpx-agent.p08-object-shape-canary-validation/v1",
        "state": "pass",
        "task": "P08-24",
        "attempt_id": value["attempt_id"],
        "qualified_canary_case_count": 5,
        "semantic_undo_verified_count": 5,
        "raw_undo_exact_count": 4,
        "hwp_file_open_count": 0,
        "document_save_count": 0,
        "routing": "disabled",
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
