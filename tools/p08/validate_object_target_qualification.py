from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-20-object-target-qualification.current-2020.v1.json"
)
ORACLE = Path("tools/p08/object_target_oracle.py")
WRAPPER = Path("implementation/p08/tools/run-hancom-2020-object-target-batch.ps1")
ENGINE = Path("implementation/p08/tools/run-hancom-2020-object-target-batch-engine.ps1")

DIGEST = re.compile(r"[0-9a-f]{64}")
EXPECTED_FEATURES = (
    "OBJ-001", "OBJ-002", "OBJ-007", "OBJ-042",
    "OBJ-015", "OBJ-016", "OBJ-017", "OBJ-018", "OBJ-032", "OBJ-033",
    "OBJ-020", "OBJ-021", "OBJ-022", "OBJ-023", "OBJ-024", "OBJ-026",
    "OBJ-027", "OBJ-028", "OBJ-029", "OBJ-034", "OBJ-035",
    "OBJ-019", "OBJ-025", "OBJ-030", "OBJ-043", "OBJ-045", "OBJ-046",
    "OBJ-047", "OBJ-048", "OBJ-013", "OBJ-012", "OBJ-003", "OBJ-014",
    "OBJ-036", "OBJ-037", "OBJ-038", "OBJ-039", "OBJ-040", "OBJ-041",
    "OBJ-031", "OBJ-010",
)
EXPECTED_IDENTITIES = {
    "fixture_manifest_sha256": "2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b",
    "engine_trace_sha256": "68be0ef72423a3075a68303172702d74aad7bb1d2e13b44613d6956e6753c5f5",
    "runtime_receipt_sha256": "8288ba3e93c1166b998b626d9342f3e2a267b069d3e9a3313c3e738cbcca5d9d",
    "progress_sha256": "d9d1448c7dcf6576256b96198bfe8373e6fec5b5ce2612e302da962572e45eeb",
    "oracle_report_sha256": "18ab75d601ee40681aeb47869e5b097497d18a1f438ced53d22dc6ec9546ecd1",
    "oracle_source_sha256": "2df0b90b5aa125f652d4be365e5bd6ea67a0503668e9084ad96b90e4c37a0e87",
    "wrapper_sha256": "29207f0dd6eaed8b859a75f51177e6a3f2e9f0176bf75d76624fbf3ade24b485",
    "engine_sha256": "406877d9d2e688c5253f8519c2b6ddef4a404957f9cb3d1838fe468fbb1cac9b",
    "bundle_sha256": "c2e6688f17451706f6ea442a482efcc03ba69e430696801bf9ff71f9ae8a9e45",
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


def _exact_keys(value: Any, expected: set[str], context: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise QualificationError(f"shape_drift:{context}")


def _sha256(path: Path, *, root: Path = ROOT) -> str:
    import hashlib

    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def validate(
    qualification_override: dict[str, Any] | None = None,
    *,
    verify_source_hashes: bool = True,
) -> dict[str, Any]:
    value = qualification_override if qualification_override is not None else load()
    _exact_keys(
        value,
        {
            "schema_version", "task", "recorded_date", "attempt_id", "target",
            "identities", "execution", "oracle", "feature_ids",
            "normalization_boundary", "user_access", "privacy", "claims",
        },
        "root",
    )
    if (
        value["schema_version"] != "hwpx-agent.p08-object-target-qualification/v1"
        or value["task"] != "P08-20"
        or value["recorded_date"] != "2026-09-15"
        or value["attempt_id"] != "p08-20-object-target-20260915-18"
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
        not DIGEST.fullmatch(item) for item in value["identities"].values()
    ):
        raise QualificationError("identities")
    if verify_source_hashes:
        for path, key in (
            (ORACLE, "oracle_source_sha256"),
            (WRAPPER, "wrapper_sha256"),
            (ENGINE, "engine_sha256"),
        ):
            if _sha256(path) != EXPECTED_IDENTITIES[key]:
                raise QualificationError(f"source_drift:{path.as_posix()}")
    if value["execution"] != {
        "state": "pass",
        "primary_cases_passed": 41,
        "effective_cases_passed": 41,
        "representative_retries_passed": 3,
        "representative_retry_features": ["OBJ-002", "OBJ-010", "OBJ-024"],
        "recovered_primary_failures": 0,
        "scheduled_session_restarts": 3,
        "retry_session_restarts": 3,
        "remaining_hwp_processes": 0,
    }:
        raise QualificationError("execution")
    if value["oracle"] != {
        "state": "pass",
        "semantic_reopen_passed": 41,
        "resource_integrity_passed": 10,
        "object_bounds_passed": 41,
        "render_passed": 41,
        "resource_profile": "hancom-2020-single-embedded-image-canonical-v1",
        "render_profile": "hancom-2020-object-affected-region-calibrated-v1",
        "render_dpi": 96,
        "calibrated_render_features": [
            "OBJ-020", "OBJ-021", "OBJ-022", "OBJ-023", "OBJ-024", "OBJ-026", "OBJ-034",
        ],
        "unchanged_region_changed_pixels_max": 0,
        "arbitrary_resource_path_remap_allowed": False,
    }:
        raise QualificationError("oracle")
    if tuple(value["feature_ids"]) != EXPECTED_FEATURES or len(set(value["feature_ids"])) != 41:
        raise QualificationError("feature_set")
    if value["normalization_boundary"] != {
        "resource_id_and_path": "exact_hancom_2020_image1_projection_with_payload_media_length_and_reference_multiplicity_preserved",
        "forms": "exact_hancom_2020_static_edit_attribute_and_child_order_projection",
        "hyperlink": "exact_hancom_2020_semicolon_0_0_0_suffix",
        "nested_group_ids": "instance_tree_preserved_target_regenerated_nonidentity_ids",
        "connector_controls": "exact_fixture_bound_hancom_2020_generated_control_points",
        "render": "fixture_bound_object_region_calibration_only",
    }:
        raise QualificationError("normalization_boundary")
    if value["user_access"] != {
        "state": "user_attested",
        "scope": "first_open_access_dialog_only",
        "computer_use_click_or_type_invoked": False,
    }:
        raise QualificationError("user_access")
    if value["privacy"] != {
        "raw_document_text_present": False,
        "user_document_scanned": False,
        "external_network_invoked": False,
        "registry_or_system_setting_changed": False,
        "absolute_private_paths_present": False,
    }:
        raise QualificationError("privacy")
    if value["claims"] != {
        "actual_hangul": True,
        "save_reopen": True,
        "semantic_reopen": True,
        "resource_integrity": True,
        "object_bounds": True,
        "render": True,
        "direct_stage": "oracle_verified",
        "automation_runtime": False,
        "differential": False,
        "required_matrix_green": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        raise QualificationError("claims")
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise QualificationError("private_path_leak")
    return {
        "schema_version": "hwpx-agent.p08-object-target-qualification-validation/v1",
        "state": "pass",
        "task": "P08-20",
        "attempt_id": value["attempt_id"],
        "feature_count": 41,
        "primary_cases_passed": 41,
        "representative_retries_passed": 3,
        "semantic_reopen_passed": 41,
        "resource_integrity_passed": 10,
        "object_bounds_passed": 41,
        "render_passed": 41,
        "direct_stage": "oracle_verified",
        "automation_runtime": "not_run",
        "differential": "not_run",
        "required_matrix": "non_green",
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
