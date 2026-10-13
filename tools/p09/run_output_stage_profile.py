"""Test-only original36/changed16 stage diagnostic in the unchanged owned Job."""
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

import run_readback_buffer_regression as previous
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

maintenance, bounded = previous.maintenance, previous.bounded
SELF = "tools/p09/run_output_stage_profile.py"
TEST = "tools/p09/tests/test_output_stage_profile.py"
SOURCE = "crates/hwpx-package/src/document_import/fields/semantics/evaluation/output.rs"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-output-stage-timing-r8/source-preimages.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-149-output-stage-profile-candidate.run03.v1.json"
PARENT_PIN = {"path": previous.CANDIDATE, "bytes": 1609,
    "sha256": "15cba96439dd94fcc5c6f341b17bcc656bbb1e1ca71df7c87fbe5454bbc0a734"}
TASK = "formula-output-stage-profile-tests"
NAME = "document_import::fields::semantics::evaluation::output::stage_profile::actual36_and_changed16_profile_complete_original_lowering_stages"
ARGS = previous.previous.XML_ARGS
QUALIFICATION = "TEST_ONLY_PURE_OUTPUT_PROFILE_NOT_SIGNED_SQL_NATIVE_OR_GATE"
STAGES = frozenset({"fresh_source_reconstruction", "bind_and_pre_verify", "edits_and_protection",
    "preserving_patch", "patch_preservation_checks", "preserving_writer_build",
    "artifact_verify_and_full_candidate_readback", "post_source_verify", "export_verified_candidate", "noop_fresh_source_verify"})
COUNTS = {"original_inputs": 36, "original_no_targets": 20, "original_no_changes": 16,
    "changed_inputs": 16, "formula_targets": 16, "source_cell_bindings": 128,
    "unchanged_original_graphs": 36, "unchanged_changed_source_graphs": 16}
TASKS = (TASK, *previous.TASKS)


def declared_sources(candidate, archive, expected):
    maintenance.require(isinstance(candidate, dict)
        and candidate.get("schema_version") == "hwpx-agent.p09-output-stage-profile-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == previous.previous.parent.contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == PARENT_PIN
        and candidate.get("preimage_archive") == ARCHIVE, "OUTPUT_PROFILE_CANDIDATE_SCOPE")
    deltas = previous.previous.parent.contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == {SOURCE} and SOURCE in expected
        and deltas[SOURCE] != expected[SOURCE], "OUTPUT_PROFILE_EXACT_DELTA_REQUIRED")
    maintenance.require(isinstance(archive, dict)
        and archive.get("schema_version") == "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("baseline_build_pin") == previous.previous.parent.contract.CURRENT_BUILD_PIN
        and archive.get("parent_candidate_pin") == PARENT_PIN
        and len(archive.get("files", [])) == 1, "OUTPUT_PROFILE_PREIMAGE_SCOPE")
    original = archive["files"][0]
    data = base64.b64decode(original["base64"], validate=True)
    maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"]
        and {key: original[key] for key in ("path", "bytes", "sha256")} == expected[SOURCE],
        "OUTPUT_PROFILE_WHOLE_PREIMAGE_DRIFT")
    return {**expected, **deltas}


def load_binding(windows, task):
    maintenance.require(task in TASKS, "OUTPUT_PROFILE_TASK_SCOPE")
    expected, names, modules = previous.load_binding(windows, previous.UNIT if task == TASK else task)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(previous.previous.parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(previous.CANDIDATE) == PARENT_PIN, "OUTPUT_PROFILE_PARENT_BYTE_DRIFT")
    expected = declared_sources(reader.json(CANDIDATE), reader.json(ARCHIVE), expected)
    expected.update({name: reader.pin(name) for name in (SELF, TEST, ARCHIVE, CANDIDATE)})
    source = reader.text(SOURCE)
    original = base64.b64decode(reader.json(ARCHIVE)["files"][0]["base64"], validate=True).decode("utf-8")
    maintenance.require(product_view(source) == original.replace("\r\n", "\n").replace("\r", "\n"),
        "OUTPUT_PROFILE_PRODUCT_BODY_CHANGED")
    if task == TASK:
        maintenance.require(reader.pin(SOURCE) == expected[SOURCE], "OUTPUT_PROFILE_UNIT_SOURCE_DRIFT")
        actual = re.findall(r"(?m)^    #\[test\]\s+fn ([A-Za-z_][A-Za-z0-9_]*)", source)
        maintenance.require(actual == [NAME.rsplit("::", 1)[1]], "OUTPUT_PROFILE_COMPLETE_UNIT_INVENTORY")
        names, modules = (NAME,), (SOURCE,)
    reader.finish()
    return expected, names, modules


