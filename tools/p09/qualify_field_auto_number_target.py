#!/usr/bin/env python3
"""Hash-bound read-only qualification of the existing P09-17 target attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from inspect_field_auto_number_target import bounded_bytes, inspect, sha256

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "hwpx-agent.p09-17-field-auto-number-target-qualification/v1"
TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
    "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
}
EXPECTED_FIELDS = [
    {"feature_id": "REF-006", "case_id": "P09-17-C01", "native_type": "PAGE", "number": 9},
    {"feature_id": "REF-008", "case_id": "P09-17-C02", "native_type": "PICTURE", "number": 2},
    {"feature_id": "REF-008", "case_id": "P09-17-C03", "native_type": "TABLE", "number": 3},
    {"feature_id": "REF-008", "case_id": "P09-17-C04", "native_type": "EQUATION", "number": 4},
]
LIFECYCLE_KEYS = (
    "first_open", "first_save", "pdf_export", "fresh_reopen", "fresh_reopen_save",
    "fresh_reopen_pdf_export",
)
SOURCE_FILES = (
    "tools/p09/inspect_field_auto_number_target.py",
    "tools/p09/qualify_field_auto_number_target.py",
    "tools/p09/tests/test_field_auto_number_target_oracle.py",
    "tools/p09/tests/test_field_auto_number_target_qualification.py",
    "crates/hwpx-package/examples/p09_17_field_auto_number_target_fixture.rs",
    "implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1",
)


def duplicate_guard(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def digest(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("digest_invalid")
    return value


def checked_json(path: Path, expected: str):
    data = bounded_bytes(path, 128 * 1024)
    if sha256(data) != digest(expected):
        raise ValueError("evidence_digest_mismatch")
    try:
        value = json.loads(data, object_pairs_hook=duplicate_guard)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("evidence_json_invalid") from error
    if not isinstance(value, dict):
        raise ValueError("evidence_shape_invalid")
    return value


def verify_manifest(value):
    if (
        value.get("schema_version") != "hwpx-agent.p09-17-field-auto-number-target-fixture/v1"
        or value.get("target_profile") != TARGET
        or value.get("input_file") != "p09-17-field-auto-number-input.hwpx"
        or value.get("field_projection") != EXPECTED_FIELDS
        or any(type(item.get("number")) is not int for item in value["field_projection"])
        or value.get("static_evidence") != {
            "retry_package_byte_exact": True,
            "stale_source_rejected_without_output": True,
            "complete_package_hwpx": True,
        }
    ):
        raise ValueError("fixture_manifest_profile_mismatch")
    digest(value.get("input_package_sha256"))
    digest(value.get("input_section_sha256"))
    operations = value.get("operations")
    if not isinstance(operations, list) or len(operations) != 5:
        raise ValueError("fixture_operations_mismatch")
    expected = [
        (item["feature_id"], item["case_id"],
         "ref.field_page_number" if item["feature_id"] == "REF-006" else "ref.field_object_number",
         "insert", 1, 0) for item in EXPECTED_FIELDS
    ] + [("REF-009", "P09-17-C05", "ref.field_update", "update_numeric_result", 0, 1)]
    previous = None
    for operation, identity in zip(operations, expected):
        if not isinstance(operation, dict) or tuple(operation.get(key) for key in (
            "feature_id", "case_id", "capability_id", "operation", "inserted_auto_numbers",
            "updated_auto_numbers",
        )) != identity:
            raise ValueError("fixture_operations_mismatch")
        for key in (
            "plan_sha256", "source_section_sha256", "output_section_sha256",
            "source_state_sha256", "target_state_sha256", "target_document_flow_sha256",
        ):
            digest(operation.get(key))
        if previous is not None and (
            previous["output_section_sha256"] != operation["source_section_sha256"]
            or previous["target_state_sha256"] != operation["source_state_sha256"]
        ):
            raise ValueError("fixture_operation_chain_mismatch")
        previous = operation
    if operations[-1]["output_section_sha256"] != value["input_section_sha256"]:
        raise ValueError("fixture_final_section_mismatch")


def verify_trace(value, manifest):
    target = {**TARGET, "prog_id": "HWPFrame.HwpObject.2"}
    if (
        value.get("schema_version") != "hwpx-agent.p09-17-field-auto-number-target-trace/v1"
        or value.get("target") != target
        or value.get("input_sha256") != manifest["input_package_sha256"]
        or value.get("input_bytes") != manifest["input_package_bytes"]
        or value.get("state") != "pass"
        or any(value.get(key) != "pass" for key in LIFECYCLE_KEYS)
        or value.get("quit_invoked") is not True
        or type(value.get("remaining_hwp_process_count")) is not int
        or value.get("remaining_hwp_process_count") != 0
        or value.get("failed_phase") is not None
        or value.get("error_code") is not None
    ):
        raise ValueError("lifecycle_trace_mismatch")
    for key in (
        "raw_document_text_present", "user_document_scanned", "external_network_invoked",
        "registry_or_system_setting_changed", "computer_use_click_or_type_invoked",
    ):
        if value.get(key) is not False:
            raise ValueError("lifecycle_privacy_mismatch")
    if value.get("security_module") != {
        "name": "FilePathCheckerModuleExample",
        "sha256": "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6",
        "preflight_state": "pass",
    }:
        raise ValueError("lifecycle_security_preflight_mismatch")
    sessions = value.get("sessions")
    if not isinstance(sessions, list) or len(sessions) != 2:
        raise ValueError("lifecycle_sessions_mismatch")
    pids = []
    for session, label in zip(sessions, ("save", "reopen")):
        if (
            not isinstance(session, dict) or session.get("label") != label
            or session.get("version") != TARGET["build"]
            or type(session.get("register_module_return")) is not bool
            or not isinstance(session.get("process"), dict)
            or session["process"].get("executable_sha256") != TARGET["executable_sha256"]
        ):
            raise ValueError("lifecycle_session_identity_mismatch")
        pid = session["process"].get("process_id")
        if type(pid) is not int or pid <= 0:
            raise ValueError("lifecycle_process_identity_mismatch")
        pids.append(pid)
    if len(set(pids)) != 2:
        raise ValueError("fresh_session_not_independent")


def qualify(manifest_path: Path, manifest_digest: str, attempt: Path, trace_digest: str,
            *, root: Path = ROOT):
    manifest_path.resolve(strict=True).relative_to((root / "fixtures/target-build").resolve())
    attempt.resolve(strict=True).relative_to((root / "implementation/p09/evidence/private").resolve())
    manifest = checked_json(manifest_path, manifest_digest)
    verify_manifest(manifest)
    trace = checked_json(attempt / "target-trace.json", trace_digest)
    verify_trace(trace, manifest)
    projection = [{"native_type": item["native_type"], "number": item["number"]}
                  for item in EXPECTED_FIELDS]
    input_result = inspect(manifest_path.parent / manifest["input_file"],
                           manifest["input_package_sha256"], expected_projection=projection)
    if (
        input_result["state"] != "pass"
        or input_result["package_bytes"] != manifest["input_package_bytes"]
        or input_result["section_sha256"] != manifest["input_section_sha256"]
    ):
        raise ValueError("input_fixture_projection_mismatch")
    saved = inspect(attempt / "saved.hwpx", digest(trace.get("output_sha256")),
                    expected_projection=projection)
    reopened = inspect(attempt / "reopened.hwpx", digest(trace.get("reopened_sha256")),
                       expected_projection=projection)
    if saved["package_bytes"] != trace.get("output_bytes") or reopened["package_bytes"] != trace.get("reopened_bytes"):
        raise ValueError("saved_package_size_mismatch")
    pdfs = {}
    for filename, prefix in (("saved.pdf", "pdf"), ("reopened.pdf", "reopened_pdf")):
        data = bounded_bytes(attempt / filename, 32 * 1024 * 1024)
        if (not data.startswith(b"%PDF-") or sha256(data) != digest(trace.get(prefix + "_sha256"))
                or len(data) != trace.get(prefix + "_bytes")):
            raise ValueError("pdf_identity_mismatch")
        pdfs[filename] = {"sha256": sha256(data), "bytes": len(data), "signature": "pass"}
    cases = []
    for index, expected in enumerate(EXPECTED_FIELDS):
        actual_saved = saved["projection"][index]["number"]
        actual_reopened = reopened["projection"][index]["number"]
        matched = actual_saved == actual_reopened == expected["number"]
        cases.append({
            **expected, "input_number": input_result["projection"][index]["number"],
            "saved_number": actual_saved, "reopened_number": actual_reopened,
            "cached_result_preservation": "pass" if matched else "fail",
            "application_recalculation": "not_run", "render": "not_run",
            "automation": "not_run", "differential": "not_run", "gate_state": "non_green",
        })
    cases.append({
        "feature_id": "REF-009", "case_id": "P09-17-C05",
        "direct_numeric_result_update": "pass", "cached_result_preservation": cases[0]["cached_result_preservation"],
        "application_recalculation": "not_run", "render": "not_run",
        "automation": "not_run", "differential": "not_run", "gate_state": "non_green",
    })
    matched = all(case["cached_result_preservation"] == "pass" for case in cases)
    return {
        "schema_version": SCHEMA, "task": "P09-17", "target": TARGET,
        "state": "partial_non_green" if matched else "failed_semantic_non_green",
        "manifest_sha256": manifest_digest, "lifecycle_trace_sha256": trace_digest,
        "source_sha256": {relative: sha256(bounded_bytes(root / relative, 2 * 1024 * 1024))
                          for relative in SOURCE_FILES},
        "input": input_result, "saved": saved, "reopened": reopened, "pdf_identity": pdfs,
        "lifecycle": {key: trace[key] for key in LIFECYCLE_KEYS},
        "register_module_returns": [session["register_module_return"] for session in trace["sessions"]],
        "remaining_hwp_process_count_at_run": trace["remaining_hwp_process_count"],
        "cases": cases,
        "claims": {
            "complete_generated_package": True, "historical_exact_target_lifecycle": True,
            "cached_result_preservation": matched, "object_number_target_qualified": False,
            "reference_update": "not_run", "render": "not_run", "automation": "not_run",
            "differential": "not_run", "green_rows": 0, "p09_complete": False,
            "production_ready": False, "product_complete": False,
        },
        "privacy": {"absolute_private_paths": False, "raw_document_text_present": False,
                    "user_document_scanned": False, "external_network_invoked": False},
    }


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--expected-trace-sha256", required=True)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path)
    output.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        result = qualify(args.manifest, args.expected_manifest_sha256, args.attempt,
                         args.expected_trace_sha256)
        encoded = canonical_bytes(result)
        if args.output is not None:
            destination = args.output.absolute()
            destination.parent.resolve(strict=True).relative_to((ROOT / "implementation/p09/evidence").resolve())
            if any(item.is_symlink() or item.is_junction() for item in (destination, *destination.parents)):
                raise ValueError("qualification_output_link_rejected")
            if "private" in destination.relative_to(ROOT).parts:
                raise ValueError("qualification_output_private_rejected")
            with destination.open("xb") as handle:
                handle.write(encoded)
        if args.verify is not None and bounded_bytes(args.verify, 128 * 1024) != encoded:
            raise ValueError("qualification_record_mismatch")
    except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code}, sort_keys=True))
        return 2
    # 명령의 완료와 의미 검증 성공을 구분한다. 재현된 실패도 증거 기록 검증은 성공할 수 있다.
    print(json.dumps({"state": "pass", "qualification_state": result["state"],
                      "qualification_sha256": hashlib.sha256(encoded).hexdigest(),
                      "semantic_failures": sum(case["cached_result_preservation"] == "fail"
                                               for case in result["cases"]),
                      "green_rows": 0, "p09_complete": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
