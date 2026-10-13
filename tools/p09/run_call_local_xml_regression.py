"""One call-local parse reuse candidate; original full reads/Job/GO checks retained."""
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

import run_output_stage_profile as previous
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

maintenance, bounded = previous.maintenance, previous.bounded
parent = previous.previous.previous.parent
SELF = "tools/p09/run_call_local_xml_regression.py"
TEST = "tools/p09/tests/test_call_local_xml_regression.py"
NEW = "crates/hwpx-package/src/call_local_xml.rs"
EXISTING = frozenset("crates/hwpx-package/src/" + name for name in ("lib.rs", "preservation.rs", "id_index.rs", "patch.rs"))
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-call-local-xml-reuse-r9/source-preimages.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-149-call-local-xml-reuse-candidate.run01.v1.json"
PARENT_PIN = {"path": previous.CANDIDATE, "bytes": 3585,
    "sha256": "18c34f71e8afd03b7f8e48e178498f7f27034c8c62f2bdb612958c687b20308d"}
UNIT = "call-local-xml-tests"
FILTER = "call_local_xml::tests::"
UNIT_NAMES = frozenset(FILTER + name for name in (
    "exact_fresh_bytes_reuse_one_immutable_model_and_full_round_trip",
    "same_length_changed_bytes_replace_model_instead_of_hash_only_replay",
    "malformed_new_bytes_keep_original_parser_errors_not_cached_acceptance",
    "transfer_moves_only_exact_local_model_and_scopes_do_not_share_state",
    "optimization_budget_falls_back_to_full_fresh_parse_without_rejecting_input",
    "all36_originals_every_modeled_xml_part_match_independent_fresh_parses",
    "full36_preservation_profiles_id_results_and_fresh_read_counts_match_original",
))
CASES = {UNIT: (["test", "-p", "hwpx-package", "--lib"], NEW, 7),
    "patch-engine-tests": (["test", "-p", "hwpx-package", "--test", "patch_engine"], "crates/hwpx-package/tests/patch_engine.rs", 6),
    "id-index-tests": (["test", "-p", "hwpx-package", "--test", "id_index"], "crates/hwpx-package/tests/id_index.rs", 8),
    "preservation-map-tests": (["test", "-p", "hwpx-package", "--test", "preservation_map"], "crates/hwpx-package/tests/preservation_map.rs", 7)}
TASKS = (*CASES, *previous.TASKS)


def declared_sources(candidate, archive, expected):
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-call-local-xml-reuse-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == parent.contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == PARENT_PIN
        and candidate.get("preimage_archive") == ARCHIVE
        and candidate.get("added_sources") == [NEW], "LOCAL_XML_CANDIDATE_SCOPE")
    deltas = parent.contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == EXISTING | {NEW} and NEW not in expected
        and EXISTING <= set(expected) and all(deltas[p] != expected[p] for p in EXISTING), "LOCAL_XML_EXACT_DELTA_REQUIRED")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("baseline_build_pin") == parent.contract.CURRENT_BUILD_PIN
        and archive.get("parent_candidate_pin") == PARENT_PIN
        and len(archive.get("files", [])) == len(EXISTING), "LOCAL_XML_PREIMAGE_SCOPE")
    seen = set()
    for original in archive["files"]:
        data = base64.b64decode(original["base64"], validate=True)
        name = original["path"]
        maintenance.require(name in EXISTING and name not in seen and len(data) == original["bytes"]
            and hashlib.sha256(data).hexdigest() == original["sha256"]
            and {key: original[key] for key in ("path", "bytes", "sha256")} == expected[name],
            "LOCAL_XML_WHOLE_PREIMAGE_DRIFT")
        seen.add(name)
    maintenance.require(seen == EXISTING, "LOCAL_XML_COMPLETE_PREIMAGES_REQUIRED")
    return {**expected, **deltas}


def load_binding(windows, task):
    maintenance.require(task in TASKS, "LOCAL_XML_TASK_SCOPE")
    expected, names, modules = previous.load_binding(windows, previous.TASK if task in CASES else task)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(previous.CANDIDATE) == PARENT_PIN, "LOCAL_XML_PARENT_BYTE_DRIFT")
    expected = declared_sources(reader.json(CANDIDATE), reader.json(ARCHIVE), expected)
    expected.update({name: reader.pin(name) for name in (SELF, TEST, ARCHIVE, CANDIDATE)})
    if task in CASES:
        _, root, count = CASES[task]
        source = reader.text(root)
        maintenance.require(reader.pin(root) == expected[root], "LOCAL_XML_TARGET_SOURCE_DRIFT")
        if task == UNIT:
            names = frozenset(FILTER + name for name in re.findall(r"(?m)^    #\[test\]\s+fn ([A-Za-z_][A-Za-z0-9_]*)", source))
            maintenance.require(names == UNIT_NAMES, "LOCAL_XML_COMPLETE_UNIT_INVENTORY")
        else:
            maintenance.require(not re.search(r"(?m)^mod |#\[path", source), "LOCAL_XML_UNREVIEWED_MODULE")
            names = re.findall(r"(?m)^#\[test\]\s+fn ([A-Za-z_][A-Za-z0-9_]*)", source)
            maintenance.require(len(names) == count and len(set(names)) == count, "LOCAL_XML_COMPLETE_TARGET_INVENTORY")
        modules = (root,)
    reader.finish()
    return expected, names, modules


