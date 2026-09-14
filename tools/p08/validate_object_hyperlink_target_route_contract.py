#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-hyperlink-target-route-v1.json"
MIGRATION = "protocol/migrations/p08-object-hyperlink-target-route-v0-to-v1.md"
POLICY = "implementation/p08/P08-16_OBJECT_HYPERLINK_TARGET_ROUTE_POLICY.md"
REPORT = "implementation/p08/P08-16_OBJECT_HYPERLINK_TARGET_ROUTE_REPORT.md"
QUALIFICATION = (
    "implementation/p08/evidence/"
    "p08-16-object-hyperlink-target-route-source-qualification.current-2020.v1.json"
)
PROFILE = "hwpx-agent.object-hyperlink-target.hangul-2020-11.0.0.9136-x86-ko-KR/v1"

SOURCE_SHA256 = {
    "docs/03_document_model/08_drawing_image_chart.md": "ea35c475b434995174d6130f63e98254a19156aea0d99715511bb9b5c804194b",
    "docs/04_feature_catalog/09_obj.md": "e3c4c71e8d8c608c8e403404c1cf7767bbd91bdfd93dbcdb07f2e91e90c785e8",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md": "e1274922109762ab3de1b7118e954510f37d1f0686b9b0c5fc1152936983bec2",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "specs/work-breakdown-structure.json": "56b5f9fe1279a15e7262d2dbb2c60c372f3bc9ad33acb418e1c905f2a731f2b2",
}
IMPLEMENTATION_SHA256 = {
    "crates/hwpx-package/src/object_hyperlink_target.rs": "8742b3cdf8ca2525cd998cfa067767eb620b4a2afc6beac231120bf68ff39a69",
    "crates/hwpx-package/tests/object_hyperlink_target.rs": "2ac64cef4d59282d4dde06b665811384df1f6299febfb057d7a4f06b7f0f199a",
}
IMPLEMENTATION_FILES = [
    "crates/hwpx-package/src/lib.rs",
    *IMPLEMENTATION_SHA256,
]
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load(root: Path, relative: str) -> Any:
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard)


def normalized_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_route_policy() -> dict[str, Any]:
    return {
        "direct_hwpx": [
            "picture",
            "basic_shape",
            "text_box",
            "drawing_canvas",
            "embedded_object",
        ],
        "chart": "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        "form_object_and_paragraph_band": "outside_catalogued_capability_ir",
        "direct_preflight_rejected": "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        "desktop_automation_fallback": "unavailable_with_reason",
        "fallback_after_partial_mutation": "forbidden",
    }


def expected_target_observation() -> dict[str, Any]:
    return {
        "strength": "target_scope_only_without_persisted_raw_trace",
        "generic_shape_semantic_action_available": True,
        "generic_shape_invocation": "dialog_opened_user_attested_mutation_not_claimed",
        "chart_selection_paths": 3,
        "chart_selection_successes": 3,
        "chart_semantic_action_available_count": 0,
        "chart_command_executed": False,
        "document_saved": False,
        "external_file_opened": False,
        "owned_hwp_processes_after": 0,
    }


def expected_boundary() -> dict[str, Any]:
    return {
        "target_scope_qualified": True,
        "fail_closed_route_pass": True,
        "chart_unavailable_with_reason": True,
        "route_unit_tests": True,
        "raw_target_trace_persisted": False,
        "object_hyperlink_mutation": False,
        "actual_target_hwpx": False,
        "save_reopen": False,
        "resource_integrity": False,
        "object_bounds": False,
        "render": False,
        "automation_runtime_binding": False,
        "differential": False,
        "obj_048_row_stage": "unit_passed",
        "obj_048_complete": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], False)

    expected_keys = {
        "schema_version",
        "task",
        "profile",
        "feature_ids",
        "capabilities",
        "source_lock_canonicalization",
        "source_qualification",
        "migration",
        "policy",
        "report",
        "source_locks",
        "implementation_files",
        "route_policy",
        "target_observation",
        "failure_policy",
        "evidence_boundary",
        "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_keys:
        errors.append("contract_shape")
    if (
        contract.get("schema_version")
        != "hwpx-agent.p08-object-hyperlink-target-route-contract/v1"
        or contract.get("task") != "P08-16"
        or contract.get("profile") != PROFILE
    ):
        errors.append("contract_identity")
    if contract.get("feature_ids") != ["OBJ-048"] or contract.get("capabilities") != [
        "obj.object_hyperlink"
    ]:
        errors.append("row_identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if (
        contract.get("source_qualification") != QUALIFICATION
        or contract.get("migration") != MIGRATION
        or contract.get("policy") != POLICY
        or contract.get("report") != REPORT
    ):
        errors.append("artifact_paths")
    if contract.get("implementation_files") != IMPLEMENTATION_FILES:
        errors.append("implementation_files")
    if contract.get("route_policy") != expected_route_policy():
        errors.append("route_policy")
    if contract.get("target_observation") != expected_target_observation():
        errors.append("target_observation")
    if not isinstance(contract.get("failure_policy"), list) or len(contract["failure_policy"]) != 6:
        errors.append("failure_policy")
    if contract.get("evidence_boundary") != expected_boundary():
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "chart_fallback": "unavailable_with_reason",
        "current_target_mutation": "not_run",
        "release_green_rows": 0,
        "p08": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")

    validate_source_locks(root, contract.get("source_locks"), errors)
    validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, qualification_ok)


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("source_lock_shape")
        return
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative = item.get("path")
        expected = item.get("sha256")
        if (
            not isinstance(relative, str)
            or relative in declared
            or not isinstance(expected, str)
            or not DIGEST.fullmatch(expected)
        ):
            errors.append("source_lock_identity")
            continue
        declared[relative] = expected
        try:
            if normalized_sha256(file(root, relative)) != expected:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path")
    if declared != SOURCE_SHA256:
        errors.append("source_lock_set")


