"""Complete36 numeric timing diagnostic in the unchanged owned Job, not product/Gate."""
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

import conservative_maintenance as maintenance
import bounded_process_progress as bounded
import run_stored_comment_regression as parent
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

SELF = "tools/p09/run_source_stage_profile.py"
TEST = "tools/p09/tests/test_source_stage_profile.py"
EXAMPLE = "crates/hwpx-package/examples/source_formula_evaluation_probe.rs"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-source-stage-timing-probe/source-preimages.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-149-source-stage-profile-candidate.run01.v1.json"
PARENT_PIN = {"path": parent.ANCHOR_PREFIX_CANDIDATE, "bytes": 1864,
    "sha256": "91505a2d1158cc86153dc77d8adc36abf97a3bc6e445e89acdd3100a52bfc285"}
TASK = "source-formula-stage-profile"
ARGS = ["run", "--profile", "test", "-p", "hwpx-package", "--example", "source_formula_evaluation_probe"]
STAGES = frozenset({"source_import", "forms_import", "field_ranges_import", "field_semantics_import",
    "meaning_graph_clone", "meaning_graph_canonical_sha256", "source_formula_evaluation", "fresh_source_verify"})
QUALIFICATION = "PROFILE_ONLY_NOT_SIGNED_SERVICE_SQL_NATIVE_OR_GATE"
PROFILE_KEYS = frozenset({"schema_version", "qualification", "actual_historical_inputs",
    "unchanged_whole_meaning_graphs", "inputs_with_formula_targets", "formula_targets",
    "source_cell_bindings", "stages", "native_or_SQL_qualified", "product_complete", "P09_gate"})


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        maintenance.require(key not in result, "PROFILE_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def validate_profile(output):
    maintenance.require(isinstance(output, str) and len(output.encode("utf-8")) <= 4096,
        "PROFILE_OUTPUT_BUDGET")
    try:
        row = json.loads(output, object_pairs_hook=unique_object)
    except json.JSONDecodeError:
        raise ValueError("PROFILE_OUTPUT_JSON") from None
    maintenance.require(isinstance(row, dict) and set(row) == PROFILE_KEYS
        and row["schema_version"] == "hwpx-agent.p09-source-stage-timing/v1"
        and row["qualification"] == QUALIFICATION and row["native_or_SQL_qualified"] is False
        and row["product_complete"] is False and row["P09_gate"] == "OPEN", "PROFILE_OUTPUT_SCOPE")
    for key, exact in (("actual_historical_inputs", 36), ("unchanged_whole_meaning_graphs", 36),
            ("inputs_with_formula_targets", 16), ("source_cell_bindings", 128)):
        maintenance.require(type(row[key]) is int and row[key] == exact, "PROFILE_COMPLETE_CORPUS_REQUIRED")
    maintenance.require(type(row["formula_targets"]) is int and 16 <= row["formula_targets"] <= 100000,
        "PROFILE_FORMULA_COVERAGE")
    stages = row["stages"]
    maintenance.require(isinstance(stages, dict) and set(stages) == STAGES, "PROFILE_STAGE_COVERAGE")
    for stage in stages.values():
        maintenance.require(isinstance(stage, dict) and set(stage) == {"calls", "total_us", "min_us", "max_us"}
            and all(type(value) is int and 0 <= value <= 180000000 for value in stage.values())
            and stage["calls"] == 36 and stage["min_us"] <= stage["max_us"] <= stage["total_us"]
            and stage["min_us"] * 36 <= stage["total_us"] <= stage["max_us"] * 36,
            "PROFILE_NUMERIC_STAGE_BOUNDS")
    return row


def profile_sources(candidate, archive, expected):
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-source-stage-profile-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == parent.contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == PARENT_PIN
        and candidate.get("preimage_archive") == ARCHIVE, "PROFILE_CANDIDATE_SCOPE")
    deltas = parent.contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == {EXAMPLE} and EXAMPLE in expected and deltas[EXAMPLE] != expected[EXAMPLE],
        "PROFILE_EXACT_EXAMPLE_DELTA_REQUIRED")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("baseline_build_pin") == parent.contract.CURRENT_BUILD_PIN
        and archive.get("parent_candidate_pin") == PARENT_PIN and len(archive.get("files", [])) == 1,
        "PROFILE_PREIMAGE_SCOPE")
    original = archive["files"][0]
    data = base64.b64decode(original["base64"], validate=True)
    maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"]
        and {key: original[key] for key in ("path", "bytes", "sha256")} == expected[EXAMPLE],
        "PROFILE_ORIGINAL_EXAMPLE_DRIFT")
    return {**expected, **deltas}


