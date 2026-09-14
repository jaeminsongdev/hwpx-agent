#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p08-active-content-v1.json"
MIGRATION = "protocol/migrations/p08-active-content-v0-to-v1.md"
POLICY = "implementation/p08/P08-08_ACTIVE_CONTENT_POLICY.md"
REPORT = "implementation/p08/P08-08_ACTIVE_CONTENT_REPORT.md"
QUALIFICATION = "implementation/p08/evidence/p08-08-active-content-source-qualification.v1.json"
OFFICIAL_ROOT = Path(r"D:\개발데이터\Temp\hwpx-owpml-model-probe-20260912")
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"

SOURCE_SHA256 = {
    "docs/09_roadmap/P08_images_shapes_drawing_charts.md": "f07ee05eb72481f86b9499fbc9aa3f5e8191f42f875b6e0bd1a88fc7c9a62fe3",
    "docs/12_implementation_guides/11_security_privacy_license.md": "0be76f7e2c6c7a77a2031b10322839bf8693914f2ad7740de44646ea7f6d7b75",
    "docs/12_implementation_guides/07_windows_automation_worker.md": "76e5cfb985f77b55347714f3d3d3b97c527c18d0d8238a4c0e79b3f680b44168",
    "implementation/p08/P08-08_DRAWING_CANVAS_POLICY.md": "b199ffed1828bf83e3c581ed02251f2dd1514b5d236e4bd4455cd0d08b5e11b4",
    "protocol/private/p08-drawing-canvas-v1.json": "688bde7c0f889885bf06defa1bf7bd654cc038f88bf850d52a21bf4dbe9ef074",
}
OFFICIAL_SHA256 = {
    "OWPML/Class/Para/OLEType.h": "fa52c5168c6723f79e3bd074fb735d7101c18ac8e1f676b914e2d2c457a122b1",
    "OWPML/Class/Para/OLEType.cpp": "ca455aaac391862a420574aa623274619dc29fc7b23332b48d5c25a6b9516fc8",
    "OWPML/Class/Para/VideoType.h": "ec00541d4ab1e51c81b2efe5cfefb64fda6a108bc396969afa12497a1aa85e63",
    "OWPML/Class/Para/VideoType.cpp": "fc8cd8ca3eac3f99255146234012920b08004d0f5e6cf5ac4a601b8ad764008c",
    "OWPML/Class/Para/AbstractFormObjectType.h": "949c9d96ece2cbd7a23779dd310471318d74fc91235f236d1a47247de138625b",
    "OWPML/Class/Para/AbstractFormObjectType.cpp": "f516fbeef26442f06d3e9e12d580a391c9323313a956509cfcaf88bf2c727e4a",
    "OWPML/Class/Para/RunType.cpp": "dbaa0fe2b553dccc13381c856fd9c188185a16bf63685f575acf6bf2c9b88dee",
    "OWPML/Class/enumdef.h": "1c86392c934ac85f7ddd85c710b76be7649403a8404bce146db52558a0b95457",
}
IMPLEMENTATION_SHA256 = {
    "crates/hwpx-package/src/active_content.rs": "d9c095d7c58fcdc0c375dc754d6c059e7159e60a4d16ebd825262f6ea2f3d017",
    "crates/hwpx-package/src/reader.rs": "e40d1da01f1aa52b2d1453fe8165d862e6c3a284c7dfaaa10eed1b7850d3e115",
    "crates/hwpx-package/src/lib.rs": "5c7d538880cc26259c8981a69df51fce54b795f1bd1b0204717fc860718fc37b",
    "crates/hwpx-package/tests/active_content.rs": "af64cbf35f648d15dfe4f20205c87f56ea47d74d81ae4814167fdd22e2f359ae",
}
MARKERS = {
    "crates/hwpx-package/src/active_content.rs": (
        'ACTIVE_CONTENT_SCHEMA_VERSION: &str = "hwpx-agent.active-content-inventory/v1"',
        "pub struct ActiveContentInventory",
        "pub fn scan<R: Read + Seek>",
        "fn scan_ole_control(",
        "fn scan_video_control(",
        "fn executable_signature(",
        "pub const fn authorize(",
        "pub fn verify_preserved(",
        "control_states(&self.controls)",
        "<redacted>",
    ),
    "crates/hwpx-package/src/reader.rs": (
        "fn nested_signature(bytes: &[u8])",
        'bytes.starts_with(b"PK\\x03\\x04")',
    ),
    "crates/hwpx-package/src/lib.rs": (
        "mod active_content;",
        "ActiveContentInventory",
        "ActiveContentPreservationReceipt",
    ),
    "crates/hwpx-package/tests/active_content.rs": (
        "embedded_ole_is_relationship_bound_opaque_and_never_activatable",
        "local_video_and_unreferenced_audio_are_complete_and_signature_checked",
        "external_ole_web_video_and_form_commands_are_quarantined_without_value_leak",
        "namespace_spoof_dangling_reference_and_bad_enum_fail_closed",
        "preservation_allows_unrelated_xml_shift_but_rejects_payload_or_control_tamper",
        "limits_and_json_are_finite_deterministic_and_redacted",
    ),
}
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