def product_view(source):
    # Prove the old product text is unchanged after removing ONLY the exact
    # test-gated timer statements and the explicitly test-only modules.
    statements = ["let mut timer = stage_profile::Timer::new();", *(
        f'timer.record("{stage}");' for stage in sorted(STAGES - {
            "fresh_source_reconstruction", "export_verified_candidate", "noop_fresh_source_verify"}))]
    for statement in statements:
        gated = "        #[cfg(test)]\n        " + statement + "\n"
        maintenance.require(source.count(gated) == 1, "OUTPUT_PROFILE_EXACT_TEST_GATE_REQUIRED")
        source = source.replace(gated, "", 1)
    marker = "// Private test-only observation. No product API, callback, receipt change or cache.\n"
    maintenance.require(source.count(marker) == 1, "OUTPUT_PROFILE_PRIVATE_MODULE_SCOPE")
    begin = source.index(marker)
    end = source.index("#[derive(Debug, Error, Eq, PartialEq)]", begin)
    modules = source[begin:end]
    maintenance.require('#[cfg(test)]\n#[path = "../../../../../tests/support/document_import_settings_inputs.rs"]' in modules
        and "#[cfg(test)]\nmod stage_profile {" in modules, "OUTPUT_PROFILE_MODULES_TEST_ONLY")
    return source[:begin].rstrip("\n") + "\n" + source[end:]


def unique_object(pairs):
    row = {}
    for key, value in pairs:
        maintenance.require(key not in row, "OUTPUT_PROFILE_DUPLICATE_JSON_KEY")
        row[key] = value
    return row


def validate_output(output):
    maintenance.require(isinstance(output, str) and len(output.encode()) <= maintenance.POLICY["output_limit_bytes_per_stream"],
        "OUTPUT_PROFILE_OUTPUT_BUDGET")
    profile_lines = re.findall(r"(?m)^P149_OUTPUT_STAGE_PROFILE=(\{[^\n]+\})$", output)
    maintenance.require(len(profile_lines) == 1, "OUTPUT_PROFILE_SINGLE_PAYLOAD_REQUIRED")
    try:
        row = json.loads(profile_lines[0], object_pairs_hook=unique_object)
    except json.JSONDecodeError:
        raise ValueError("OUTPUT_PROFILE_JSON_INVALID") from None
    keys = {*COUNTS, "lowered_candidates", "mathematically_unchanged", "schema_version", "qualification", "stages", "native_or_SQL_qualified", "product_complete", "P09_gate"}
    maintenance.require(isinstance(row, dict) and set(row) == keys
        and row["schema_version"] == "hwpx-agent.p09-output-stage-timing/v1"
        and row["qualification"] == QUALIFICATION and row["native_or_SQL_qualified"] is False
        and row["product_complete"] is False and row["P09_gate"] == "OPEN", "OUTPUT_PROFILE_PAYLOAD_SCOPE")
    for key, exact in COUNTS.items():
        maintenance.require(type(row[key]) is int and row[key] == exact, "OUTPUT_PROFILE_COMPLETE_CORPUS")
    lowered, unchanged = row["lowered_candidates"], row["mathematically_unchanged"]
    maintenance.require(type(lowered) is int and type(unchanged) is int and lowered > 0 and unchanged > 0
        and lowered + unchanged == 16, "OUTPUT_PROFILE_COMPLETE_RESULT_CLASSIFICATION")
    stages = row["stages"]
    maintenance.require(isinstance(stages, dict) and set(stages) == STAGES, "OUTPUT_PROFILE_COMPLETE_STAGES")
    for name, stage in stages.items():
        calls = 16 if name in {"fresh_source_reconstruction", "bind_and_pre_verify", "edits_and_protection"} else (
            unchanged if name == "noop_fresh_source_verify" else lowered)
        maintenance.require(isinstance(stage, dict) and set(stage) == {"calls", "total_us", "min_us", "max_us"}
            and all(type(v) is int and 0 <= v <= 180000000 for v in stage.values()) and stage["calls"] == calls
            and stage["min_us"] <= stage["max_us"] <= stage["total_us"]
            and stage["min_us"]*calls <= stage["total_us"] <= stage["max_us"]*calls, "OUTPUT_PROFILE_NUMERIC_BOUNDS")
    running = re.findall(r"(?m)^running ([0-9]+) test$", output)
    names = re.findall(r"(?m)^test ([A-Za-z0-9_:]+) \.\.\. ok$", output)
    summaries = re.findall(r"(?m)^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; ([0-9]+) filtered out;", output)
    maintenance.require(running == ["1"] and names == [NAME] and len(summaries) == 1,
        "OUTPUT_PROFILE_COMPLETE_UNIT_RESULTS")
    return row, int(summaries[0])