def load_binding(windows):
    expected, _, _ = parent.load_binding(windows, "import-source-tests", "anchor-prefix-r4")
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(parent.ANCHOR_PREFIX_CANDIDATE) == PARENT_PIN, "PROFILE_PARENT_BYTE_DRIFT")
    expected = profile_sources(reader.json(CANDIDATE), reader.json(ARCHIVE), expected)
    expected.update({name: reader.pin(name) for name in (CANDIDATE, ARCHIVE, SELF, TEST)})
    reader.finish()
    return expected


def run_owned(destination, expected, maximum_seconds):
    maintenance.require(type(maximum_seconds) is int and 30 <= maximum_seconds <= 180, "PROFILE_DURATION_SCOPE")
    original_pins, original_capture, original_dump = maintenance.pins, bounded.BoundedProcessCapture, json.dump
    captures = []
    class ProfileCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.numeric_profile = None
            captures.append(self)
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                self.numeric_profile = validate_profile(output)
            return output, errors
    def pins(checkpoint=None):
        return parent.require_pins(original_pins(checkpoint), expected)
    def write_receipt(result, stream, **kwargs):
        maintenance.require(result.get("task") == TASK, "PROFILE_RECEIPT_SCOPE")
        profile = captures[-1].numeric_profile if captures else None
        if result.get("state") == "PASS_SCOPED_NOT_GATE" and profile is None:
            result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "PROFILE_RESULT_MISSING"
        result.update(source_variant="profile-instrumentation-r5", execution_mode="complete36_numeric_diagnostic",
            baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD", qualification=QUALIFICATION,
            stage_profile=profile, stage_profile_qualified=result.get("state") == "PASS_SCOPED_NOT_GATE" and profile is not None,
            exact_CPU_profiler=False, statistical_speedup_proven=False, signed_SQL_native_or_Gate_qualified=False)
        return original_dump(result, stream, **kwargs)
    sources = list(dict.fromkeys(maintenance.SOURCES + list(expected) + [SELF, TEST, ARCHIVE, CANDIDATE]))
    with patch.object(maintenance, "__file__", str(maintenance.ROOT / SELF)), \
            patch.object(maintenance, "TASKS", {TASK: ARGS}), patch.object(maintenance, "SOURCES", sources), \
            patch.object(maintenance, "pins", pins), patch.object(bounded, "BoundedProcessCapture", ProfileCapture), \
            patch.object(json, "dump", write_receipt):
        return maintenance.run(TASK, destination, maximum_seconds)


def run_worker():
    original_call = subprocess.call
    def diagnostic_call(arguments, **kwargs):
        expected = [*ARGS, "--locked", "--offline", "--jobs", "1", "--color=never", "--target-dir", str(maintenance.TARGET)]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == expected
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "PROFILE_WORKER_ARGUMENT_SCOPE")
        return original_call([*arguments, "--", "--timing-only"], **kwargs)
    with patch.object(maintenance, "TASKS", {TASK: ARGS}), patch.object(subprocess, "call", diagnostic_call):
        return maintenance.worker(TASK)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--light", action="store_true")
    parser.add_argument("--maximum-seconds", type=int, default=180)
    args = parser.parse_args()
    maintenance.require(Path.cwd().resolve() == maintenance.ROOT, "PROFILE_ROOT_SCOPE")
    maintenance.require(30 <= args.maximum_seconds <= 180, "PROFILE_DURATION_SCOPE")
    windows = maintenance.Windows()
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-source-stage-profile.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        return run_owned(destination, load_binding(windows), args.maximum_seconds)
    from tests.test_source_stage_profile import SourceStageProfileTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(name) for name in (SELF, TEST, EXAMPLE, ARCHIVE)]
    with patch("subprocess.Popen", side_effect=AssertionError("PROFILE_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("PROFILE_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("PROFILE_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(SourceStageProfileTests))
    reader.finish()
    failed = sorted({test.id().split(".")[-1] for test, _ in result.failures + result.errors + result.skipped})
    passed = result.testsRun == 10 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_PROFILE_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun - len(failed), "failed_tests": failed,
        "source_freeze": freeze, "source_freeze_exact_after": True, "Cargo_SQL_native_executed": False,
        "product_complete": False, "P09_gate": "OPEN"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--owned-worker", "--task", TASK]:
        raise SystemExit(run_worker())
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "PROFILE_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
