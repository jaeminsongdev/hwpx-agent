"""One moved fresh-part buffer delta; retain r6 chain, full checks and owned limits."""
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_xml_roundtrip_regression as previous
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

maintenance, bounded = previous.maintenance, previous.bounded
SELF = "tools/p09/run_readback_buffer_regression.py"
TEST = "tools/p09/tests/test_readback_buffer_regression.py"
SOURCE = "crates/hwpx-package/src/document_import/fields/semantics/evaluation/output/readback.rs"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-moved-readback-buffer-r7/source-preimages.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-149-moved-readback-buffer-candidate.run01.v1.json"
PARENT_PIN = {"path": previous.CANDIDATE, "bytes": 1738,
    "sha256": "ec30cdc4344d1bca94e1de3f583cdd811fddc3822a08d958fd51623360f16343"}
UNIT = "readback-buffer-tests"
FILTER = "document_import::fields::semantics::evaluation::output::readback::tests::"
NAMES = frozenset(FILTER + name for name in (
    "unchanged_large_part_reuses_fresh_buffer_and_keeps_all_bytes",
    "all_valid_spans_values_and_empty_names_match_allocating_oracle",
    "reverse_edits_use_original_offsets_and_length_after_growth_and_shrink",
    "original_ascii_bounds_and_overlap_failures_are_not_weakened",
))
TASKS = (UNIT, *previous.TASKS)


def declared_sources(candidate, archive, expected):
    maintenance.require(isinstance(candidate, dict)
        and candidate.get("schema_version") == "hwpx-agent.p09-moved-readback-buffer-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == previous.parent.contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == PARENT_PIN
        and candidate.get("preimage_archive") == ARCHIVE, "READBACK_CANDIDATE_SCOPE")
    deltas = previous.parent.contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == {SOURCE} and SOURCE in expected
        and deltas[SOURCE] != expected[SOURCE], "READBACK_EXACT_DELTA_REQUIRED")
    maintenance.require(isinstance(archive, dict)
        and archive.get("schema_version") == "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("baseline_build_pin") == previous.parent.contract.CURRENT_BUILD_PIN
        and archive.get("parent_candidate_pin") == PARENT_PIN
        and len(archive.get("files", [])) == 1, "READBACK_PREIMAGE_SCOPE")
    original = archive["files"][0]
    data = base64.b64decode(original["base64"], validate=True)
    maintenance.require(len(data) == original["bytes"]
        and hashlib.sha256(data).hexdigest() == original["sha256"]
        and {key: original[key] for key in ("path", "bytes", "sha256")} == expected[SOURCE],
        "READBACK_WHOLE_PREIMAGE_DRIFT")
    return {**expected, **deltas}


def load_binding(windows, task):
    maintenance.require(task in TASKS, "READBACK_TASK_SCOPE")
    expected, names, modules = previous.load_binding(windows, previous.XML_TASK if task == UNIT else task)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(previous.parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(previous.CANDIDATE) == PARENT_PIN, "READBACK_PARENT_BYTE_DRIFT")
    expected = declared_sources(reader.json(CANDIDATE), reader.json(ARCHIVE), expected)
    expected.update({name: reader.pin(name) for name in (SELF, TEST, ARCHIVE, CANDIDATE)})
    if task == UNIT:
        source = reader.text(SOURCE)
        maintenance.require(reader.pin(SOURCE) == expected[SOURCE], "READBACK_UNIT_SOURCE_DRIFT")
        actual = frozenset(FILTER + name for name in
            re.findall(r"(?m)^    #\[test\]\s+fn ([A-Za-z_][A-Za-z0-9_]*)", source))
        maintenance.require(actual == NAMES, "READBACK_COMPLETE_UNIT_INVENTORY")
        names, modules = NAMES, (SOURCE,)
    reader.finish()
    return expected, names, modules