def validate_implementation(root: Path, errors: list[str]) -> None:
    markers = {
        "crates/hwpx-package/src/object_hyperlink_target.rs": (
            "ObjectHyperlinkTargetRouter",
            "ObjectPropertyKind::Chart",
            "ObjectHyperlinkDirectAdmission::Rejected",
            "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        ),
        "crates/hwpx-package/tests/object_hyperlink_target.rs": (
            "chart_fails_closed_without_desktop_automation_fallback",
            "rejected_direct_preflight_never_widens_to_dialog_automation",
            "target_drift_and_out_of_scope_ir_kinds_are_rejected",
        ),
    }
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if raw_sha256(path) != expected:
                errors.append("implementation_digest")
            text = path.read_text(encoding="utf-8")
            if any(marker not in text for marker in markers[relative]):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    try:
        lib = file(root, "crates/hwpx-package/src/lib.rs").read_text(encoding="utf-8")
        if "mod object_hyperlink_target;" not in lib or "ObjectHyperlinkTargetRouter" not in lib:
            errors.append("integration_export")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("integration_export")


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if (
        value.get("schema_version")
        != "hwpx-agent.p08-object-hyperlink-target-route-source-qualification/v1"
        or value.get("task") != "P08-16"
        or value.get("profile") != PROFILE
        or value.get("source_sha256") != SOURCE_SHA256
        or value.get("implementation_sha256") != IMPLEMENTATION_SHA256
    ):
        errors.append("qualification_identity")
    official = value.get("official_sources")
    if not isinstance(official, dict) or set(official) != {
        "owpml_model",
        "automation_archive",
        "help",
    }:
        errors.append("qualification_official_sources")
    else:
        archive = official.get("automation_archive")
        documents = archive.get("documents") if isinstance(archive, dict) else None
        if (
            not isinstance(archive, dict)
            or archive.get("commit") != "213c7faad552b4853b525887e36accb6025e837b"
            or not isinstance(documents, list)
            or len(documents) != 4
            or any(
                not isinstance(item, dict)
                or set(item) != {"path", "sha256"}
                or not DIGEST.fullmatch(str(item.get("sha256", "")))
                for item in documents
            )
        ):
            errors.append("qualification_archive")
    observation = value.get("target_observation")
    if not isinstance(observation, dict):
        errors.append("qualification_observation")
    else:
        target = observation.get("target")
        positive = observation.get("generic_shape_positive_control")
        negative = observation.get("chart_negative_control")
        safety = observation.get("safety")
        if target != {
            "product": "Hancom Hangul 2020",
            "version": "11.0.0.9136",
            "architecture": "x86",
            "locale": "ko-KR",
            "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        }:
            errors.append("qualification_target")
        if positive != {
            "semantic_action_available": True,
            "invocation_result": "dialog_opened_user_attested",
            "mutation_result": "not_claimed",
        }:
            errors.append("qualification_positive_control")
        if negative != {
            "selection_paths": 3,
            "selection_successes": 3,
            "semantic_action_available_count": 0,
            "command_executed": False,
        }:
            errors.append("qualification_negative_control")
        if safety != {
            "external_file_opened": False,
            "document_saved": False,
            "raw_trace_persisted": False,
            "owned_hwp_processes_after": 0,
        }:
            errors.append("qualification_safety")
    claims = value.get("claims")
    if not isinstance(claims, dict) or claims.get("chart_unavailable_with_reason") is not True:
        errors.append("qualification_claims")
    forbidden_true = {
        "raw_target_trace_persisted",
        "object_hyperlink_mutation",
        "actual_target_hwpx",
        "save_reopen",
        "resource_integrity",
        "object_bounds",
        "render",
        "automation_runtime_binding",
        "differential",
        "obj_048_complete",
        "p08_complete",
        "production_ready",
        "product_complete",
    }
    if not isinstance(claims, dict) or any(claims.get(key) is not False for key in forbidden_true):
        errors.append("qualification_false_promotion")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "CAPABILITY_UNAVAILABLE_FOR_TARGET"),
        POLICY: (
            "target_scope_qualified",
            "raw_target_trace_persisted=false",
            "product_complete=false",
        ),
        REPORT: ("5/5", "chart_unavailable_with_reason=true", "obj_048_complete=false"),
    }
    for relative, markers in expected.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p08-object-hyperlink-target-route-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_FILES),
        "source_qualification_verified": qualification,
        "chart_fallback": "unavailable_with_reason",
        "obj_048_row_stage": "unit_passed",
        "actual_target_mutation": False,
        "p08_complete": False,
    }


def main() -> int:
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value["state"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