def annotate(result, task):
    maintenance.require(isinstance(result, dict) and result.get("task") == task, "OUTPUT_PROFILE_RECEIPT_SCOPE")
    result.update(source_variant="test-only-output-stage-profile-r8", optimization_candidate=CANDIDATE,
        product_complete=False, P09_gate="OPEN", signed_SQL_native_or_Gate_qualified=False,
        PC_freeze_resolved=False, statistical_speedup_proven=False, exact_CPU_profiler=False,
        baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD")
    return result


def run_owned(destination, expected, names, modules, task, seconds):
    previous.previous.require_duration(previous.previous.XML_TASK if task == TASK else task, seconds)
    original_dump = json.dump
    def write(result, stream, **kwargs):
        return original_dump(annotate(result, task), stream, **kwargs)
    if task != TASK:
        with patch.object(json, "dump", write):
            return previous.run_owned(destination, expected, names, modules, task, seconds)
    original_pins, original_capture = maintenance.pins, bounded.BoundedProcessCapture
    captures = []
    class ProfileCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.profile, self.filtered = None, None
            captures.append(self)
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                self.profile, self.filtered = validate_output(output)
            return output, errors
    def pins(checkpoint=None):
        return previous.previous.parent.require_pins(original_pins(checkpoint), expected)
    def profile_write(result, stream, **kwargs):
        annotate(result, task)
        profile = captures[-1].profile if captures else None
        filtered = captures[-1].filtered if captures else None
        if result.get("state") == "PASS_SCOPED_NOT_GATE" and (profile is None or result.get("tests_passed") != 1):
            result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "OUTPUT_PROFILE_RESULT_MISSING"
        result.update(qualification=QUALIFICATION, expected_test_count=1, source_test_names=[NAME],
            stage_profile=profile, outside_component_filtered=filtered, whole_library_qualified=False,
            stage_profile_qualified=result.get("state") == "PASS_SCOPED_NOT_GATE" and profile is not None)
        return original_dump(result, stream, **kwargs)
    with patch.object(maintenance, "__file__", str(maintenance.ROOT / SELF)), \
            patch.object(maintenance, "TASKS", {TASK: ARGS}), \
            patch.object(maintenance, "SOURCES", list(dict.fromkeys(maintenance.SOURCES + list(expected)))), \
            patch.object(maintenance, "pins", pins), \
            patch.object(bounded, "BoundedProcessCapture", ProfileCapture), patch.object(json, "dump", profile_write):
        return maintenance.run(task, destination, seconds)


def run_worker():
    original_call = subprocess.call
    def profile_call(arguments, **kwargs):
        expected = [*ARGS, "--locked", "--offline", "--jobs", "1", "--color=never",
            "--target-dir", str(maintenance.TARGET), "--", "--test-threads=1"]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == expected
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "OUTPUT_PROFILE_WORKER_ARGUMENT_SCOPE")
        return original_call([*arguments[:-1], NAME, "--exact", "--show-output", arguments[-1]], **kwargs)
    with patch.object(maintenance, "TASKS", {TASK: ARGS}), patch.object(subprocess, "call", profile_call):
        return maintenance.worker(TASK)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--task", choices=TASKS, default=TASK)
    parser.add_argument("--maximum-seconds", type=int, default=180)
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    maintenance.require(maintenance.Path.cwd().resolve() == maintenance.ROOT, "OUTPUT_PROFILE_ROOT_SCOPE")
    previous.previous.require_duration(previous.previous.XML_TASK if args.task == TASK else args.task, args.maximum_seconds)
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-output-stage-profile.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(maintenance.Windows(), args.task)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_output_stage_profile import OutputStageProfileTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(name) for name in (SELF, TEST, SOURCE, ARCHIVE, CANDIDATE)]
    with patch("subprocess.Popen", side_effect=AssertionError("OUTPUT_PROFILE_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("OUTPUT_PROFILE_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("OUTPUT_PROFILE_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(OutputStageProfileTests))
    reader.finish()
    failed = sorted({test.id().split(".")[-1] for test, _ in result.failures + result.errors + result.skipped})
    passed = result.testsRun == 12 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_OUTPUT_PROFILE_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(failed), "failed_tests": failed,
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
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "OUTPUT_PROFILE_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
