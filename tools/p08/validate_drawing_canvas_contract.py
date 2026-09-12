#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-drawing-canvas-v1.json"
MIGRATION = "protocol/migrations/p08-drawing-canvas-v0-to-v1.md"
POLICY = "implementation/p08/P08-08_DRAWING_CANVAS_POLICY.md"
REPORT = "implementation/p08/P08-08_DRAWING_CANVAS_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-08-drawing-canvas-source-qualification.v1.json"
OFFICIAL_ROOT = Path(r"D:\개발데이터\Temp\hwpx-owpml-model-probe-20260912")
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"

SOURCE_SHA256 = {
    "specs/work-breakdown-structure.json": "56b5f9fe1279a15e7262d2dbb2c60c372f3bc9ad33acb418e1c905f2a731f2b2",
    "docs/03_document_model/08_drawing_image_chart.md": "ea35c475b434995174d6130f63e98254a19156aea0d99715511bb9b5c804194b",
    "docs/04_feature_catalog/09_obj.md": "e3c4c71e8d8c608c8e403404c1cf7767bbd91bdfd93dbcdb07f2e91e90c785e8",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md": "e1274922109762ab3de1b7118e954510f37d1f0686b9b0c5fc1152936983bec2",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "implementation/p08/P08-05_OBJECT_APPEARANCE_POLICY.md": "1d05d280c00b8e61f216ed44fcfe4ed7ea4fcbb4ba86ac72be7fcf806b3da68a",
    "implementation/p08/P08-05_OBJECT_APPEARANCE_REPORT.md": "e7da98298637eaae4083318cb6d496c6bbb193533e580d466b63d0a663a7f090",
    "protocol/private/p08-object-appearance-v1.json": "94e3e7ef6298773f80cc4eb43bd518568a0b2f86715ecbb87448525c91ab073c",
    "implementation/p08/P08-06_OBJECT_COMPOSITION_POLICY.md": "5b42d86e2dd6a9a26706f96473798516ae6a34d0bda0888fab65ea22e5eae8be",
    "protocol/private/p08-object-composition-v1.json": "466fe49261b90ffb046ff7fb8e88ac5ab9aeacb7b0af9cf12c4a0ac30c46c0ab",
    "implementation/p08/P08-07_CHART_AUTOMATION_POLICY.md": "71d35105551af3bd0ccaca52c7dba4c68cfe97a7496c7c10205ee36bcaca7bda",
    "protocol/private/p08-chart-automation-v1.json": "3374cb3cfd16bffc8ed3b203887476c1d95828a5374417a7f5dd614199ebf355",
}
OFFICIAL_SHA256 = {
    "OWPML/Class/Para/ContainerType.h": "09e1a6aab9f867c3e1ff2d1ae80953244d46d47b127b6e6d5d0478c3a74cf22c",
    "OWPML/Class/Para/ContainerType.cpp": "7a37dd1a45bc0b15af58a153eae92b4fe9d894df379993fd1af72bbbf16e8055",
    "OWPML/Class/Para/PictureType.h": "d483022e95171dfa3ad5af0e27d99029f188a4c7e834deed0e2ca89fa88f193c",
    "OWPML/Class/Para/PictureType.cpp": "07475a21f4895f9f6f6d3c566155aedf494a3782976a6ce399bcc4e056b8babe",
    "OWPML/Class/Para/imgClip.h": "89dd01b9ad6cae689c5de0aa6f208ba013a68be28badce806bdb804c5c26b278",
    "OWPML/Class/Para/imgClip.cpp": "46741f03adbe4bfbfec409348ebdbf7f26e9c7de974cad51de620e6a4a2aeb9f",
    "OWPML/Class/Para/EffectsType.h": "6e80f6cd736daad5c7b499e1b9f756c434bfb5e755c53a2be2d95a996e8c5958",
    "OWPML/Class/Para/EffectsType.cpp": "17f00e7b2557fbb068575e147ffa7c5a07c5eede80160f59661f896d25f14bd5",
    "OWPML/Class/Para/OLEType.h": "fa52c5168c6723f79e3bd074fb735d7101c18ac8e1f676b914e2d2c457a122b1",
    "OWPML/Class/Para/OLEType.cpp": "ca455aaac391862a420574aa623274619dc29fc7b23332b48d5c25a6b9516fc8",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/drawing_canvas.rs": "e0fc9e25852f19ab70ad6fdfd3680f1d8dd5a07e7d184cb2d02d5103533de118",
    "crates/domain-ir/src/lib.rs": "b13dcc56b5938d524084179b6c31e1c51bbc0fbd716146f47fcb89fa73cdb8d0",
    "crates/domain-ir/tests/drawing_canvas.rs": "c96670bda68975e02c9ce1d90c33797290581055d21dde02faa964ce0f3e96b9",
}
MARKERS = {
    "crates/domain-ir/src/drawing_canvas.rs": (
        'DRAWING_CANVAS_SCHEMA_VERSION: &str = "hwpx-agent.drawing-canvas/v1"',
        "pub struct DrawingCanvasState",
        "pub enum DrawingCanvasOperation",
        'Self::InsertCanvas { .. } => "obj.drawing_object_insert"',
        'Self::SetPictureClip { .. } => "obj.crop"',
        'Self::SetPictureEffects { .. } => "obj.picture_effects"',
        "ActiveContentPolicy::Blocked",
        "validate_picture_delta",
        "reject_duplicate_json_keys",
        "private_plan_seal_rejects_tampering",
        "<redacted>",
    ),
    "crates/domain-ir/src/lib.rs": ("mod drawing_canvas;", "DrawingCanvasBuilder"),
    "crates/domain-ir/tests/drawing_canvas.rs": (
        "canonicalizes_complete_tree_and_resource_inventory",
        "inserts_one_complete_reserved_canvas_and_preserves_existing_state",
        "changes_only_clip_and_payload_binding",
        "changes_only_effects_and_appearance_binding",
        "rejects_invalid_clip_effects_and_unblocked_ole",
        "rechecks_request_plan_and_build_drift",
        "enforces_json_limits_unknown_duplicate_keys_and_redacted_debug",
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


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False, False)

    if contract.get("schema_version") != "hwpx-agent.drawing-canvas-contract/v1":
        errors.append("schema_version")
    if contract.get("state_schema_version") != "hwpx-agent.drawing-canvas/v1":
        errors.append("state_schema_version")
    if contract.get("task") != "P08-08":
        errors.append("task")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_canonicalization")
    if contract.get("source_qualification") != QUALIFICATION:
        errors.append("source_qualification")
    if (contract.get("migration"), contract.get("policy"), contract.get("report")) != (
        MIGRATION,
        POLICY,
        REPORT,
    ):
        errors.append("document_paths")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    operations = contract.get("operations")
    if not isinstance(operations, dict) or list(operations) != [
        "obj.drawing_object_insert",
        "obj.crop",
        "obj.picture_effects",
    ]:
        errors.append("operations")
    active = contract.get("active_content")
    if (
        not isinstance(active, dict)
        or active.get("activation_policy") != "blocked_only"
        or active.get("creation") is not False
        or active.get("activation") is not False
        or active.get("semantic_property_edit") is not False
    ):
        errors.append("active_content")
    boundary = contract.get("evidence_boundary")
    if not isinstance(boundary, dict) or boundary != {
        "exact_canvas_state_component_pass": True,
        "focused_rust_tests": "10/10 PASS",
        "direct_hwpx": False,
        "synthetic_package": False,
        "security_corpus": False,
        "actual_hangul": False,
        "save_reopen": False,
        "property_readback": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p08_08_complete": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        errors.append("evidence_boundary")
    gate = contract.get("gate_decision")
    if not isinstance(gate, dict) or gate != {
        "component": "pass",
        "direct_stage": "unit_passed",
        "exact_canvas_state": "pass",
        "direct_hwpx": "not_run",
        "security_corpus": "not_run",
        "p08_08": "checkpoint_component_pass_task_incomplete",
        "p08_08_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")
    if not isinstance(contract.get("failure_policy"), list) or len(contract["failure_policy"]) != 13:
        errors.append("failure_policy")

    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok, official_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok, official_ok)


def validate_sources(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, expected = item.get("path"), item.get("sha256")
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
            if canonical_digest(file(root, relative)) != expected:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path")
    if declared != SOURCE_SHA256:
        errors.append("source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if raw_digest(path) != expected:
                errors.append("implementation_digest")
            text = path.read_text(encoding="utf-8")
            if any(marker not in text for marker in MARKERS[relative]):
                errors.append("implementation_marker")
            if relative.endswith("drawing_canvas.rs") and "HAction" in text:
                errors.append("raw_action_name")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(IMPLEMENTATION_SHA256)


def validate_qualification(root: Path, errors: list[str]) -> tuple[bool, bool]:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False, False
    public = value.get("public_model")
    official_ok = (
        isinstance(public, dict)
        and public.get("repository") == "hancom-io/owpml-model"
        and public.get("commit") == OFFICIAL_COMMIT
        and public.get("source_locks") == OFFICIAL_SHA256
    )
    if not official_ok:
        errors.append("qualification_official")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    claims = value.get("claims")
    if not isinstance(claims, dict) or claims != {
        "exact_canvas_state_component_pass": True,
        "insert_clip_effect_transitions": True,
        "opaque_ole_activation_blocked_by_model": True,
        "direct_hwpx": False,
        "synthetic_package": False,
        "security_corpus": False,
        "actual_hangul": False,
        "save_reopen": False,
        "property_readback": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p08_08_complete": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    tests = value.get("tests")
    if not isinstance(tests, dict) or tests.get("focused_rust") != "10/10 PASS":
        errors.append("qualification_tests")
    if root.resolve() == ROOT.resolve() and official_ok:
        if not OFFICIAL_ROOT.is_dir():
            errors.append("official_source_root")
            official_ok = False
        else:
            for relative, expected in OFFICIAL_SHA256.items():
                path = OFFICIAL_ROOT / relative
                if not path.is_file() or raw_digest(path) != expected:
                    errors.append("official_source_digest")
                    official_ok = False
    return not any(item.startswith("qualification_") for item in errors), official_ok


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "blocked", "fail closed"),
        POLICY: (
            "exact_canvas_transition_component_pass / successor_static_hwpx_integration_pass",
            "P08-05 `PictureEffects`",
            "p08_08_complete=false",
        ),
        REPORT: ("10/10 PASS", "P08-11", "no complete package"),
    }
    for relative, markers in expected.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(
    errors: list[str],
    sources: int,
    implementation: int,
    qualification: bool,
    official: bool,
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p08-drawing-canvas-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "official_source_locks_verified": official,
        "task": "P08-08",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "exact_canvas_state": "pass" if not unique else "not_proven",
        "direct_hwpx": "not_run",
        "security_corpus": "not_run",
        "p08_08_complete": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        sys.exit(1)
    print(
        "P08_DRAWING_CANVAS_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']} "
        "exact_canvas_state=pass direct_hwpx=not_run security_corpus=not_run "
        "p08_08_complete=false"
    )
