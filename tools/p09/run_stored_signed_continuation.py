"""Exact unchanged signed16 test, not a replay/qualification of the full249 prefix.

Reuse original owned Job/GO/CPU/RAM/streams/cleanup. Only reviewed task selection
and a finite 600s budget for the previously >222s observed single corpus test.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_call_local_xml_regression as previous
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

maintenance, bounded, parent = previous.maintenance, previous.bounded, previous.parent
SELF = "tools/p09/run_stored_signed_continuation.py"
TEST = "tools/p09/tests/test_stored_signed_continuation.py"
PARENT_PIN = {"path": previous.CANDIDATE, "bytes": 1667,
    "sha256": "5d229e2a37f0dd033417d263d27e94f6904f58eab363b44dbc7bdcff3e83b69b"}
INVENTORY = "stored-signed-inventory"
CHANGED = "stored-signed-changed-tests"
NAME = "actual_import::formula_policy_issuer::corpus::changed::all16_original_numeric_derivatives_have_signed_changed_candidates_exact_current_and_live_revocation"
ARGS = parent.CASES["stored-form-tests"][0]
TASKS = (INVENTORY, CHANGED)


def require_duration(task, seconds):
    maintenance.require(task in TASKS and type(seconds) is int
        and 30 <= seconds <= (600 if task == CHANGED else 180), "SIGNED_CONTINUATION_FINITE_SCOPE")


def select_names(names):
    maintenance.require(isinstance(names, (list, tuple)) and len(names) == len(set(names)) == 249
        and all(isinstance(n, str) and re.fullmatch(r"[a-z][a-z0-9_:]*", n) for n in names)
        and names.count(NAME) == 1, "SIGNED_CONTINUATION_COMPLETE_PARENT_INVENTORY")
    return [NAME]


def inventory_path(run):
    maintenance.require(type(run) is int and 1 <= run <= 99, "SIGNED_CONTINUATION_INVENTORY_RUN_SCOPE")
    return f"implementation/p09/evidence/p09-149-stored-signed-continuation.inventory-run{run:02}.v1.json"


def accept_inventory(row, expected, names, modules):
    select_names(names)
    maintenance.require(isinstance(row, dict) and row.get("state") == "PASS_SCOPED_NOT_GATE"
        and row.get("task") == INVENTORY and row.get("compiled_inventory_exact") is True
        and row.get("source_variant") == "call-local-xml-reuse-r9"
        and row.get("source_test_names") == list(names)
        and row.get("source_module_instances") == list(modules)
        and row.get("runtime_tests_executed") is False and row.get("product_complete") is False
        and row.get("P09_gate") == "OPEN" and row.get("stop_reason") is None
        and row.get("owned_tree_empty") is True and row.get("cleanup_confirmed") is True
        and row.get("job_final", {}).get("active_processes") == 0,
        "SIGNED_CONTINUATION_CURRENT_COMPILED_INVENTORY_REQUIRED")
    frozen = parent.contract.inputs.inventory(row["source_freeze"])
    maintenance.require(all(frozen.get(name) == pin for name, pin in expected.items()),
        "SIGNED_CONTINUATION_COMPILED_SOURCE_OR_HELPER_DRIFT")


def load_binding(windows, task, inventory_run):
    maintenance.require(task in TASKS, "SIGNED_CONTINUATION_TASK_SCOPE")
    expected, names, modules = previous.load_binding(windows, "stored-form-tests")
    select_names(names)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(previous.CANDIDATE) == PARENT_PIN, "SIGNED_CONTINUATION_PARENT_PIN_DRIFT")
    expected.update({name: reader.pin(name) for name in (SELF, TEST)})
    if task == CHANGED:
        name = inventory_path(inventory_run)
        accept_inventory(reader.json(name), expected, names, modules)
        expected[name] = reader.pin(name)
    reader.finish()
    return expected, names, modules


def validate_output(output):
    maintenance.require(isinstance(output, str) and len(output.encode()) <= bounded.LIMIT,
        "SIGNED_CONTINUATION_OUTPUT_LIMIT")
    running = re.findall(r"(?m)^running ([0-9]+) test(?:s)?\r?$", output)
    completed = re.findall(r"(?m)^test ([a-z][a-z0-9_:]*) \.\.\. ok\r?$", output)
    summaries = re.findall(r"(?m)^test result: ok\. ([0-9]+) passed; ([0-9]+) failed; ([0-9]+) ignored; ([0-9]+) measured; ([0-9]+) filtered out;", output)
    maintenance.require(running == ["1"] and completed == [NAME]
        and summaries == [("1", "0", "0", "0", "248")], "SIGNED_CONTINUATION_EXACT_SINGLE_COMPLETE_RESULT")


def annotate(result, task, names, modules, accepted, progress=None):
    maintenance.require(isinstance(result, dict) and result.get("task") == task, "SIGNED_CONTINUATION_RECEIPT_SCOPE")
    selected = select_names(names)
    if result.get("state") == "PASS_SCOPED_NOT_GATE" and (not accepted
            or (task == CHANGED and result.get("tests_passed") != 1)):
        result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "SIGNED_CONTINUATION_COMPLETE_RESULT_MISSING"
    passed = result.get("state") == "PASS_SCOPED_NOT_GATE" and accepted
    result.update(source_variant="call-local-xml-reuse-r9", optimization_parent_pin=PARENT_PIN,
        execution_mode="compiled_inventory_only" if task == INVENTORY else "exact_original_signed16_test",
        source_test_names=list(names), source_module_instances=list(modules),
        selected_test_names=[] if task == INVENTORY else selected,
        expected_test_count=249 if task == INVENTORY else 1,
        compiled_inventory_exact=passed if task == INVENTORY else None,
        runtime_tests_executed=False if task == INVENTORY else (True if passed else None),
        signed_changed16_component_complete=passed and task == CHANGED,
        outside_component_filtered=248 if passed and task == CHANGED else None,
        full249_current_qualified=False, signed_SQL_native_or_Gate_qualified=False,
        product_complete=False, P09_gate="OPEN", PC_freeze_resolved=False,
        baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD",
        raw_logs_printed_or_saved=False, original_test_bodies_changed=False,
        resource_policy_changed=False, system_or_Defender_or_WSL_or_Codex_settings_changed=False)
    if progress is not None:
        result["runtime_progress"] = progress.snapshot()
    return result


def run_owned(destination, expected, names, modules, task, seconds):
    require_duration(task, seconds)
    select_names(names)
    original_pins, original_capture, original_dump = maintenance.pins, bounded.BoundedProcessCapture, json.dump
    progress = parent.RuntimeProgress([NAME]) if task == CHANGED else None
    captures = []
    class ExactCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.accepted = False
            captures.append(self)
        def observe_runtime(self):
            if progress is not None:
                with self.lock:
                    text = bytes(self.buffers["stdout"]).decode("utf-8", errors="replace")
                progress.observe(text)
        def progress(self):
            result = super().progress()
            self.observe_runtime()
            return result
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                if task == INVENTORY:
                    parent.validate_listing(output, names, "stored-form-list")
                else:
                    validate_output(output)
                self.accepted = True
            return output, errors
    def pins(checkpoint=None):
        return parent.require_pins(original_pins(checkpoint), expected)
    def write(result, stream, **kwargs):
        capture = captures[-1] if captures else None
        try:
            if capture:
                capture.observe_runtime()
            annotate(result, task, names, modules, bool(capture and capture.accepted), progress)
        except ValueError:
            result.update(state="STOPPED_NOT_ACCEPTED", stop_reason="SIGNED_CONTINUATION_PROGRESS_NOT_ACCEPTED",
                signed_changed16_component_complete=False, full249_current_qualified=False,
                product_complete=False, P09_gate="OPEN")
        return original_dump(result, stream, **kwargs)
    with patch.object(maintenance, "__file__", str(maintenance.ROOT / SELF)), \
            patch.object(maintenance, "TASKS", {task: list(ARGS)}), \
            patch.object(maintenance, "SOURCES", list(dict.fromkeys(maintenance.SOURCES + list(expected)))), \
            patch.object(maintenance, "pins", pins), patch.object(bounded, "BoundedProcessCapture", ExactCapture), \
            patch.object(json, "dump", write):
        return maintenance.run(task, destination, seconds)


def run_worker(task):
    maintenance.require(task in TASKS, "SIGNED_CONTINUATION_WORKER_TASK_SCOPE")
    original_call = subprocess.call
    def call(arguments, **kwargs):
        args = [*ARGS, "--locked", "--offline", "--jobs", "1", "--color=never",
            "--target-dir", str(maintenance.TARGET)]
        if task == CHANGED:
            args += ["--", "--test-threads=1"]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == args
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "SIGNED_CONTINUATION_WORKER_ARGUMENT_SCOPE")
        selected = [*arguments[:-1], NAME, "--exact", arguments[-1]] if task == CHANGED else [
            *arguments, "--", "--list", "--format", "terse"]
        return original_call(selected, **kwargs)
    with patch.object(maintenance, "TASKS", {task: list(ARGS)}), patch.object(subprocess, "call", call):
        return maintenance.worker(task)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--task", choices=TASKS, default=CHANGED)
    parser.add_argument("--inventory-run", type=int, choices=range(1, 100), default=1)
    parser.add_argument("--maximum-seconds", type=int, default=600)
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    maintenance.require(maintenance.Path.cwd().resolve() == maintenance.ROOT, "SIGNED_CONTINUATION_ROOT_SCOPE")
    require_duration(args.task, args.maximum_seconds)
    windows = maintenance.Windows()
    kind = "light" if args.light else ("inventory" if args.task == INVENTORY else "actual")
    destination = scoped_path(f"implementation/p09/evidence/p09-149-stored-signed-continuation.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(windows, args.task, args.inventory_run)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_stored_signed_continuation import StoredSignedContinuationTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    frozen = [reader.pin(name) for name in (SELF, TEST, previous.CANDIDATE)]
    with patch("subprocess.Popen", side_effect=AssertionError("SIGNED_CONTINUATION_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("SIGNED_CONTINUATION_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("SIGNED_CONTINUATION_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(StoredSignedContinuationTests))
    reader.finish()
    failures = sorted({test.id().split(".")[-1] for test, _ in result.failures + result.errors + result.skipped})
    passed = result.testsRun == 12 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_SIGNED_CONTINUATION_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(failures), "failed_tests": failures,
        "source_freeze": frozen, "source_freeze_exact_after": True, "Cargo_SQL_native_executed": False,
        "original_test_bodies_changed": False, "resource_policy_changed": False,
        "product_complete": False, "P09_gate": "OPEN"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key:row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        raise SystemExit(run_worker(sys.argv[3]))
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "SIGNED_CONTINUATION_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
