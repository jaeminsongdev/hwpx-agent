#!/usr/bin/env python3
"""Bind all six real native attempts, complete public readback and PDF stability."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import inspect_native_form_complete_fixture as prepared
from tools.p09 import qualify_click_here_update_target as click

ROOT = prepared.ROOT
shared = prepared.shared
GENERATOR = "crates/hwpx-package/examples/p09_32_native_form_target_fixture.rs"
GENERATOR_OLD = "3f970f6c8ad0d1d3eba4d73bccc862d23b32539ead32fa5914206ccacd053965"
ARCHIVE = "implementation/p09/source-archive/p09-32-pre-failed-attempt-support/p09_32_native_form_target_fixture.rs"
PREPARATION = "implementation/p09/evidence/p09-32-native-form-complete-preparation.current-2020.v1.json"
PREPARATION_SHA = "420d10fffa83bda333fe5711cd5d3e305f2bd0b9ac726980cc9054b3a6ff75f4"
MANIFEST = "fixtures/target-build/p09-32-native-form-target-20261002-01/output/fixture-manifest.json"
MANIFEST_SHA = "f07a8a73dbead998db253050d011ebe58ac331c42060b31c0c7a617a23ad8ef8"
PREFIX = "p09-32-20261002"
TRACE_SHA = (
    "9e92ff858e18df67ab3c37d8cb43d3cd5245b593cb56bb099a53c18324000da9",
    "05e7779d37591b0ee8c8d972b8151afc6a18cd1d14a41a06e755c77a7fbdc76d",
    "a429f3073468b0ca6d5169d8454f1456b0e17631743b7164dcd50760cdadcce7",
    "660540d5021d489f0c38e24bc715568b68f7bb25f144ab66aa329e4ee5941af5",
    "e488d8d0b8632c0687ba72036f183ed17c0299d5398648b72b5627ca24bd12a8",
    "942c638ce661166b30caaa451ff682ab66825b5c603cef924c6d2ed46cc46de7",
)
OLD = b'            let raw = bounded_native_bytes(&dir.join(format!("{stage}.hwpx")))?;\n'
NEW = b'''            let path = dir.join(format!("{stage}.hwpx"));
            if !path.exists() {
                row[stage] = serde_json::json!({"complete_public_reader_or_policy_binding":"not_run",
                    "error_code":"native_output_missing", "green_rows":0});
                continue;
            }
            let raw = bounded_native_bytes(&path)?;
'''
SOURCES = (
    "tools/p09/qualify_native_form_complete_batch.py",
    "tools/p09/tests/test_native_form_complete_batch.py",
    GENERATOR, ARCHIVE, *tuple(p for p in prepared.SOURCES if p != GENERATOR),
    "tools/p09/qualify_field_object_caption_target.py", "tools/p09/qualify_field_auto_number_target.py",
    "tools/p09/qualify_click_here_update_target.py", "tools/p08/object_target_oracle.py",
)


def source_bridge(root=ROOT):
    record = shared.lifecycle.checked_json(root / PREPARATION, PREPARATION_SHA)
    if record["source_sha256"].get(GENERATOR) != GENERATOR_OLD:
        raise ValueError("native_form_initial_generator_pin_invalid")
    old = prepared.output.export.checked(root / ARCHIVE, GENERATOR_OLD)
    current = prepared.output.export.bounded_bytes(root / GENERATOR, 2 * 1024 * 1024)
    if current.count(NEW) != 1 or old.count(OLD) != 1 or current.replace(NEW, OLD) != old:
        raise ValueError("native_form_readback_successor_delta_invalid")
    for path, digest in record["source_sha256"].items():
        prepared.output.export.checked(root / (ARCHIVE if path == GENERATOR else path), digest)
    actual = prepared.inspect(root / MANIFEST, MANIFEST_SHA, root)
    actual["source_sha256"] = record["source_sha256"]
    if shared.lifecycle.canonical_bytes(actual) != prepared.output.export.checked(root / PREPARATION, PREPARATION_SHA):
        raise ValueError("native_form_initial_preparation_reproduction_mismatch")
    return {"initial_preparation_sha256": PREPARATION_SHA, "initial_generator_sha256": GENERATOR_OLD,
            "current_generator_sha256": prepared.sha(current), "exact_archive_and_single_missing_output_delta": True,
            "predecessor_failed_output_is_not_run_not_pass": True}


def rust_observations(root=ROOT):
    process = subprocess.run(["cargo", "run", "-p", "hwpx-package", "--example", "p09_32_native_form_target_fixture",
                              "--locked", "--offline", "--", "--inspect-native-batch", PREFIX], cwd=root,
                             capture_output=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 128 * 1024 or len(process.stderr) > 1024 * 1024:
        raise ValueError("native_form_actual_public_readback_command_failed")
    value = json.loads(process.stdout, object_pairs_hook=shared.lifecycle.duplicate_guard)
    expected = {"schema_version": "hwpx-agent.p09-native-form-public-readback/v1", "task": "P09-32",
                "state": "actual_complete_public_readback_observations_non_green", "native_session_started": False,
                "raw_document_text_present": False, "absolute_private_paths_present": False, "green_rows": 0, "p09_complete": False}
    prepared.exact({k: v for k, v in value.items() if k != "cases"}, expected, "native_form_public_readback_claims_invalid")
    if type(value.get("cases")) is not list or len(value["cases"]) != 6:
        raise ValueError("native_form_public_readback_inventory_invalid")
    return value


def verified_traces(root=ROOT):
    manifest = shared.lifecycle.checked_json(root / MANIFEST, MANIFEST_SHA)
    traces = []
    ids = []
    for row, path, digest in zip(manifest["cases"], prepared.attempt_paths(PREFIX, root), TRACE_SHA, strict=True):
        shared.within(path, root / "implementation/p09/evidence/private")
        trace = shared.lifecycle.checked_json(path / "target-trace.json", digest)
        passed = shared.verify_attempt(trace, {"output_package_sha256": row["package_sha256"], "output_package_bytes": row["package_bytes"]})
        expected_files = {"target-trace.json", "saved.hwpx", "reopened.hwpx", "saved.pdf", "reopened.pdf"} if passed else {"target-trace.json"}
        if {p.name for p in path.iterdir()} != expected_files:
            raise ValueError("native_form_attempt_artifact_inventory_invalid")
        ids.extend(s["process"]["process_id"] for s in trace["sessions"])
        traces.append((row, path, trace, passed))
    if len(set(ids)) != len(ids) or len(ids) != 10:
        raise ValueError("native_form_all_attempt_sessions_not_independent")
    return traces


def verify_rust(value, traces):
    results = value["cases"]
    for result, (row, _, trace, passed) in zip(results, traces, strict=True):
        prepared.exact(sorted(result), ["case_id", "reopened", "saved"], "native_form_public_row_shape_invalid")
        prepared.exact(result["case_id"], row["case_id"], "native_form_public_row_identity_invalid")
        for stage, hash_key, bytes_key in (("saved", "output_sha256", "output_bytes"), ("reopened", "reopened_sha256", "reopened_bytes")):
            item = result[stage]
            if not passed:
                prepared.exact(item, {"complete_public_reader_or_policy_binding": "not_run", "error_code": "native_output_missing", "green_rows": 0},
                               "native_form_missing_output_promoted")
                continue
            keys = {"complete_public_reader", "complete_policy_binding", "package_sha256", "package_bytes", "controls",
                    "target_state_sha256", "document_flow_sha256", "complete_target_state_exact", "target_control_fingerprints_exact",
                    "document_flow_exact", "complete_package_bindings_exact", "green_rows"}
            prepared.exact(sorted(item), sorted(keys), "native_form_public_stage_shape_invalid")
            for key, expected in (("complete_public_reader", "pass"), ("complete_policy_binding", "pass"),
                                  ("package_sha256", trace[hash_key]), ("package_bytes", trace[bytes_key]), ("controls", 1), ("green_rows", 0)):
                prepared.exact(item[key], expected, "native_form_public_stage_identity_invalid")
            for key in ("complete_target_state_exact", "target_control_fingerprints_exact", "document_flow_exact", "complete_package_bindings_exact"):
                if type(item[key]) is not bool:
                    raise ValueError("native_form_public_stage_boolean_invalid")
            for key in ("target_state_sha256", "document_flow_sha256"):
                shared.lifecycle.digest(item[key])


def qualify(root=ROOT, *, render=True):
    bridge = source_bridge(root)
    before = {p: prepared.sha(prepared.output.export.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}
    traces = verified_traces(root)
    native = prepared.native_batch(root / MANIFEST, MANIFEST_SHA, PREFIX, root)
    actual = rust_observations(root)
    verify_rust(actual, traces)
    for record, rust, (row, path, trace, passed) in zip(native["cases"], actual["cases"], traces, strict=True):
        record["complete_public_readback"] = rust
        record["failed_trace_qualification"] = "not_applicable" if passed else "exact_input_target_first_open_failure_verified"
        record["actual_owned_sessions"] = len(trace["sessions"])
        record["register_module_returns"] = [s["register_module_return"] for s in trace["sessions"]]
        record["pdf_stability"] = {"state": "not_run"}
        if not passed:
            record["failed_phase"] = trace["failed_phase"]
            record["error_code"] = trace["error_code"]
            continue
        for name, hash_key, bytes_key, maximum in (("saved.hwpx", "output_sha256", "output_bytes", 4*1024*1024),
                                                 ("reopened.hwpx", "reopened_sha256", "reopened_bytes", 4*1024*1024),
                                                 ("saved.pdf", "pdf_sha256", "pdf_bytes", 32*1024*1024),
                                                 ("reopened.pdf", "reopened_pdf_sha256", "reopened_pdf_bytes", 32*1024*1024)):
            raw = prepared.output.export.checked(path / name, trace[hash_key], maximum)
            prepared.exact(len(raw), trace[bytes_key], "native_form_native_artifact_bytes_mismatch")
            if name.endswith(".pdf") and not raw.startswith(b"%PDF-"):
                raise ValueError("native_form_pdf_identity_invalid")
        if render:
            record["pdf_stability"] = click.pdf_comparison(path / "saved.pdf", path / "reopened.pdf")
        record["native_artifact_hashes"] = {name: trace[key] for name, key in (
            ("saved.hwpx", "output_sha256"), ("reopened.hwpx", "reopened_sha256"), ("saved.pdf", "pdf_sha256"), ("reopened.pdf", "reopened_pdf_sha256"))}
    if before != {p: prepared.sha(prepared.output.export.bounded_bytes(root / p, 2 * 1024 * 1024)) for p in SOURCES}:
        raise ValueError("native_form_batch_sources_changed")
    verified_traces(root)
    source_bridge(root)
    return {"schema_version": "hwpx-agent.p09-native-form-complete-qualification/v1", "task": "P09-32",
            "state": "whole_batch_observed_with_preserved_failures_non_green", "source_bridge": bridge,
            "source_sha256": before, "manifest_sha256": MANIFEST_SHA, "trace_sha256": list(TRACE_SHA),
            "cases": native["cases"], "actual_owned_session_count": 10, "passed_lifecycle_cases": 4, "failed_first_open_cases": 2,
            "claims": {"actual_native_batch_executed": True, "actual_complete_public_reader_executed": True,
                       "permission_click_attestation": "not_attested", "native_normalization_qualified": False,
                       "pdf_saved_reopened_stability_observed": render, "full_render_acceptance": "not_run",
                       "product_differential": "not_run", "production_routing_qualified": False,
                       "green_rows": 0, "p09_complete": False},
            "privacy": {"raw_document_text_present": False, "absolute_private_paths_present": False,
                        "trust_or_registry_changed": False, "computer_use_click_or_type_invoked": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        value = qualify()
        raw = shared.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute()
            shared.within(path.parent, ROOT / "implementation/p09/evidence")
            if path.is_symlink() or path.is_junction() or "private" in path.relative_to(ROOT).parts:
                raise ValueError("native_form_batch_public_boundary_invalid")
            with path.open("xb") as stream:
                stream.write(raw)
        if args.verify and prepared.output.export.bounded_bytes(args.verify, 512 * 1024) != raw:
            raise ValueError("native_form_batch_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError, click.pdf_oracle.OracleError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else "native_form_batch_qualification_failed"
        print(json.dumps({"state": "fail", "error_code": code})); return 2
    print(json.dumps({"state": "pass", "qualification_state": value["state"], "qualification_sha256": prepared.sha(raw),
                      "lifecycle_pass": 4, "first_open_fail": 2, "actual_owned_sessions": 10, "green_rows": 0})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
