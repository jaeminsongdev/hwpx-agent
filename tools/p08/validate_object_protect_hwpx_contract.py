#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-protect-hwpx-v1.json"
MIGRATION = "protocol/migrations/p08-object-protect-hwpx-v0-to-v1.md"
POLICY = "implementation/p08/P08-14_OBJECT_PROTECT_HWPX_POLICY.md"
REPORT = "implementation/p08/P08-14_OBJECT_PROTECT_HWPX_REPORT.md"
QUALIFICATION = (
    "implementation/p08/evidence/"
    "p08-14-object-protect-hwpx-source-qualification.v1.json"
)

SOURCE_SHA256 = {
    "docs/03_document_model/08_drawing_image_chart.md": "ea35c475b434995174d6130f63e98254a19156aea0d99715511bb9b5c804194b",
    "docs/04_feature_catalog/09_obj.md": "e3c4c71e8d8c608c8e403404c1cf7767bbd91bdfd93dbcdb07f2e91e90c785e8",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md": "e1274922109762ab3de1b7118e954510f37d1f0686b9b0c5fc1152936983bec2",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "specs/work-breakdown-structure.json": "56b5f9fe1279a15e7262d2dbb2c60c372f3bc9ad33acb418e1c905f2a731f2b2",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/object_geometry.rs": "b8d42a0fd02c6a831d1e675761556192b713c59d90fae59e95a367cf3a1b12e1",
    "crates/domain-ir/tests/object_geometry.rs": "5a88b76187bedf9939193de2db85dd105c6924d2946008c4a2d2fcbebf6f1f10",
    "crates/hwpx-package/src/object_geometry_hwpx.rs": "88bbd23bb63cd95e18fdc96c06d9c7029c6cae89ae5917233801036a57fc4a69",
    "crates/hwpx-package/tests/object_geometry_hwpx.rs": "9a72cd328b5923d36f7d8d73ce089a94463899ba4a9fbc5b0340ea4aa3d3980e",
}
MARKERS = {
    "crates/domain-ir/src/object_geometry.rs": (
        'Self::SetLocked { .. } => "obj.object_protect"',
        "ObjectGeometryError::NoOp",
        "source_document_flow_sha256",
        "finish_non_exhaustive",
    ),
    "crates/domain-ir/tests/object_geometry.rs": (
        "plans_and_builds_all_seven_exact_geometry_capabilities",
        "object_protect_rejects_noop_without_building_a_plan",
    ),
    "crates/hwpx-package/src/object_geometry_hwpx.rs": (
        '"lock"',
        "source_section_sha256",
        "source_object_sha256",
        "apply_edits(source",
    ),
    "crates/hwpx-package/tests/object_geometry_hwpx.rs": (
        "lowers_object_protect_for_all_common_kinds_with_one_exact_attribute_edit",
        'replacen("lock=\\\"0\\\"", "lock=\\\"true\\\"", 1)',
        "request_and_build_reject_section_object_state_and_flow_drift",
    ),
}
PROFILE = "hwpx-agent.object-protect-hwpx.hwpml-2011-root-lock/v1"
KINDS = [
    "pic", "rect", "ellipse", "line", "arc", "polygon", "curve", "connectLine",
    "container", "ole", "video", "textart",
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


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_boundary() -> dict[str, Any]:
    return {
        "direct_stage": "integration_passed",
        "obj_045_static_section_hwpx": True,
        "typed_semantic_reopen": True,
        "outside_attribute_span_preserved": True,
        "complete_state_and_flow_bound": True,
        "all_twelve_common_kinds": True,
        "actual_target_hwpx": False,
        "actual_hangul": False,
        "save_reopen": False,
        "object_bounds": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)

    expected_root = {
        "schema_version", "task", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "implementation_files", "profile", "feature_ids", "capabilities",
        "admitted_profile", "planning", "failure_policy", "evidence_boundary",
        "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_root:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.p08-object-protect-hwpx-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P08-14":
        errors.append("task")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_canonicalization")
    if contract.get("source_qualification") != QUALIFICATION:
        errors.append("source_qualification")
    if (contract.get("migration"), contract.get("policy"), contract.get("report")) != (
        MIGRATION, POLICY, REPORT,
    ):
        errors.append("document_paths")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("profile") != PROFILE:
        errors.append("profile")
    if contract.get("feature_ids") != ["OBJ-045"] or contract.get("capabilities") != [
        "obj.object_protect"
    ]:
        errors.append("row_identity")
    admitted = contract.get("admitted_profile")
    if not isinstance(admitted, dict) or admitted.get("object_kinds") != KINDS:
        errors.append("object_kinds")
    if contract.get("evidence_boundary") != expected_boundary():
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "direct_hwpx_integration": "pass",
        "current_target": "not_run",
        "release_green_rows": 0,
        "p08": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")
    if not isinstance(contract.get("failure_policy"), list) or len(contract["failure_policy"]) != 7:
        errors.append("failure_policy")

    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


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
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(IMPLEMENTATION_SHA256)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if value.get("schema_version") != "hwpx-agent.p08-object-protect-hwpx-source-qualification/v1":
        errors.append("qualification_schema")
    if (
        value.get("task") != "P08-14"
        or value.get("profile") != PROFILE
        or value.get("implementation_sha256") != IMPLEMENTATION_SHA256
    ):
        errors.append("qualification_implementation")
    official = value.get("official_source")
    if not isinstance(official, dict) or official != {
        "repository": "https://github.com/hancom-io/owpml-model",
        "commit": "1453388472c703a4b299a0834f425cdac16644b9",
        "reviewed_files": [
            "OWPML/Class/Para/AbstractShapeObjectType.cpp",
            "OWPML/Class/Para/AbstractShapeObjectType.h",
        ],
        "scope": "HWPML_2011_common_shape_root_lock_static_vocabulary_and_inheritance_only",
    }:
        errors.append("qualification_official_source")
    if value.get("tests") != {
        "object_geometry_domain": "7/7 PASS",
        "object_geometry_hwpx": "12/12 PASS",
        "fixture_classes": ["boundary", "happy_path", "negative", "preservation"],
        "all_common_object_kinds": "12/12 PASS",
        "focused_clippy": "PASS",
    }:
        errors.append("qualification_tests")
    expected_claims = {
        key: item for key, item in expected_boundary().items() if key != "direct_stage"
    }
    expected_claims = {"one_row_direct_hwpx_integration": True, **expected_claims}
    if value.get("claims") != expected_claims:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "no partial output"),
        POLICY: (
            "direct_hwpx_integration_pass",
            "AbstractShapeObjectType",
            "obj.aspect_lock",
            "product_complete=false",
        ),
        REPORT: ("7/7 PASS", "12/12 PASS", "actual_hangul=false"),
    }
    for relative, markers in expected.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(
    errors: list[str], sources: int, implementation: int, qualification: bool
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p08-object-protect-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "direct_stage": "integration_passed" if not unique else "not_proven",
        "actual_hangul": False,
        "p08_complete": False,
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        sys.exit(1)
    print(
        "P08_OBJECT_PROTECT_HWPX_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']} "
        "direct_stage=integration_passed actual_hangul=false p08_complete=false"
    )