def annotate(result, task):
    maintenance.require(isinstance(result, dict) and result.get("task") == task, "READBACK_RECEIPT_SCOPE")
    result.update(source_variant="moved-readback-buffer-r7", optimization_candidate=CANDIDATE,
        product_complete=False, P09_gate="OPEN", signed_SQL_native_or_Gate_qualified=False,
        PC_freeze_resolved=False, statistical_speedup_proven=False,
        baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD")
    return result


def validate_output(output):
    maintenance.require(isinstance(output, str)
        and len(output.encode()) <= maintenance.POLICY["output_limit_bytes_per_stream"], "READBACK_OUTPUT_BUDGET")
    running = re.findall(r"(?m)^running ([0-9]+) tests$", output)
    names = re.findall(r"(?m)^test ([A-Za-z0-9_:]+) \.\.\. ok$", output)
    summaries = re.findall(r"(?m)^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; ([0-9]+) filtered out;", output)
    maintenance.require(running == ["4"] and len(names) == 4 and frozenset(names) == NAMES
        and len(summaries) == 1, "READBACK_COMPLETE_UNIT_RESULTS")
    return int(summaries[0])


def run_owned(destination, expected, names, modules, task, seconds):
    previous.require_duration(previous.XML_TASK if task == UNIT else task, seconds)
    original_dump = json.dump
    def write(result, stream, **kwargs):
        return original_dump(annotate(result, task), stream, **kwargs)
    if task != UNIT:
        with patch.object(json, "dump", write):
            return previous.run_owned(destination, expected, names, modules, task, seconds)
    original_pins, original_capture = maintenance.pins, bounded.BoundedProcessCapture
    captures = []
    class UnitCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.filtered = None
            captures.append(self)
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                self.filtered = validate_output(output)
            return output, errors
    def pins(checkpoint=None):
        return previous.parent.require_pins(original_pins(checkpoint), expected)
    def unit_write(result, stream, **kwargs):
        annotate(result, task)
        filtered = captures[-1].filtered if captures else None
        if result.get("state") == "PASS_SCOPED_NOT_GATE" and (
                filtered is None or result.get("tests_passed") != 4):
            result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "READBACK_UNIT_RESULT_MISSING"
        result.update(qualification="COMPLETE_READBACK_BUFFER_UNIT_ONLY_NOT_WHOLE_LIBRARY_OR_GATE",
            expected_test_count=4, source_test_names=sorted(NAMES), outside_component_filtered=filtered,
            whole_library_qualified=False)
        return original_dump(result, stream, **kwargs)
    with patch.object(maintenance, "__file__", str(maintenance.ROOT / SELF)), \
            patch.object(maintenance, "TASKS", {UNIT: previous.XML_ARGS}), \
            patch.object(maintenance, "SOURCES", list(dict.fromkeys(maintenance.SOURCES + list(expected)))), \
            patch.object(maintenance, "pins", pins), \
            patch.object(bounded, "BoundedProcessCapture", UnitCapture), patch.object(json, "dump", unit_write):
        return maintenance.run(task, destination, seconds)


def run_worker():
    original_call = subprocess.call
    def unit_call(arguments, **kwargs):
        expected = [*previous.XML_ARGS, "--locked", "--offline", "--jobs", "1", "--color=never",
            "--target-dir", str(maintenance.TARGET), "--", "--test-threads=1"]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == expected
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "READBACK_WORKER_ARGUMENT_SCOPE")
        return original_call([*arguments[:-1], FILTER, arguments[-1]], **kwargs)
    with patch.object(maintenance, "TASKS", {UNIT: previous.XML_ARGS}), patch.object(subprocess, "call", unit_call):
        return maintenance.worker(UNIT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--task", choices=TASKS, default=UNIT)
    parser.add_argument("--maximum-seconds", type=int, default=180)
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    maintenance.require(maintenance.Path.cwd().resolve() == maintenance.ROOT, "READBACK_ROOT_SCOPE")
    previous.require_duration(previous.XML_TASK if args.task == UNIT else args.task, args.maximum_seconds)
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-moved-readback-buffer.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(maintenance.Windows(), args.task)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_readback_buffer_regression import ReadbackBufferTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(name) for name in (SELF, TEST, SOURCE, ARCHIVE, CANDIDATE)]
    with patch("subprocess.Popen", side_effect=AssertionError("READBACK_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("READBACK_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("READBACK_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ReadbackBufferTests))
    reader.finish()
    failed = sorted({test.id().split(".")[-1] for test, _ in result.failures + result.errors + result.skipped})
    passed = result.testsRun == 8 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_READBACK_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(failed), "failed_tests": failed,
        "source_freeze": freeze, "source_freeze_exact_after": True, "Cargo_SQL_native_executed": False,
        "product_complete": False, "P09_gate": "OPEN"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--owned-worker", "--task", UNIT]:
        raise SystemExit(run_worker())
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "READBACK_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