def file(root: Path, relative: str, maximum: int = 64 * 1024 * 1024) -> Path:
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

    if contract.get("schema_version") != "hwpx-agent.active-content-contract/v1":
        errors.append("schema_version")
    if contract.get("inventory_schema_version") != "hwpx-agent.active-content-inventory/v1":
        errors.append("inventory_schema_version")
    if contract.get("profile_id") != (
        "hwpx-agent.active-content.hwpml-2011-opaque-preserve-blocked/v1"
    ):
        errors.append("profile_id")
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

    activation = contract.get("activation")
    if not isinstance(activation, dict) or activation != {
        "allowed": False,
        "always_denied": [
            "ole",
            "multimedia",
            "embedded_executable",
            "script_macro",
            "form_command",
            "external_link",
        ],
        "creation_api": False,
        "dispatch_api": False,
        "fetch_api": False,
        "playback_api": False,
        "execution_api": False,
    }:
        errors.append("activation")
    inventory = contract.get("inventory")
    if (
        not isinstance(inventory, dict)
        or inventory.get("authoritative_package_graph_rebuilt") is not True
        or inventory.get("all_xml_parts_integrity_read") is not True
        or inventory.get("state_sha256_excludes_diagnostic_ordinal") is not True
    ):
        errors.append("inventory")
    preservation = contract.get("preservation")
    if not isinstance(preservation, dict) or preservation != {
        "resource_bytes_exact": True,
        "active_element_bytes_exact": True,
        "unrelated_package_changes_allowed": True,
        "diagnostic_ordinal_shift_allowed": True,
        "addition_removal_retarget_or_mutation_rejected": True,
        "receipt_activation_allowed": False,
    }:
        errors.append("preservation")
    boundary = contract.get("evidence_boundary")
    if not isinstance(boundary, dict) or boundary != expected_claims(with_tests=True):
        errors.append("evidence_boundary")
    gate = contract.get("gate_decision")
    if not isinstance(gate, dict) or gate != {
        "component": "pass",
        "direct_stage": "synthetic_integration_passed",
        "drawing_canvas_prerequisite": "component_pass",
        "active_content_implementation": "pass",
        "synthetic_security_corpus": "pass",
        "actual_target": "not_run",
        "p08_08": "implementation_complete_evidence_not_green",
        "p08_08_green": False,
        "p08": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")
    if not isinstance(contract.get("failure_policy"), list) or len(contract["failure_policy"]) != 12:
        errors.append("failure_policy")

    source_count = validate_sources(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok, official_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok, official_ok)


def expected_claims(with_tests: bool) -> dict[str, Any]:
    claims: dict[str, Any] = {
        "package_inventory_implemented": True,
        "activation_denial_implemented": True,
        "opaque_binary_preservation_check": True,
    }
    if with_tests:
        claims |= {
            "focused_rust_security_tests": "10/10 PASS",
            "malicious_zip_regression_tests": "8/8 PASS",
        }
    claims |= {
        "synthetic_security_corpus_pass": True,
        "actual_security_corpus": False,
        "actual_hwpx": False,
        "actual_hangul": False,
        "save_reopen": False,
        "property_readback": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p08_08_implementation_complete": True,
        "p08_08_green": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }
    return claims


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
            if relative.endswith("active_content.rs") and any(
                marker in text for marker in ("ShellExecute", "CreateProcess", "HAction")
            ):
                errors.append("activation_surface")
            if relative.endswith("reader.rs") and (
                "0xD0, 0xCF, 0x11, 0xE0" in text[text.index("fn nested_signature"): ]
            ):
                errors.append("cfb_still_nested")
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
        and public.get("qualification_boundary") == "static_names_attributes_and_enums_only"
    )
    if not official_ok:
        errors.append("qualification_official")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("claims") != expected_claims(with_tests=False):
        errors.append("qualification_claims")
    tests = value.get("tests")
    if not isinstance(tests, dict) or tests != {
        "focused_rust_security": "10/10 PASS",
        "malicious_zip_regression": "8/8 PASS",
        "package_kind": "in_memory_synthetic_hwpx",
        "network_used": False,
        "licensed_application_used": False,
    }:
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
        MIGRATION: ("There is no accepted v0", "fail closed", "no migration switch"),
        POLICY: (
            "synthetic_security_corpus_pass",
            "PreservePassive describes byte handling",
            "p08_08_green=false",
        ),
        REPORT: (
            "10/10 PASS",
            "in memory from synthetic fixtures",
            "actual_hangul=false",
        ),
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
        "schema_version": "hwpx-agent.p08-active-content-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "official_source_locks_verified": official,
        "task": "P08-08",
        "direct_stage": "synthetic_integration_passed" if not unique else "not_proven",
        "synthetic_security_corpus": "pass" if not unique else "not_proven",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "p08_08_implementation_complete": not unique,
        "p08_08_green": False,
        "p08": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    value = validate()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if value["state"] == "pass" else 1)
