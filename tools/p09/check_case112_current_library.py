"""Current CLI library typecheck in a fresh target under the original owned Job.

원 P149 승인 token/Job membership/CPU·RAM 비율/원본 정리/출력 상한을 재사용한다.
기존 binary를 새 source로 재표시하지 않으며 현재249 실행 또는 Gate PASS가 아니다.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from unittest.mock import patch

import audit_case112_source_epoch as epoch
import conservative_maintenance as owned
import current_issuer_build_inputs as inputs
import weighted_audit_io as weighted

SELF = "tools/p09/check_case112_current_library.py"
TEST = "tools/p09/tests/test_case112_current_library.py"
AUDIT_PIN = dict(path="implementation/p09/evidence/p09-361-case112-source-epoch-run001.v1.json",
    bytes=164636, sha256="60b495ced9324e5f0daa8286ccc718e87b987776200cdd569736af965f90114b")
ARGS = ["check", "--quiet", "-p", "hwpx-agent-cli", "--lib"]
MARKER = "P112_CURRENT_CLI_LIBRARY_CHECK_COMPLETE\n"
PASS = "PASS_CURRENT_CLI_LIBRARY_TYPECHECK_NOT_TEST_BINARY_RUNTIME_OR_GATE"
RAW_DRIVER = owned.__file__
OVERRIDES = ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER",
             "RUSTC", "CARGO_BUILD_TARGET")


def require(ok, code):
    if not ok:
        # Original driver persists only closed uppercase/underscore codes.
        raise ValueError("P_CURRENT_LIBRARY_CHECK_" + code)


def quiet_completion(output, errors):
    require(output.replace("\r\n", "\n") == MARKER and errors == "",
            "CLEAN_COMPLETE_QUIET_CHECK_OUTPUT")
    return True


def imported_helpers():
    helpers = {SELF, TEST, epoch.SELF, epoch.TEST, "Cargo.toml", "Cargo.lock", AUDIT_PIN["path"]}
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name:
            path = Path(name).absolute()
            if path.is_relative_to(owned.ROOT / "tools/p09") and path.suffix == ".py":
                helpers.add(path.relative_to(owned.ROOT).as_posix())
    helpers.add(Path(RAW_DRIVER).relative_to(owned.ROOT).as_posix())
    return helpers


def task_for(run):
    require(type(run) is int and 1 <= run <= 999, "RUN_RANGE")
    return f"case112-lib-check-r{run:03}"


def target_for(run):
    task_for(run)
    return owned.ROOT / "target" / f"p09-361-case112-current-lib-check-r{run:03}"


def worker(task):
    require(type(task) is str and re.fullmatch(r"case112-lib-check-r[0-9]{3}", task), "WORKER_TASK")
    run = int(task[-3:])
    require(task == task_for(run), "WORKER_GENERATION")
    target = target_for(run)
    require(not target.exists() and not target.is_symlink() and not target.is_junction(), "FRESH_TARGET")
    raw_call = subprocess.call
    def call(argv, **kwargs):
        require(argv[1:] == ARGS + ["--locked", "--offline", "--jobs", "1", "--color=never",
            "--target-dir", str(target)], "EXACT_CHECK_ARGUMENTS")
        require(kwargs.get("cwd") == owned.ROOT and kwargs.get("stdin") == subprocess.DEVNULL,
                "EXACT_CHECK_WORKING_DIRECTORY")
        env = dict(kwargs["env"])
        require(all(not env.get(name) for name in OVERRIDES), "AMBIENT_COMPILER_OVERRIDE")
        require(env.get("CARGO_BUILD_JOBS") == "1" and env.get("RUSTUP_AUTO_INSTALL") == "0"
                and env.get("CARGO_PROFILE_DEV_DEBUG_ASSERTIONS") == "true"
                and env.get("CARGO_PROFILE_DEV_OVERFLOW_CHECKS") == "true", "ORIGINAL_CHECK_ENVIRONMENT")
        env["CARGO_INCREMENTAL"] = "0"
        kwargs["env"] = env
        code = raw_call(argv, **kwargs)
        if code == 0:
            print(MARKER, end="", flush=True)
        return code
    with patch.object(owned, "TARGET", target), patch.object(owned, "TASKS", {task: list(ARGS)}), \
            patch.object(subprocess, "call", call):
        return owned.worker(task)


def check(run):
    from bounded_process_progress import BoundedProcessCapture
    require(Path.cwd().resolve() == owned.ROOT, "REPOSITORY_ROOT")
    task, target = task_for(run), target_for(run)
    destination = owned.ROOT / "implementation/p09/evidence" / f"p09-361-case112-current-lib-check-run{run:03}.v1.json"
    require(not destination.exists() and not target.exists(), "FRESH_RECEIPT_AND_TARGET")
    for path in (owned.ROOT, owned.ROOT / "target"):
        require(path.is_dir() and not path.is_symlink() and not path.is_junction(), "DIRECT_TARGET_PARENT")
    captures = []
    selected_names = None
    selected_helpers = None
    audit = None
    accepted = False
    raw_dump = json.dump
    class Capture(BoundedProcessCapture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.accepted_check = False
            captures.append(self)
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                self.accepted_check = quiet_completion(output, errors)
            return output, errors
    def pins(checkpoint=None):
        nonlocal selected_names, selected_helpers, audit
        callback = (lambda: None) if checkpoint is None else checkpoint
        deadline = time.monotonic() + 600
        def guarded():
            callback()
            require(time.monotonic() < deadline, "SOURCE_READ_SCOPE_LIMIT")
        names = inputs.rust_inputs(owned.ROOT, guarded)
        require(epoch.MODULE in names and epoch.LIBRARY in names, "REGISTERED_MODULE_INCLUDED")
        if selected_names is None:
            selected_names = set(names)
        else:
            require(names == selected_names, "RUST_INPUT_INVENTORY_DRIFT")
        helpers = imported_helpers()
        if selected_helpers is None:
            selected_helpers = set(helpers)
        else:
            require(helpers == selected_helpers, "IMPORTED_HELPER_INVENTORY_DRIFT")
        with patch.object(weighted, "BINARY_RATE", 1048576), patch.object(weighted, "OTHER_RATE", 2097152):
            reader = weighted.WeightedReader(owned.ROOT, guarded)
            audit = reader.json(AUDIT_PIN["path"])
            require(reader.snapshots[AUDIT_PIN["path"]] == AUDIT_PIN and audit["state"] == epoch.PASS,
                    "EXACT_SOURCE_EPOCH_AUDIT")
            binary = audit["current_binary_pin"]
            names.update(helpers | {binary["path"]})
            require(len(names) <= 2048, "ALL_SOURCE_INVENTORY_BUDGET")
            result = [reader.pin(name) for name in sorted(names)]
            require(reader.snapshots[epoch.LIBRARY] == audit["current_library_pin"]
                    and reader.snapshots[epoch.MODULE] == audit["current_module_pin"]
                    and reader.snapshots[binary["path"]] == binary, "ADMITTED_INPUT_OR_PROTECTED_BINARY_DRIFT")
            return result
    def write(row, stream, **kwargs):
        nonlocal accepted
        observed = captures[-1] if captures else None
        accepted = (row["state"] == "PASS_SCOPED_NOT_GATE" and row["cleanup_confirmed"] is True
            and row["owned_tree_empty"] is True and observed is not None and observed.accepted_check)
        if row["state"] == "PASS_SCOPED_NOT_GATE":
            row["state"] = PASS if accepted else "STOPPED_NOT_ACCEPTED"
        row.update(schema_version="hwpx-agent.p09-case112-current-library-typecheck/v1",
            source_epoch_audit_pin=AUDIT_PIN, current_CLI_library_typecheck_qualified=accepted,
            whole_workspace_Rust_input_count=len(selected_names or ()),
            whole_workspace_compilation_qualified=False, source_input_bytes_checked_before_after=accepted,
            current_test_executable_built=False, full249_current_qualified=False,
            current_library_bound_to_old_test_binary=False, runtime_tests_executed=False,
            source_overwritten_or_frozen_pins_rebased=False, assertions_and_overflow_checks_retained=True,
            selected_target_directory=target.relative_to(owned.ROOT).as_posix(),
            prior_queue_cases=105, next_case=112, accepted_count_delta=0,
            PC_freeze_resolved=False, A12_gate="OPEN", A13_gate="OPEN")
        return raw_dump(row, stream, **kwargs)
    with patch.object(owned, "__file__", str(owned.ROOT / SELF)), \
            patch.object(owned, "TARGET", target), patch.object(owned, "TASKS", {task: list(ARGS)}), \
            patch.object(owned, "pins", pins), patch("bounded_process_progress.BoundedProcessCapture", Capture), \
            patch.object(json, "dump", write):
        code = owned.run(task, destination, 600)
    return 0 if accepted else (code or 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=int)
    return check(parser.parse_args().run)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        raise SystemExit(worker(sys.argv[3]))
    raise SystemExit(main())
