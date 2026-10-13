"""Exact r5 source plus one streaming XML delta; original Job/GO/pressure unchanged."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_source_stage_profile as profile
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

parent = profile.parent
maintenance = profile.maintenance
bounded = profile.bounded
SELF = "tools/p09/run_xml_roundtrip_regression.py"
TEST = "tools/p09/tests/test_xml_roundtrip_regression.py"
XML = "crates/hwpx-package/src/preserving_xml.rs"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-streaming-xml-roundtrip-r6/source-preimages.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-149-streaming-xml-roundtrip-candidate.run01.v1.json"
PARENT_PIN = {"path": profile.CANDIDATE, "bytes": 1483,
    "sha256": "e06fe91a38c0b63abf5de077e46cb4a092e7eb03058e5a237c887f16ecbcfb5e"}
XML_TASK = "xml-roundtrip-tests"
XML_ARGS = ["test", "-p", "hwpx-package", "--lib"]
XML_FILTER = "preserving_xml::tests::"
XML_NAMES = frozenset(XML_FILTER + name for name in (
    "preserves_every_accepted_token_byte_and_digest",
    "preserves_utf8_bom_as_an_explicit_non_markup_token",
    "resolves_rebound_element_and_attribute_namespaces",
    "builds_parent_child_sibling_and_matching_tag_index",
    "inherits_safe_xml_fail_closed_policy_and_codes",
    "preserving_parser_keeps_finite_safe_reader_limits",
    "checked_spans_reject_bounds_order_and_utf8_splits",
    "streaming_round_trip_matches_allocating_oracle_for_all36_sources",
    "streaming_round_trip_rejects_token_omission_duplication_reordering_and_gaps",
    "streaming_round_trip_preserves_invalid_span_precedence_after_byte_mismatch",
    "streaming_round_trip_checks_digest_when_all_token_bytes_still_equal",
    "streaming_round_trip_keeps_equal_bytes_from_different_span_positions",
    "streaming_round_trip_preserves_large_unicode_references_bom_and_comments",
))
TASKS = (XML_TASK, profile.TASK, *parent.CASES)


def declared_sources(candidate, archive, expected):
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-streaming-xml-roundtrip-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == parent.contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == PARENT_PIN
        and candidate.get("preimage_archive") == ARCHIVE, "XML_CANDIDATE_SCOPE")
    deltas = parent.contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == {XML} and XML in expected and deltas[XML] != expected[XML],
        "XML_EXACT_SOURCE_DELTA_REQUIRED")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("baseline_build_pin") == parent.contract.CURRENT_BUILD_PIN
        and archive.get("parent_candidate_pin") == PARENT_PIN and len(archive.get("files", [])) == 1,
        "XML_PREIMAGE_SCOPE")
    original = archive["files"][0]
    data = base64.b64decode(original["base64"], validate=True)
    maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"]
        and {key: original[key] for key in ("path", "bytes", "sha256")} == expected[XML],
        "XML_WHOLE_ORIGINAL_SOURCE_DRIFT")
    return {**expected, **deltas}


def load_binding(windows, task):
    maintenance.require(task in TASKS, "XML_TASK_SCOPE")
    expected = profile.load_binding(windows)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(profile.CANDIDATE) == PARENT_PIN, "XML_PARENT_BYTE_DRIFT")
    expected = declared_sources(reader.json(CANDIDATE), reader.json(ARCHIVE), expected)
    expected.update({name: reader.pin(name) for name in (SELF, TEST, ARCHIVE, CANDIDATE)})
    if task == XML_TASK:
        source = reader.text(XML)
        maintenance.require(reader.pin(XML) == expected[XML], "XML_TEST_SOURCE_DRIFT")
        names = frozenset(XML_FILTER + name for name in
            re.findall(r"(?m)^    #\[test\]\s+fn ([A-Za-z_][A-Za-z0-9_]*)", source))
        maintenance.require(names == XML_NAMES, "XML_COMPLETE_COMPONENT_INVENTORY")
        modules = (XML,)
    elif task == profile.TASK:
        names, modules = (), ()
    else:
        def read(name):
            maintenance.require(name in expected and reader.pin(name) == expected[name], "XML_PARENT_TEST_SOURCE_DRIFT")
            return reader.text(name)
        names, modules = parent.recursive_names(read, task)
        maintenance.require(len(names) == parent.CASES[task][2], "XML_COMPLETE_PARENT_TARGET_INVENTORY")
    reader.finish()
    return expected, names, modules


def validate_xml_output(output):
    maintenance.require(isinstance(output, str) and len(output.encode()) <= maintenance.POLICY["output_limit_bytes_per_stream"],
        "XML_OUTPUT_BUDGET")
    running = re.findall(r"(?m)^running ([0-9]+) tests$", output)
    names = re.findall(r"(?m)^test ([A-Za-z0-9_:]+) \.\.\. ok$", output)
    summaries = re.findall(r"(?m)^test result: ok\. ([0-9]+) passed; 0 failed; 0 ignored; 0 measured; ([0-9]+) filtered out;", output)
    maintenance.require(running == [str(len(XML_NAMES))] and len(names) == len(XML_NAMES)
        and frozenset(names) == XML_NAMES and len(summaries) == 1
        and summaries[0][0] == str(len(XML_NAMES)), "XML_COMPLETE_COMPONENT_RESULTS_REQUIRED")
    return int(summaries[0][1])


def annotate(result, task):
    maintenance.require(isinstance(result, dict) and result.get("task") == task, "XML_RECEIPT_SCOPE")
    result.update(source_variant="streaming-xml-r6", baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD",
        optimization_candidate=CANDIDATE, product_complete=False, P09_gate="OPEN",
        signed_SQL_native_or_Gate_qualified=False, PC_freeze_resolved=False, statistical_speedup_proven=False)
    return result


def run_xml(destination, expected, maximum_seconds):
    original_pins, original_capture, original_dump = maintenance.pins, bounded.BoundedProcessCapture, json.dump
    captures = []
    class XmlCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.outside_component_filtered = None
            captures.append(self)
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                self.outside_component_filtered = validate_xml_output(output)
            return output, errors
    def pins(checkpoint=None):
        return parent.require_pins(original_pins(checkpoint), expected)
    def write(result, stream, **kwargs):
        annotate(result, XML_TASK)
        filtered = captures[-1].outside_component_filtered if captures else None
        if result.get("state") == "PASS_SCOPED_NOT_GATE" and (filtered is None
                or result.get("tests_passed") != len(XML_NAMES)):
            result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "XML_COMPONENT_RESULT_MISSING"
        result.update(qualification="COMPLETE_XML_COMPONENT_ONLY_NOT_WHOLE_LIBRARY_OR_GATE",
            expected_test_count=len(XML_NAMES), source_test_names=sorted(XML_NAMES),
            outside_component_filtered=filtered,
            whole_library_qualified=False, original7_XML_tests_retained=True, new_XML_regressions=6)
        return original_dump(result, stream, **kwargs)
    sources = list(dict.fromkeys(maintenance.SOURCES + list(expected)))
    with patch.object(maintenance, "__file__", str(maintenance.ROOT / SELF)), \
            patch.object(maintenance, "TASKS", {XML_TASK: XML_ARGS}), patch.object(maintenance, "SOURCES", sources), \
            patch.object(maintenance, "pins", pins), patch.object(bounded, "BoundedProcessCapture", XmlCapture), \
            patch.object(json, "dump", write):
        return maintenance.run(XML_TASK, destination, maximum_seconds)


def require_duration(task, seconds):
    maximum = 1200 if task == "stored-form-tests" else 180
    maintenance.require(task in TASKS and type(seconds) is int and 30 <= seconds <= maximum, "XML_DURATION_SCOPE")


def run_owned(destination, expected, names, modules, task, maximum_seconds):
    require_duration(task, maximum_seconds)
    if task == XML_TASK:
        return run_xml(destination, expected, maximum_seconds)
    original_dump = json.dump
    def write(result, stream, **kwargs):
        return original_dump(annotate(result, task), stream, **kwargs)
    with patch.object(json, "dump", write):
        if task == profile.TASK:
            return profile.run_owned(destination, expected, maximum_seconds)
        # The declared r6 binding above supplies every fresh source pin. Reuse
        # the original full-target runner and its already-reviewed duration
        # scope unchanged, then label the final receipt with the actual r6.
        return parent.run_owned(destination, expected, names, maximum_seconds,
            task, modules, "anchor-prefix-r4")


def run_worker():
    original_call = subprocess.call
    def component_call(arguments, **kwargs):
        expected = [*XML_ARGS, "--locked", "--offline", "--jobs", "1", "--color=never",
            "--target-dir", str(maintenance.TARGET), "--", "--test-threads=1"]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == expected
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "XML_WORKER_ARGUMENT_SCOPE")
        return original_call([*arguments[:-1], XML_FILTER, arguments[-1]], **kwargs)
    with patch.object(maintenance, "TASKS", {XML_TASK: XML_ARGS}), patch.object(subprocess, "call", component_call):
        return maintenance.worker(XML_TASK)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--task", choices=TASKS, default=XML_TASK)
    parser.add_argument("--maximum-seconds", type=int, default=180)
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    maintenance.require(Path.cwd().resolve() == maintenance.ROOT, "XML_ROOT_SCOPE")
    require_duration(args.task, args.maximum_seconds)
    windows = maintenance.Windows()
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-streaming-xml-roundtrip.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(windows, args.task)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_xml_roundtrip_regression import XmlRoundtripRegressionTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(name) for name in (SELF, TEST, XML, ARCHIVE)]
    with patch("subprocess.Popen", side_effect=AssertionError("XML_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("XML_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("XML_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(XmlRoundtripRegressionTests))
    reader.finish()
    failed = sorted({test.id().split(".")[-1] for test, _ in result.failures + result.errors + result.skipped})
    passed = result.testsRun == 10 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_XML_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun - len(failed), "failed_tests": failed,
        "source_freeze": freeze, "source_freeze_exact_after": True, "Cargo_SQL_native_executed": False,
        "product_complete": False, "P09_gate": "OPEN"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--owned-worker", "--task", XML_TASK]:
        raise SystemExit(run_worker())
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "XML_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
