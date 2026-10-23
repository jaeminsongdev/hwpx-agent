#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-object-remainder-hwpx-v1.json"
MIGRATION = "protocol/migrations/p08-object-remainder-hwpx-v0-to-v1.md"
POLICY = "implementation/p08/P08-17_OBJECT_REMAINDER_HWPX_POLICY.md"
REPORT = "implementation/p08/P08-17_OBJECT_REMAINDER_HWPX_REPORT.md"
QUALIFICATION = (
    "implementation/p08/evidence/"
    "p08-17-object-remainder-hwpx-source-qualification.current-2020.v1.json"
)
PROFILE = "hwpx-agent.object-remainder-target.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
INSTALLED_TEMPLATE = Path(
    r"C:\Program Files (x86)\HNC\Office 2020\HOffice110\Shared\HwpTemplate\Draw"
    r"\FG_Basic_Shapes\Rectangle.drt"
)
INSTALLED_TEMPLATE_BYTES = 12_288
INSTALLED_TEMPLATE_SHA256 = "97263ccadb83c470550354abf6bf8fdfd57e8ba4f3b294f479c7bab80f36753b"

FEATURES = ["OBJ-003", "OBJ-012", "OBJ-013", "OBJ-014", "OBJ-019", "OBJ-030", "OBJ-044", "OBJ-046", "OBJ-047"]
CAPABILITIES = [
    "obj.drawing_gallery", "obj.form_object_insert", "obj.caption_insert",
    "obj.paragraph_band_object", "obj.margin_caption", "obj.image_properties",
    "obj.aspect_lock", "obj.printable", "obj.alt_text",
]
SOURCE_SHA256 = {
    "docs/03_document_model/08_drawing_image_chart.md": "ea35c475b434995174d6130f63e98254a19156aea0d99715511bb9b5c804194b",
    "docs/04_feature_catalog/09_obj.md": "e3c4c71e8d8c608c8e403404c1cf7767bbd91bdfd93dbcdb07f2e91e90c785e8",
    "docs/04_feature_catalog/contracts/09_obj_contracts.md": "e1274922109762ab3de1b7118e954510f37d1f0686b9b0c5fc1152936983bec2",
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "specs/work-breakdown-structure.json": "56b5f9fe1279a15e7262d2dbb2c60c372f3bc9ad33acb418e1c905f2a731f2b2",
}
IMPLEMENTATION_SHA256 = {
    "crates/hwpx-package/src/object_common_properties_hwpx.rs": "e1aeeea3fa03fe6325efa78d40d704c9e4420b24fd834da6b4fd2c1b705b86b6",
    "crates/hwpx-package/src/object_caption_insert_hwpx.rs": "d3fc91d0cc18649f4d59db11f6855c5b2e181459d38abd37d14c5bc68aac4878",
    "crates/hwpx-package/src/object_form_insert_hwpx.rs": "b505d5ee747d90af2a7571b16c3e96929d0b3b77c2595720eb126198a62be9c1",
    "crates/hwpx-package/src/object_remainder_target.rs": "3ab9250db0326a7f20e3a0607e3a632ba5b9190ed28f8b1ccfafa92019294879",
    "crates/hwpx-package/examples/p08_19_support/special.rs": "7830ba6b3ca65acde05e3843bfd98fd1d6e0fb26fb437c51e84d03e2367c2b43",
    "crates/hwpx-package/tests/object_common_properties_hwpx.rs": "94c2a449c151214c50778b752fe59c92e2b28e5748ed692d4f08feb4c465d956",
    "crates/hwpx-package/tests/object_caption_insert_hwpx.rs": "ba8e043c2fbd4db9927afff045bb898fde783c7e28a3beab5a1fa04b004ee31b",
    "crates/hwpx-package/tests/object_form_insert_hwpx.rs": "90cb32121ebaa0d6c05a31d19c456be2b916a372cd368c300288bf6a6b5dcd98",
    "crates/hwpx-package/tests/object_remainder_target.rs": "85bf7db219324c16797a3f02a84c14fbd8f380917698b8a98a06212a6c741989",
}
IMPLEMENTATION_FILES = ["crates/hwpx-package/src/lib.rs", *IMPLEMENTATION_SHA256]
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


def expected_direct() -> dict[str, str]:
    return {
        "OBJ-003": "installed_rectangle_drt_exact_identity_to_native_rectangle",
        "OBJ-012": "static_edit_insert_complete_native_state_hash_profile",
        "OBJ-013": "plain_static_caption_insert_exact_subtree",
        "OBJ-014": "fixed_rectangle_behind_paragraph_band_profile",
        "OBJ-019": "existing_plain_caption_and_outMargin_only",
        "OBJ-030": "checked_imgDim_orgSz_curSz_mapping",
        "OBJ-046": "existing_admitted_form_root_only",
        "OBJ-047": "existing_shapeComment_description_only_empty_title",
    }