def validate_output(output, task, names):
    maintenance.require(task in CASES and isinstance(output, str)
        and len(output.encode()) <= maintenance.POLICY["output_limit_bytes_per_stream"], "LOCAL_XML_OUTPUT_SCOPE")
    count = CASES[task][2]
    running = re.findall(r"(?m)^running ([0-9]+) tests$", output)
    completed = re.findall(r"(?m)^test ([A-Za-z0-9_:]+) \.\.\. ok$", output)
    summaries = re.findall(r"(?m)^test result: ok\. ([0-9]+) passed; 0 failed; 0 ignored; 0 measured; ([0-9]+) filtered out;", output)
    maintenance.require(running == [str(count)] and len(completed) == count and set(completed) == set(names)
        and len(summaries) == 1 and summaries[0][0] == str(count)
        and (task == UNIT or summaries[0][1] == "0"), "LOCAL_XML_COMPLETE_RESULTS_REQUIRED")
    return int(summaries[0][1])


def annotate(result, task):
    maintenance.require(isinstance(result, dict) and result.get("task") == task, "LOCAL_XML_RECEIPT_SCOPE")
    result.update(source_variant="call-local-xml-reuse-r9", optimization_candidate=CANDIDATE,
        product_complete=False, P09_gate="OPEN", signed_SQL_native_or_Gate_qualified=False,
        PC_freeze_resolved=False, statistical_speedup_proven=False,
        baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD")
    return result


def require_duration(task, seconds):
    maintenance.require(task in TASKS, "LOCAL_XML_DURATION_TASK_SCOPE")
    mapped = previous.previous.previous.XML_TASK if task in CASES or task in {
        previous.TASK, previous.previous.UNIT} else task
    previous.previous.previous.require_duration(mapped, seconds)


def run_owned(destination, expected, names, modules, task, seconds):
    require_duration(task, seconds)
    original_dump = json.dump
    def write(result, stream, **kwargs):
        return original_dump(annotate(result, task), stream, **kwargs)
    if task not in CASES:
        with patch.object(json, "dump", write):
            return previous.run_owned(destination, expected, names, modules, task, seconds)
    original_pins, original_capture = maintenance.pins, bounded.BoundedProcessCapture
    captures = []
    class CompleteCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.filtered = None
            captures.append(self)
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                self.filtered = validate_output(output, task, names)
            return output, errors
    def pins(checkpoint=None):
        return parent.require_pins(original_pins(checkpoint), expected)
    def complete_write(result, stream, **kwargs):
        annotate(result, task)
        filtered = captures[-1].filtered if captures else None
        if result.get("state") == "PASS_SCOPED_NOT_GATE" and (
                filtered is None or result.get("tests_passed") != CASES[task][2]):
            result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "LOCAL_XML_RESULT_MISSING"
        result.update(qualification="CALL_LOCAL_XML_COMPONENT_OR_COMPLETE_DECLARED_TARGET_ONLY_NOT_GATE",
            expected_test_count=CASES[task][2], source_test_names=sorted(names),
            outside_component_filtered=filtered, whole_library_qualified=False)
        return original_dump(result, stream, **kwargs)
    with patch.object(maintenance, "__file__", str(maintenance.ROOT / SELF)), \
            patch.object(maintenance, "TASKS", {task: CASES[task][0]}), \
            patch.object(maintenance, "SOURCES", list(dict.fromkeys(maintenance.SOURCES + list(expected)))), \
            patch.object(maintenance, "pins", pins), \
            patch.object(bounded, "BoundedProcessCapture", CompleteCapture), patch.object(json, "dump", complete_write):
        return maintenance.run(task, destination, seconds)


def run_worker(task):
    maintenance.require(task in CASES, "LOCAL_XML_WORKER_TASK_SCOPE")
    original_call = subprocess.call
    def closed_call(arguments, **kwargs):
        expected = [*CASES[task][0], "--locked", "--offline", "--jobs", "1", "--color=never",
            "--target-dir", str(maintenance.TARGET), "--", "--test-threads=1"]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == expected
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "LOCAL_XML_WORKER_ARGUMENT_SCOPE")
        return original_call([*arguments[:-1], FILTER, arguments[-1]] if task == UNIT else arguments, **kwargs)
    with patch.object(maintenance, "TASKS", {task: CASES[task][0]}), patch.object(subprocess, "call", closed_call):
        return maintenance.worker(task)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--task", choices=TASKS, default=UNIT)
    parser.add_argument("--maximum-seconds", type=int, default=180)
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    maintenance.require(maintenance.Path.cwd().resolve() == maintenance.ROOT, "LOCAL_XML_ROOT_SCOPE")
    require_duration(args.task, args.maximum_seconds)
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-call-local-xml-reuse.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(maintenance.Windows(), args.task)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_call_local_xml_regression import CallLocalXmlTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(name) for name in (SELF, TEST, NEW, ARCHIVE, CANDIDATE)]
    with patch("subprocess.Popen", side_effect=AssertionError("LOCAL_XML_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("LOCAL_XML_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("LOCAL_XML_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(CallLocalXmlTests))
    reader.finish()
    failed = sorted({test.id().split(".")[-1] for test, _ in result.failures + result.errors + result.skipped})
    passed = result.testsRun == 11 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_LOCAL_XML_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(failed), "failed_tests": failed,
        "source_freeze": freeze, "source_freeze_exact_after": True, "Cargo_SQL_native_executed": False,
        "product_complete": False, "P09_gate": "OPEN"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        raise SystemExit(run_worker(sys.argv[3]))
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "LOCAL_XML_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
