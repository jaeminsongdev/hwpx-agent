#!/usr/bin/env python3
"""Read-only strict native trace/artifact binding; does not launch COM or Hancom."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import inspect_native_form_diagnostic_fixture as prepared

q = prepared.q
public = prepared.public
ROOT = prepared.ROOT
previous = public.preparation.predecessor
PREPARATION = "implementation/p09/evidence/p09-35-native-form-diagnostic-preparation.current-2020.v1.json"
PREPARATION_SHA = "9cedac0887e49f545a71dec17620ebdd1676b8266081bde042cbfa9723331a44"
MANIFEST = "fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json"
MANIFEST_SHA = "ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750"
SOURCES = ("tools/p09/qualify_native_form_diagnostic_batch.py", "tools/p09/tests/test_native_form_diagnostic_batch.py",
           "implementation/p09/P09-36_NATIVE_FORM_DIAGNOSTIC_BINDING_POLICY.md")
ARTIFACTS = {
    "saved.hwpx": ("output_sha256", "output_bytes", 4 * 1024 * 1024),
    "reopened.hwpx": ("reopened_sha256", "reopened_bytes", 4 * 1024 * 1024),
    "saved.pdf": ("pdf_sha256", "pdf_bytes", 32 * 1024 * 1024),
    "reopened.pdf": ("reopened_pdf_sha256", "reopened_pdf_bytes", 32 * 1024 * 1024),
}
TRACE_KEYS = {"schema_version", "state", "started_at_utc", "completed_at_utc", "target", "input_sha256", "input_bytes",
              "security_module", "sessions", *q.shared.lifecycle.LIFECYCLE_KEYS,
              *(key for pair in ARTIFACTS.values() for key in pair[:2]), "quit_invoked", "remaining_hwp_process_count",
              "failed_phase", "error_code", "raw_document_text_present", "user_document_scanned", "external_network_invoked",
              "registry_or_system_setting_changed", "computer_use_click_or_type_invoked"}
MISSING = {"complete_public_reader_or_policy_binding": "not_run", "error_code": "native_output_missing", "green_rows": 0}


def utc(value):
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?(?:Z|\+00:00)", value):
        raise ValueError("diagnostic_trace_utc_invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("diagnostic_trace_utc_invalid") from error
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("diagnostic_trace_utc_invalid")
    # .NET UTC receipts have 100 ns precision; datetime alone truncates digit 7.
    fraction = re.search(r"\.(\d{1,7})(?:Z|\+00:00)$", value)
    tick = int(fraction.group(1).ljust(7, "0")[-1]) if fraction else 0
    return parsed, tick


def verify_case_trace(trace, row):
    if type(trace) is not dict or set(trace) != TRACE_KEYS:
        raise ValueError("diagnostic_trace_shape_invalid")
    if type(row["package_bytes"]) is not int or not 0 < row["package_bytes"] <= 4 * 1024 * 1024:
        raise ValueError("diagnostic_input_bytes_invalid")
    q.shared.lifecycle.digest(row["package_sha256"])
    if type(trace["input_bytes"]) is not int:
        raise ValueError("diagnostic_trace_input_type_invalid")
    started, completed = utc(trace["started_at_utc"]), utc(trace["completed_at_utc"])
    if completed < started:
        raise ValueError("diagnostic_trace_time_order_invalid")
    if type(trace["sessions"]) is not list or not 0 < len(trace["sessions"]) <= 2:
        raise ValueError("diagnostic_sessions_shape_invalid")
    for session in trace["sessions"]:
        if type(session) is not dict or set(session) != {"label", "version", "register_module_return", "process"}:
            raise ValueError("diagnostic_session_shape_invalid")
        process = session["process"]
        if type(process) is not dict or set(process) != {"process_id", "session_id", "executable_sha256", "command_line_sha256"}:
            raise ValueError("diagnostic_process_shape_invalid")
        if type(process["session_id"]) is not int or process["session_id"] < 0:
            raise ValueError("diagnostic_windows_session_invalid")
        q.shared.lifecycle.digest(process["command_line_sha256"])
    passed = q.shared.verify_attempt(trace, {"output_package_sha256": row["package_sha256"], "output_package_bytes": row["package_bytes"]})
    if passed:
        for digest_key, bytes_key, maximum in ARTIFACTS.values():
            q.shared.lifecycle.digest(trace[digest_key])
            if type(trace[bytes_key]) is not int or not 0 < trace[bytes_key] <= maximum:
                raise ValueError("diagnostic_trace_artifact_bytes_invalid")
    return passed


def session_inventory(records, expected_count):
    if type(records) is not list or type(expected_count) is not int or len(records) != expected_count or not 0 < expected_count <= 15:
        raise ValueError("diagnostic_trace_inventory_invalid")
    cases, pids, windows_sessions = [], [], []
    previous_completed = None
    for record in records:
        row, _, trace, passed = record
        if type(passed) is not bool or verify_case_trace(trace, row) is not passed:
            raise ValueError("diagnostic_trace_lifecycle_coerced")
        cases.append(row["case_id"])
        started = utc(trace["started_at_utc"])
        if previous_completed is not None and started < previous_completed:
            raise ValueError("diagnostic_cases_not_sequential")
        previous_completed = utc(trace["completed_at_utc"])
        pids.extend(session["process"]["process_id"] for session in trace["sessions"])
        windows_sessions.extend(session["process"]["session_id"] for session in trace["sessions"])
    if len(set(cases)) != expected_count or len(set(pids)) != len(pids) or len(set(windows_sessions)) != 1:
        raise ValueError("diagnostic_all_sessions_not_independent")
    return {"case_count": expected_count, "owned_session_count": len(pids),
            "passed_lifecycle_cases": sum(record[3] for record in records), "failed_first_open_cases": sum(not record[3] for record in records),
            "all_cases_sequential": True, "all_owned_process_ids_unique": True}


def artifact_snapshot(directory, trace, passed):
    if type(passed) is not bool:
        raise ValueError("diagnostic_artifact_lifecycle_coerced")
    q.shared.within(directory, directory)
    if not directory.is_dir():
        raise ValueError("diagnostic_attempt_directory_invalid")
    expected = {"target-trace.json", *ARTIFACTS} if passed else {"target-trace.json"}
    if {path.name for path in directory.iterdir()} != expected:
        raise ValueError("diagnostic_attempt_artifact_inventory_invalid")
    raw_trace = public.bounded_bytes(directory / "target-trace.json", 128 * 1024)
    actual_trace = json.loads(raw_trace, object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    q.exact(actual_trace, trace, "diagnostic_trace_snapshot_changed")
    result = {}
    for name, (digest_key, bytes_key, maximum) in ARTIFACTS.items() if passed else ():
        raw = public.checked(directory / name, trace[digest_key], maximum)
        q.exact(len(raw), trace[bytes_key], "diagnostic_native_artifact_bytes_mismatch")
        if name.endswith(".pdf") and not raw.startswith(b"%PDF-"):
            raise ValueError("diagnostic_native_pdf_signature_invalid")
        result[name] = {"sha256": q.sha(raw), "bytes": len(raw)}
    return result


def dependency_guard(root=ROOT):
    value = q.shared.lifecycle.checked_json(root / PREPARATION, PREPARATION_SHA)
    for path, digest in value["source_sha256"].items():
        public.checked(root / path, digest)
    prepared.authority(root)
    q.shared.lifecycle.checked_json(root / MANIFEST, MANIFEST_SHA)
    return value


def own_sources(root=ROOT):
    return {path: q.sha(public.bounded_bytes(root / path, 2 * 1024 * 1024)) for path in SOURCES}


def preparation(root=ROOT):
    value = dependency_guard(root)
    actual = prepared.qualify(root / MANIFEST, MANIFEST_SHA, root)
    q.exact(actual, value, "diagnostic_preparation_capsule_not_reproduced")
    return q.shared.lifecycle.checked_json(root / MANIFEST, MANIFEST_SHA)


def attempt_paths(prefix, root=ROOT):
    if type(prefix) is not str or re.fullmatch(r"[a-z0-9-]{1,40}", prefix) is None:
        raise ValueError("diagnostic_batch_prefix_invalid")
    return [root / "implementation/p09/evidence/private" / f"p09-17-field-auto-number-target-{prefix}-c{i+1:02}-attempt01" for i in range(15)]


def traces(manifest, prefix, root=ROOT):
    if type(manifest["cases"]) is not list or len(manifest["cases"]) != 15:
        raise ValueError("diagnostic_complete_case_inventory_invalid")
    records, source_pins = [], {}
    for index, (row, path) in enumerate(zip(manifest["cases"], attempt_paths(prefix, root), strict=True)):
        q.exact(row["case_id"], f"P09-35-C{index+1:02}", "diagnostic_trace_case_identity_invalid")
        q.shared.within(path, root / "implementation/p09/evidence/private")
        raw = public.bounded_bytes(path / "target-trace.json", 128 * 1024)
        trace = json.loads(raw, object_pairs_hook=q.shared.lifecycle.duplicate_guard)
        passed = verify_case_trace(trace, row)
        snapshot = artifact_snapshot(path, trace, passed)
        input_raw = public.checked((root / MANIFEST).parent / row["file"], row["package_sha256"], 4 * 1024 * 1024)
        q.exact(len(input_raw), row["package_bytes"], "diagnostic_trace_input_bytes_mismatch")
        source_pins[str((path / "target-trace.json").relative_to(root))] = q.sha(raw)
        source_pins.update({str((path / name).relative_to(root)): value["sha256"] for name, value in snapshot.items()})
        records.append((row, path, trace, passed))
    session_inventory(records, 15)
    return records, source_pins


def rust_observations(prefix, root=ROOT):
    attempt_paths(prefix, root)
    process = subprocess.run(["cargo", "run", "-p", "hwpx-package", "--example", "p09_35_native_form_diagnostic_fixture",
                              "--locked", "--offline", "--", "--inspect-native-batch", prefix], cwd=root, capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 256 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("diagnostic_actual_native_readback_failed")
    value = json.loads(process.stdout, object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    if type(value) is not dict:
        raise ValueError("diagnostic_native_observer_shape_invalid")
    expected = {"schema_version": "hwpx-agent.p09-native-form-diagnostic-readback/v1", "task": "P09-35",
                "qualification": "file_readback_only_native_trace_binding_required", "native_session_started": False,
                "raw_document_text_present": False, "absolute_private_paths_present": False, "green_rows": 0, "p09_complete": False}
    q.exact({k: v for k, v in value.items() if k != "cases"}, expected, "diagnostic_native_observer_claims_invalid")
    return value


def verify_rust(value, records):
    if type(value) is not dict or type(value.get("cases")) is not list:
        raise ValueError("diagnostic_native_observer_inventory_invalid")
    rows = value["cases"]
    if type(rows) is not list or len(rows) != len(records):
        raise ValueError("diagnostic_native_observer_inventory_invalid")
    for observed, (row, _, trace, passed) in zip(rows, records, strict=True):
        if type(observed) is not dict:
            raise ValueError("diagnostic_native_row_shape_invalid")
        if type(passed) is not bool:
            raise ValueError("diagnostic_native_lifecycle_coerced")
        q.exact(sorted(observed), ["case_id", "reopened", "saved"], "diagnostic_native_row_shape_invalid")
        q.exact(observed["case_id"], row["case_id"], "diagnostic_native_row_identity_invalid")
        for stage, digest_key, bytes_key in (("saved", "output_sha256", "output_bytes"), ("reopened", "reopened_sha256", "reopened_bytes")):
            item = observed[stage]
            if type(item) is not dict:
                raise ValueError("diagnostic_native_stage_shape_invalid")
            if not passed:
                q.exact(item, MISSING, "diagnostic_missing_native_stage_promoted")
                continue
            q.exact(item.get("package_sha256"), trace[digest_key], "diagnostic_native_readback_digest_unbound")
            q.exact(item.get("package_bytes"), trace[bytes_key], "diagnostic_native_readback_size_unbound")
            if item.get("complete_public_reader_or_policy_binding") == "fail":
                q.exact(item, {"complete_public_reader_or_policy_binding": "fail", "error_code": "complete_readback_failed",
                               "package_sha256": trace[digest_key], "package_bytes": trace[bytes_key], "green_rows": 0}, "diagnostic_native_failure_shape_invalid")
                continue
            keys = {"complete_public_reader", "complete_policy_binding", "package_sha256", "package_bytes", "target_state_sha256",
                    "target_controls_sha256", "document_flow_sha256", "complete_target_state_exact", "target_control_fingerprints_exact",
                    "document_flow_exact", "complete_package_bindings_exact", "green_rows"}
            q.exact(sorted(item), sorted(keys), "diagnostic_native_stage_shape_invalid")
            for key in ("complete_public_reader", "complete_policy_binding"):
                q.exact(item[key], "pass", "diagnostic_native_reader_state_invalid")
            q.exact(item["green_rows"], 0, "diagnostic_native_promoted_green")
            for key in ("target_state_sha256", "document_flow_sha256"):
                q.shared.lifecycle.digest(item[key])
            controls = item["target_controls_sha256"]
            if type(controls) is not list or len(controls) != row["controls"]:
                raise ValueError("diagnostic_native_control_inventory_invalid")
            for digest in controls:
                q.shared.lifecycle.digest(digest)
            for key in ("complete_target_state_exact", "target_control_fingerprints_exact", "document_flow_exact", "complete_package_bindings_exact"):
                if type(item[key]) is not bool:
                    raise ValueError("diagnostic_native_state_boolean_invalid")
            q.exact(item["complete_target_state_exact"], item["target_state_sha256"] == row["target_state_sha256"], "diagnostic_native_target_match_forged")
            q.exact(item["target_control_fingerprints_exact"], controls == row["target_controls_sha256"], "diagnostic_native_control_match_forged")
            q.exact(item["document_flow_exact"], item["document_flow_sha256"] == row["document_flow_sha256"], "diagnostic_native_flow_match_forged")


def qualify(prefix, root=ROOT):
    attempt_paths(prefix, root)
    before = own_sources(root)
    manifest = preparation(root)
    records, native_pins = traces(manifest, prefix, root)
    observed = rust_observations(prefix, root)
    verify_rust(observed, records)
    cases = []
    for actual, (row, path, trace, passed) in zip(observed["cases"], records, strict=True):
        input_raw = public.checked((root / MANIFEST).parent / row["file"], row["package_sha256"], 4 * 1024 * 1024)
        result = {"case_id": row["case_id"], "trace_sha256": q.sha(public.bounded_bytes(path / "target-trace.json", 128 * 1024)),
                  "lifecycle": "pass" if passed else "fail", "permission_click_attestation": "not_attested",
                  "register_module_returns": [session["register_module_return"] for session in trace["sessions"]],
                  "failed_phase": trace["failed_phase"], "error_code": trace["error_code"], "complete_public_readback": actual,
                  "pdf_identity": {name: data for name, data in artifact_snapshot(path, trace, passed).items() if name.endswith(".pdf")},
                  "saved": {"state": "not_run"}, "reopened": {"state": "not_run"}}
        if passed:
            for stage, digest_key in (("saved", "output_sha256"), ("reopened", "reopened_sha256")):
                raw = public.checked(path / f"{stage}.hwpx", trace[digest_key], 4 * 1024 * 1024)
                try:
                    result[stage] = q.compare_native(input_raw, raw)
                except (ValueError, KeyError, ET.ParseError, zipfile.BadZipFile):
                    result[stage] = {"state": "fail", "error_code": "independent_complete_projection_failed", "package_sha256": q.sha(raw)}
        cases.append(result)
    if before != own_sources(root):
        raise ValueError("diagnostic_binding_sources_changed")
    if native_pins != traces(manifest, prefix, root)[1]:
        raise ValueError("diagnostic_native_evidence_changed_during_verification")
    dependency_guard(root)
    return {"schema_version": "hwpx-agent.p09-native-form-diagnostic-bound-batch/v1", "task": "P09-36",
            "state": "actual_bound_whole_batch_non_green", "preparation_sha256": PREPARATION_SHA, "manifest_sha256": MANIFEST_SHA,
            "source_sha256": before, "native_evidence_sha256": native_pins, "cases": cases, "session_inventory": session_inventory(records, 15),
            "claims": {"actual_existing_trace_and_artifacts_verified": True, "actual_public_file_readback_bound": True,
                       "native_normalization_qualified": False, "native_color_name_repair_qualified": False,
                       "render": "not_run", "pdf_stability": "not_run", "product_differential": "not_run",
                       "production_routing_qualified": False, "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started_by_verifier": False, "trust_or_registry_changed": False}}


def preflight(root=ROOT):
    source_pins = own_sources(root)
    manifest = preparation(root)
    old = previous.verified_traces(root)
    historical_pins = {}
    for row, path, trace, passed in old:
        if verify_case_trace(trace, row) is not passed:
            raise ValueError("diagnostic_historical_trace_reverification_changed")
        snapshot = artifact_snapshot(path, trace, passed)
        historical_pins[str((path / "target-trace.json").relative_to(root))] = q.sha(public.bounded_bytes(path / "target-trace.json", 128 * 1024))
        historical_pins.update({str((path / name).relative_to(root)): value["sha256"] for name, value in snapshot.items()})
    previous.verified_traces(root)
    for path, digest in historical_pins.items():
        public.checked(root / path, digest, 32 * 1024 * 1024)
    dependency_guard(root)
    if source_pins != own_sources(root):
        raise ValueError("diagnostic_binding_sources_changed")
    return {"schema_version": "hwpx-agent.p09-native-form-diagnostic-binding-component/v1", "task": "P09-36",
            "state": "strict_trace_binding_preflight_only_not_new_native_execution", "source_sha256": source_pins,
            "preparation_sha256": PREPARATION_SHA, "prepared_case_count": len(manifest["cases"]),
            "historical_trace_reverification": session_inventory(old, 6),
            "historical_trace_and_artifact_sha256": historical_pins,
            "new_native_batch": {"state": "not_run", "cases": 15, "stages": 30},
            "claims": {"strict_input_trace_artifact_session_and_typed_hash_binding_implemented": True,
                       "historical_reverification_is_new_batch_proof": False, "new_native_target_execution": False,
                       "native_color_name_repair_qualified": False, "native_normalization_qualified": False,
                       "render": "not_run", "product_differential": "not_run", "production_routing_qualified": False,
                       "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "native_session_started": False, "trust_or_registry_changed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True); mode.add_argument("--preflight", action="store_true"); mode.add_argument("--prefix")
    group = parser.add_mutually_exclusive_group(); group.add_argument("--output", type=Path); group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = preflight() if args.preflight else qualify(args.prefix)
        raw = q.shared.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute(); q.shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if "private" in path.relative_to(ROOT).parts or path.is_symlink() or path.is_junction():
                raise ValueError("diagnostic_binding_public_evidence_boundary_invalid")
            with path.open("xb") as stream: stream.write(raw)
        if args.verify and public.bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("diagnostic_binding_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError, ET.ParseError, zipfile.BadZipFile) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "diagnostic_binding_verification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_sha256": q.sha(raw), "qualification_state": value["state"],
                      "native_session_started_by_verifier": False, "green_rows": 0, "p09_complete": False})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
