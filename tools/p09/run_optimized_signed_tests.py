"""Bounded test-only package profile comparison; no source/auth/assertion removal.

Only CLI Cargo config keys for two exact workspace packages are added. Existing
owned Job/GO/CPU/RAM/stream/cleanup remain unchanged. Original signed16 assertions
and full249 compiled inventory must match before any component success is accepted.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_signed_stage_cost as previous
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

maintenance, bounded = previous.maintenance, previous.bounded
SELF = "tools/p09/run_optimized_signed_tests.py"
TEST = "tools/p09/tests/test_optimized_signed_tests.py"
INVENTORY = "stored-signed-basic-opt-inventory"
PROFILE = "stored-signed-basic-opt-tests"
PACKAGES = ("hwpx-package", "hwpx-agent-cli")
CONFIG = tuple(f'profile.test.package.{package}.{key}={value}'
    for package in PACKAGES for key, value in (
        ("opt-level", "1"), ("debug-assertions", "true"),
        ("overflow-checks", "true"), ("codegen-units", "16"),
        ("debug", '"line-tables-only"'))) + ('profile.test.lto="off"',)
PARENT_SUMMARY = "implementation/p09/evidence/p09-149-signed-stage-cost.summary-run01.v1.json"
PARENT_PIN = {"path": PARENT_SUMMARY, "bytes": 6947,
    "sha256": "cab38d820add8b78e0a3ee82d0d03915e548160e25d2f79941bed78125449aa6"}
SOURCE_VARIANT = "unchanged-r11-Rust-basic-opt-two-package-test-profile-r12"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-basic-opt-memory-scope-r12/helper-preimages.v1.json"
STOP_PIN = {"path":"implementation/p09/evidence/p09-149-signed-basic-opt.inventory-run01.v1.json",
    "bytes":618983,"sha256":"90edf58f7074ee3570af894e16e143f6ca0daf17f6b7d15baa9177d4536891ef"}


def require_duration(task, seconds):
    maintenance.require(task in (INVENTORY, PROFILE) and type(seconds) is int
        and 30 <= seconds <= (600 if task == INVENTORY else 180), "BASIC_OPT_FINITE_SCOPE")


def inventory_path(run):
    previous.original.inventory_path(run)
    return f"implementation/p09/evidence/p09-149-signed-basic-opt.inventory-run{run:02}.v1.json"


def accept_inventory(row, expected, names, modules):
    maintenance.require(row.get("source_variant") == SOURCE_VARIANT
        and row.get("test_package_profile_config") == list(CONFIG)
        and row.get("task") == INVENTORY, "BASIC_OPT_CURRENT_COMPILED_PROFILE_REQUIRED")
    view = dict(row, source_variant="call-local-xml-reuse-r9", task=previous.original.INVENTORY)
    previous.original.accept_inventory(view, expected, names, modules)


def load_binding(windows, task, inventory_run):
    require_duration(task, 180)
    expected, names, modules = previous.load_binding(windows, previous.PROFILE, 1)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(previous.parent.observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(PARENT_SUMMARY) == PARENT_PIN, "BASIC_OPT_PARENT_SUMMARY_DRIFT")
    parent = reader.json(PARENT_SUMMARY)
    maintenance.require(parent["source_closing_exact"] and parent["source_test_count"] == 249
        and parent["source_module_instances"] == 59 and not parent["product_complete"], "BASIC_OPT_PARENT_SCOPE")
    # The former three-package profile failed safely, not a current build PASS.
    # Whole prior helpers are bound to that original stop; no resource cap change.
    maintenance.require(reader.pin(STOP_PIN["path"]) == STOP_PIN, "BASIC_OPT_PREVIOUS_STOP_PIN_DRIFT")
    stopped = reader.json(STOP_PIN["path"])
    maintenance.require(stopped["state"] == "STOPPED_NOT_ACCEPTED"
        and stopped["stop_reason"] == "STOP_OWNED_JOB_MEMORY_BUDGET"
        and stopped["job_final"]["active_processes"] == 0
        and stopped["cleanup_confirmed"] and stopped["owned_tree_empty"], "BASIC_OPT_PREVIOUS_STOP_SCOPE")
    old = previous.parent.contract.inputs.inventory(stopped["source_freeze"])
    archive = reader.json(ARCHIVE)
    maintenance.require(archive["compile_stop_pin"] == STOP_PIN and len(archive["files"]) == 2,
        "BASIC_OPT_COMPLETE_PREVIOUS_HELPERS_REQUIRED")
    import base64
    import hashlib
    seen = set()
    for item in archive["files"]:
        name = item["path"]; raw = base64.b64decode(item["base64"], validate=True)
        pin = {k:item[k] for k in ("path", "bytes", "sha256")}
        maintenance.require(name in (SELF, TEST) and name not in seen and old[name] == pin
            and len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
            "BASIC_OPT_PREVIOUS_HELPER_PREIMAGE_DRIFT")
        seen.add(name)
    maintenance.require(seen == {SELF, TEST}, "BASIC_OPT_PREVIOUS_HELPER_SCOPE")
    for name, pin in old.items():
        if name not in (SELF, TEST):
            maintenance.require(reader.pin(name) == pin, "BASIC_OPT_UNDECLARED_PRIOR_SOURCE_DRIFT")
    expected.update({name: reader.pin(name) for name in (SELF, TEST, PARENT_SUMMARY, ARCHIVE, STOP_PIN["path"])})
    if task == PROFILE:
        name = inventory_path(inventory_run)
        accept_inventory(reader.json(name), expected, names, modules)
        expected[name] = reader.pin(name)
    reader.finish()
    return expected, names, modules


def optimized_arguments(args, task, env):
    require_duration(task, 180)
    tail = ["--", previous.original.NAME, "--exact", "--nocapture", "--test-threads=1"] if task == PROFILE else ["--", "--list", "--format", "terse"]
    base = [*previous.original.ARGS, "--locked", "--offline", "--jobs", "1",
        "--color=never", "--target-dir", str(maintenance.TARGET), *tail]
    maintenance.require(isinstance(args, list) and args[1:] == base, "BASIC_OPT_ORIGINAL_ARGUMENTS_REQUIRED")
    required = {"CARGO_BUILD_JOBS": "1", "CARGO_PROFILE_TEST_OPT_LEVEL": "0",
        "CARGO_PROFILE_TEST_DEBUG_ASSERTIONS": "true", "CARGO_PROFILE_TEST_OVERFLOW_CHECKS": "true",
        "CARGO_PROFILE_TEST_CODEGEN_UNITS": "16", "RUST_TEST_THREADS": "1", "RUSTUP_AUTO_INSTALL": "0"}
    maintenance.require(isinstance(env, dict) and all(env.get(k) == v for k, v in required.items()), "BASIC_OPT_ORIGINAL_CHECKS_ENVIRONMENT_REQUIRED")
    overrides = [value for entry in CONFIG for value in ("--config", entry)]
    return [args[0], *overrides, *args[1:]]


def run_worker(task):
    require_duration(task, 180)
    real_call = subprocess.call
    def call(args, **kwargs):
        maintenance.require(kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL,
            "BASIC_OPT_ORIGINAL_WORKER_SCOPE_REQUIRED")
        actual = optimized_arguments(args, task, kwargs.get("env"))
        return real_call(actual, **kwargs)
    with patch.object(previous, "INVENTORY", INVENTORY), patch.object(previous, "PROFILE", PROFILE), \
            patch.object(previous, "require_duration", require_duration), patch.object(subprocess, "call", call):
        return previous.run_worker(task)


def run_owned(destination, expected, names, modules, task, seconds):
    require_duration(task, seconds)
    real_dump = json.dump
    def write(row, stream, **kwargs):
        row.update(source_variant=SOURCE_VARIANT, Rust_sources_or_original_test_assertions_changed=False,
            test_package_profile_config=list(CONFIG), test_profile_parent_pin=PARENT_PIN,
            basic_test_package_optimization_only=True, assertion_or_overflow_checks_disabled=False,
            whole_Cargo_or_OS_settings_changed=False, original_owned_resource_policy_changed=False,
            new_profile_qualified_only_after_current_compiled_inventory=True,
            full249_current_qualified=False, product_complete=False, P09_gate="OPEN")
        return real_dump(row, stream, **kwargs)
    with patch.object(previous, "SELF", SELF), patch.object(previous, "TEST", TEST), \
            patch.object(previous, "INVENTORY", INVENTORY), patch.object(previous, "PROFILE", PROFILE), \
            patch.object(previous, "require_duration", require_duration), patch.object(json, "dump", write):
        return previous.run_owned(destination, expected, names, modules, task, seconds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1,100), required=True)
    parser.add_argument("--task", choices=(INVENTORY, PROFILE), default=PROFILE)
    parser.add_argument("--inventory-run", type=int, choices=range(1,100), default=1)
    parser.add_argument("--maximum-seconds", type=int, default=120)
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args(); require_duration(args.task, args.maximum_seconds)
    maintenance.require(maintenance.Path.cwd().resolve() == maintenance.ROOT, "BASIC_OPT_ROOT_SCOPE")
    windows = maintenance.Windows()
    kind = "light" if args.light else ("inventory" if args.task == INVENTORY else "actual")
    destination = scoped_path(f"implementation/p09/evidence/p09-149-signed-basic-opt.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(windows, args.task, args.inventory_run)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_optimized_signed_tests import OptimizedSignedTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(n) for n in (SELF, TEST, PARENT_SUMMARY, ARCHIVE, STOP_PIN["path"])]
    with patch("subprocess.Popen", side_effect=AssertionError("BASIC_OPT_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("BASIC_OPT_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("BASIC_OPT_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(OptimizedSignedTests))
    reader.finish()
    failed = sorted({t.id().split(".")[-1] for t,_ in result.failures+result.errors+result.skipped})
    passed = result.testsRun == 12 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_BASIC_OPT_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(failed), "failed_tests": failed,
        "source_freeze": freeze, "source_freeze_exact_after": True, "product_complete": False,
        "P09_gate": "OPEN", "Cargo_SQL_native_executed": False}
    with destination.open("x", encoding="utf-8") as stream: json.dump(row, stream, indent=2)
    print(json.dumps({key:row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        raise SystemExit(run_worker(sys.argv[3]))
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error,ValueError) and re.fullmatch(r"[A-Z_]+",str(error)) else "BASIC_OPT_OPERATION_FAILED"
        print(json.dumps({"state":"FAILED_NOT_ACCEPTED", "error_code":code}))
        raise SystemExit(2) from None