def expected_unavailable() -> dict[str, str]:
    return {
        "OBJ-044": "aspect_lock_native_field_unqualified",
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], False)

    expected_keys = {
        "schema_version", "task", "profile", "feature_ids", "capabilities",
        "source_lock_canonicalization", "source_qualification", "migration", "policy",
        "report", "source_locks", "implementation_files", "direct_profiles",
        "unavailable_profiles", "failure_policy", "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_keys:
        errors.append("contract_shape")
    if (
        contract.get("schema_version") != "hwpx-agent.p08-object-remainder-hwpx-contract/v1"
        or contract.get("task") != "P08-17"
        or contract.get("profile") != PROFILE
    ):
        errors.append("contract_identity")
    if contract.get("feature_ids") != FEATURES or contract.get("capabilities") != CAPABILITIES:
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
    if contract.get("direct_profiles") != expected_direct():
        errors.append("direct_profiles")
    if contract.get("unavailable_profiles") != expected_unavailable():
        errors.append("unavailable_profiles")
    if not isinstance(contract.get("failure_policy"), list) or len(contract["failure_policy"]) != 7:
        errors.append("failure_policy")

    boundary = contract.get("evidence_boundary")
    if not isinstance(boundary, dict):
        errors.append("evidence_boundary")
    else:
        if boundary.get("direct_hwpx_profiles") != 8 or boundary.get("unavailable_with_reason_profiles") != 1:
            errors.append("evidence_counts")
        if boundary.get("integration_rows") != ["OBJ-003", "OBJ-012", "OBJ-013", "OBJ-014", "OBJ-019", "OBJ-030", "OBJ-046", "OBJ-047"]:
            errors.append("integration_rows")
        if boundary.get("unit_rows") != ["OBJ-044"]:
            errors.append("unit_rows")
        forbidden_true = {
            "actual_target_hwpx", "hancom_open", "save_reopen", "resource_integrity",
            "object_bounds", "render", "automation_runtime_binding", "differential",
            "p08_complete", "production_ready", "product_complete",
        }
        if any(boundary.get(key) is not False for key in forbidden_true):
            errors.append("evidence_false_promotion")
        if boundary.get("release_green_rows") != 0:
            errors.append("green_promotion")
    if contract.get("gate_decision") != {
        "component": "pass",
        "current_target": "not_run",
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
            not isinstance(relative, str) or relative in declared
            or not isinstance(expected, str) or not DIGEST.fullmatch(expected)
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
        "crates/hwpx-package/src/object_common_properties_hwpx.rs": (
            "ObjectCommonPropertiesHwpxLowerer", "native_image_dimensions",
            "verify_preservation", "UnsupportedProfile",
        ),
        "crates/hwpx-package/src/object_caption_insert_hwpx.rs": (
            "ObjectCaptionInsertHwpxLowerer", "plain-static",
            "verify_insertion", "UnsupportedProfile",
        ),
        "crates/hwpx-package/src/object_form_insert_hwpx.rs": (
            "ObjectFormInsertHwpxLowerer", "static-edit",
            "verify_insertion", "UnsupportedProfile",
        ),
        "crates/hwpx-package/src/object_remainder_target.rs": (
            "ObjectRemainderTargetRouter", "AspectLockNativeFieldUnqualified",
            "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        ),
        "crates/hwpx-package/examples/p08_19_support/special.rs": (
            "DRAWING_GALLERY_TEMPLATE_SHA256", "drawing_gallery_case",
            "paragraph_band_case", "ObjectTextWrap::BehindText",
        ),
        "crates/hwpx-package/tests/object_common_properties_hwpx.rs": (
            "margin_and_existing_plain_caption_patch_exact_native_spans",
            "unsupported_or_lossy_profiles_fail_before_any_output",
        ),
        "crates/hwpx-package/tests/object_caption_insert_hwpx.rs": (
            "inserts_one_exact_plain_caption_and_preserves_every_other_byte",
            "caption_attribute_drift_are_rejected",
        ),
        "crates/hwpx-package/tests/object_form_insert_hwpx.rs": (
            "inserts_one_exact_static_edit_and_preserves_every_other_byte",
            "child_order_drift_are_rejected",
        ),
        "crates/hwpx-package/tests/object_remainder_target.rs": (
            "aspect_lock_remains_unqualified_with_a_specific_stable_reason",
            "rejected_direct_preflight_never_widens_to_unverified_automation",
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
        if (
            "mod object_common_properties_hwpx;" not in lib
            or "ObjectCommonPropertiesHwpxLowerer" not in lib
            or "mod object_caption_insert_hwpx;" not in lib
            or "ObjectCaptionInsertHwpxLowerer" not in lib
            or "mod object_form_insert_hwpx;" not in lib
            or "ObjectFormInsertHwpxLowerer" not in lib
            or "mod object_remainder_target;" not in lib
            or "ObjectRemainderTargetRouter" not in lib
        ):
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
        != "hwpx-agent.p08-object-remainder-hwpx-source-qualification/v1"
        or value.get("task") != "P08-17"
        or value.get("profile") != PROFILE
        or value.get("source_sha256") != SOURCE_SHA256
        or value.get("implementation_sha256") != IMPLEMENTATION_SHA256
    ):
        errors.append("qualification_identity")
    official = value.get("official_sources")
    if not isinstance(official, dict) or set(official) != {"owpml_model", "automation_archive"}:
        errors.append("qualification_official_sources")
    else:
        model = official.get("owpml_model")
        archive = official.get("automation_archive")
        if not isinstance(model, dict) or model.get("commit") != "1453388472c703a4b299a0834f425cdac16644b9":
            errors.append("qualification_model")
        if not isinstance(archive, dict) or archive.get("commit") != "213c7faad552b4853b525887e36accb6025e837b":
            errors.append("qualification_archive")
    validate_installed_template(value.get("installed_template"), errors)
    if value.get("native_map") != {
        **{key: item for key, item in expected_direct().items()},
        "OBJ-044": "CAPABILITY_UNAVAILABLE_FOR_TARGET:protect_size_is_not_aspect_lock",
    }:
        errors.append("qualification_native_map")
    target = value.get("target")
    if target != {
        "product": "Hancom Hangul 2020", "version": "11.0.0.9136",
        "architecture": "x86", "locale": "ko-KR",
        "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        "target_execution": "not_run",
    }:
        errors.append("qualification_target")
    claims = value.get("claims")
    if not isinstance(claims, dict) or claims.get("direct_hwpx_profiles") != 8 or claims.get("unavailable_with_reason_profiles") != 1:
        errors.append("qualification_claims")
    forbidden_true = {
        "complete_native_coverage_for_all_nine", "actual_target_hwpx", "hancom_open",
        "save_reopen", "resource_integrity", "object_bounds", "render",
        "automation_runtime_binding", "differential", "p08_complete", "production_ready",
        "product_complete",
    }
    if not isinstance(claims, dict) or any(claims.get(key) is not False for key in forbidden_true):
        errors.append("qualification_false_promotion")
    return not any(error.startswith("qualification_") for error in errors)


def validate_installed_template(value: Any, errors: list[str]) -> None:
    expected = {
        "path": str(INSTALLED_TEMPLATE),
        "byte_len": INSTALLED_TEMPLATE_BYTES,
        "format": "OLE Compound File Binary",
        "sha256": INSTALLED_TEMPLATE_SHA256,
        "redistributed": False,
    }
    if value != expected:
        errors.append("qualification_installed_template")
        return
    try:
        metadata = INSTALLED_TEMPLATE.lstat()
        data = INSTALLED_TEMPLATE.read_bytes()
        if (
            INSTALLED_TEMPLATE.is_symlink()
            or not INSTALLED_TEMPLATE.is_file()
            or metadata.st_size != INSTALLED_TEMPLATE_BYTES
            or data[:8] != bytes.fromhex("d0cf11e0a1b11ae1")
            or hashlib.sha256(data).hexdigest() != INSTALLED_TEMPLATE_SHA256
        ):
            errors.append("qualification_installed_template_identity")
    except OSError:
        errors.append("qualification_installed_template_path")


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "CAPABILITY_UNAVAILABLE_FOR_TARGET"),
        POLICY: ("direct_hwpx_profiles=8", "complete_native_coverage_for_all_nine=false", "p08_complete=false"),
        REPORT: ("19/19 PASS", "unavailable_with_reason_profiles=1", "release_green_rows=0"),
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
        "schema_version": "hwpx-agent.p08-object-remainder-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_FILES),
        "source_qualification_verified": qualification,
        "direct_hwpx_profiles": 8,
        "unavailable_with_reason_profiles": 1,
        "actual_target": "not_run",
        "p08_complete": False,
    }


def main() -> int:
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value["state"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
