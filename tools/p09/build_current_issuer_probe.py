"""Current-source issuer example build in an isolated target, never SQL/native product execution.

기존 source842/helper19/protected50 후보를 다시 결합하고 전체 final hash 이후에만
build-only PASS한다. Job compiler supervisor의 target-dir 인자 하나만 명시적으로 변환한다.
"""
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import conservative_maintenance as c
import current_issuer_build_inputs as inputs
import owned_probe_build as compiler
from owned_sql_job import OwnedSQLJobProcess
from sql_percentage_resources import PercentageResources
from bounded_process_progress import bounded_observation_run, BoundedProcessCapture

CANDIDATE_PIN = {"path": "implementation/p09/evidence/p09-149-current-issuer-build-inputs.run02.v1.json",
    "bytes": 223262, "sha256": "b40eaf4bf8ac807fa795433ede7dcec1dc4fe609bcc959ff327799229219e689"}
OWN_SOURCES = ["tools/p09/build_current_issuer_probe.py", "tools/p09/tests/test_build_current_issuer_probe.py",
    "tools/p09/verify_build_current_issuer_probe_light.py",
    "implementation/p09/source-archive/p09-149-pre-current-compiler-rustup-resolution/source-preimages.v1.json",
    "target/p09-149-current-issuer-build/current-issuer-build-r1.json",
    "implementation/p09/source-archive/p09-149-pre-current-compiler-progress-observation/source-preimages.v1.json",
    "target/p09-149-current-issuer-build/current-issuer-build-r3.json",
    "implementation/p09/source-archive/p09-149-pre-current-compiler-observation-freshness/source-preimages.v1.json"]
CONFIG_NAMES = ("rust-toolchain", "rust-toolchain.toml", ".cargo/config", ".cargo/config.toml")
OVERRIDES = ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "RUSTC", "CARGO_BUILD_TARGET")
PASS = "PASS_CURRENT_SOURCE_PROBE_BUILD_ONLY_NOT_SQL_PRODUCT_OR_GATE"
PROJECT_CRATES = frozenset({"domain-ir", "hwpx-package", "hwpx-agent-cli"})
MAX_OBSERVATION_AGE_SECONDS = 4*c.POLICY["sample_seconds"]


def require(ok, code):
    c.require(ok, "CURRENT_COMPILER_"+code)


class CurrentCompilerResources(PercentageResources):
    """Alive is not fresh: a stalled watcher cannot authorize IO or compiler GO.

    사전 IO는 기존 manual sampler를 유지한다. runtime에서 두 번째 sampler를
    만들지 않고 마지막 완료 표본의 나이만 확인하며, 원래 Job/전체 host 정책은 유지한다.
    """
    def _check_observation_freshness(self):
        observed = self.last_sample_at
        now = time.monotonic()
        try:
            c.require(type(observed) in (int, float) and math.isfinite(observed)
                and type(now) in (int, float) and math.isfinite(now) and now >= observed,
                "STOP_RESOURCE_CLOCK_INVALID")
            c.require(now-observed <= MAX_OBSERVATION_AGE_SECONDS,
                "STOP_RESOURCE_OBSERVATION_STALE")
        except ValueError as error:
            self._failed(str(error))
            raise

    def checkpoint_io(self):
        # Check a live-but-stalled runtime watcher BEFORE the shared checkpoint;
        # pre-hash must first let the original manual sampler refresh its sample.
        if self.thread.ident is not None:
            self._check_observation_freshness()
        super().checkpoint_io()
        self._check_observation_freshness()


def project_announcement(capture):
    with capture.lock:
        raw = bytes(capture.buffers["stderr"])
    require(len(raw) <= compiler.MAX_OUTPUT, "PROGRESS_BUFFER_BUDGET")
    latest = None
    # Only COMPLETE Cargo announcements, not proof of current Rustc/LLVM/link stage.
    for line in raw.split(b"\n")[:-1]:
        match = re.match(rb"[ \t]*(Compiling|Checking)[ \t]+([a-z][a-z0-9-]*)(?:[ \t]|$)", line)
        if match and match[2].decode("ascii") in PROJECT_CRATES:
            latest = {"stage": match[1].decode("ascii"), "package": match[2].decode("ascii")}
    return latest


class ProgressCompilerCapture(BoundedProcessCapture):
    def __init__(self, *args, receipt, **kwargs):
        self.receipt = receipt
        super().__init__(*args, **kwargs)

    def communicate(self, timeout):
        try:
            return super().communicate(timeout)
        finally:
            self.receipt["last_project_cargo_announcement"] = project_announcement(self)


def output_paths(root, variant):
    require(isinstance(variant, str) and re.fullmatch(r"r[1-9][0-9]{0,5}", variant), "VARIANT_SCOPE")
    inputs.target_contract(root)
    target = root/inputs.CURRENT_TARGET
    receipt = target/f"current-issuer-build-{variant}.json"
    executable = target/f"debug/examples/{compiler.EXAMPLE}-p143-{variant}.exe"
    preflight_failure = root/f"implementation/p09/evidence/p09-149-current-issuer-build-{variant}.preflight-failure.v1.json"
    for path in (receipt, executable, preflight_failure):
        require(not path.exists() and not path.is_symlink() and not path.is_junction(), "FRESH_OUTPUT_REQUIRED")
    for name in ("debug", "debug/examples", "debug/deps", "debug/build", "debug/incremental", "debug/.fingerprint"):
        directory = target/name
        require(not directory.is_symlink() and not directory.is_junction()
            and (not directory.exists() or directory.is_dir()), "TARGET_OUTPUT_LINK_OR_FILE")
    return target, receipt, executable


def candidate_contract(candidate):
    require(candidate.get("schema_version") == "hwpx-agent.p09-current-issuer-build-inputs/v1"
        and candidate.get("state") == "PASS_CURRENT_BUILD_INPUTS_ONLY_NOT_COMPILE_SQL_PRODUCT_OR_GATE"
        and candidate.get("current_build_input_candidate_accepted") is True
        and candidate.get("compiler_build_binding_accepted") is False
        and candidate.get("actual_build_SQL_Docker_Cargo_native_or_child_run") is False
        and candidate.get("mutex_cleanup_confirmed") is True, "CANDIDATE_NOT_ACCEPTED")
    for flag in ("source_freeze_exact_after", "build_helper_freeze_exact_after", "protected_executables_exact_after",
            "whole_workspace_Rust_input_coverage_enforced", "historical_parent_archive_verified", "historical_protected_closure_exact"):
        require(candidate.get(flag) is True, "CANDIDATE_COVERAGE_MISSING")
    source = inputs.inventory(candidate["source_freeze"], 842)
    helper = inputs.inventory(candidate["build_helper_freeze"], 19)
    protected = inputs.inventory(candidate["protected_executables"], 50)
    require(set(candidate["declared_source_delta_paths"]) == inputs.RUST_CHANGES|{inputs.BUILDER}
        and len(candidate["declared_source_delta_paths"]) == 10
        and candidate["historical_source_inventory"] == 817 and candidate["whole_workspace_Rust_inputs"] == 781,
        "CANDIDATE_INVENTORY_SCOPE")
    require(set(helper) == set(compiler.SOURCES+['tools/p09/tests/test_owned_sql_job.py']+inputs.EXTRA), "CANDIDATE_HELPER_CLOSURE")
    require(candidate["target_contract"] == inputs.target_contract(c.ROOT), "CANDIDATE_TARGET_SCOPE")
    require(candidate["baseline_build_pin"]["path"] == inputs.BASELINE
        and [pin["path"] for pin in candidate["reviewed_delta_evidence_pins"]] == [inputs.DRIFT_AUDIT, inputs.SUPERVISOR],
        "CANDIDATE_PROVENANCE_SCOPE")
    return source, helper, protected


def validate_environment(env):
    require(isinstance(env, dict) and all(not env.get(name) for name in OVERRIDES), "UNREVIEWED_COMPILER_OVERRIDE")
    expected = {"CARGO_PROFILE_DEV_OPT_LEVEL": "1", "CARGO_PROFILE_DEV_DEBUG": "line-tables-only",
        "CARGO_PROFILE_DEV_DEBUG_ASSERTIONS": "true", "CARGO_PROFILE_DEV_OVERFLOW_CHECKS": "true",
        "CARGO_PROFILE_DEV_CODEGEN_UNITS": "16", "CARGO_INCREMENTAL": "0", "RUSTUP_AUTO_INSTALL": "0"}
    require(all(env.get(name) == value for name, value in expected.items()), "PROFILE_ENVIRONMENT_DRIFT")


def launch_current(args, *, cargo, variant, process_type=OwnedSQLJobProcess, **kwargs):
    require(args == compiler.build_arguments(cargo, variant), "ARGUMENT_TRANSLATION_SCOPE")
    require(kwargs.get("cwd") == c.ROOT and kwargs.get("allowed_executables") == [cargo], "PROCESS_ALLOWLIST_SCOPE")
    validate_environment(kwargs.get("env"))
    actual = list(args)
    index = actual.index("--target-dir")+1
    require(actual[index] == str(compiler.TARGET), "LEGACY_TARGET_ARGUMENT_MISSING")
    actual[index] = str(c.ROOT/inputs.CURRENT_TARGET)
    return process_type(actual, **kwargs)


def cargo_output_path(output, rustup_home):
    require(isinstance(output, str) and len(output.encode("utf-8")) <= 16384
        and len(output.strip().splitlines()) == 1, "RUSTUP_WHICH_OUTPUT_SCOPE")
    cargo = Path(output.strip())
    require(cargo.is_absolute() and cargo.name.lower() == "cargo.exe" and cargo.is_file()
        and not cargo.is_symlink() and not cargo.is_junction(), "RESOLVED_CARGO_NOT_DIRECT_FILE")
    require(cargo.resolve().is_relative_to((rustup_home/"toolchains").resolve())
        and cargo.parent.name == "bin", "RESOLVED_CARGO_OUTSIDE_TOOLCHAINS")
    return str(cargo)


def resolve_cargo(resources, *, runner=bounded_observation_run, which=shutil.which,
        process_type=OwnedSQLJobProcess):
    hint = which("cargo")
    require(hint is not None, "CARGO_MISSING")
    shim = Path(hint)
    require(shim.is_absolute() and shim.is_file() and shim.name.lower() == "cargo.exe", "CARGO_HINT_SCOPE")
    if not shim.is_symlink() and not shim.is_junction():
        return str(shim), {"rustup_resolver_used": False, "cargo_path": str(shim), "owned_resolver_job_profile": None}
    rustup = shim.resolve(strict=True)
    require(rustup.is_file() and not rustup.is_symlink() and not rustup.is_junction()
        and rustup.name.lower() == "rustup.exe", "CARGO_SHIM_TARGET_NOT_RUSTUP")
    flags = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS
    holders = []
    def factory(command, **kwargs):
        require(command == [str(rustup), "which", "cargo"] and kwargs.get("cwd") == c.ROOT
            and kwargs.get("creationflags") == flags and kwargs.get("stdin") == kwargs.get("stdout") == kwargs.get("stderr") == subprocess.PIPE
            and kwargs.get("text") is True and kwargs.get("encoding") == "utf-8" and kwargs.get("errors") == "replace", "RUSTUP_RESOLVER_LAUNCH_SCOPE")
        child = process_type(command, windows=resources.windows, allowed_executables=[str(rustup)],
            cwd=c.ROOT, checkpoint=resources.checkpoint_io, env=compiler.build_environment())
        holders.append(child)
        return child
    result = runner([str(rustup), "which", "cargo"], cwd=c.ROOT, timeout=3, creationflags=flags, process_factory=factory)
    require(result.returncode == 0 and len(holders) == 1, "RUSTUP_WHICH_FAILED")
    profile = holders[0].profile
    require(profile.get("cleanup_confirmed") is True and profile.get("owned_tree_empty") is True
        and profile.get("job_handle_closed") is True and (profile.get("limits_readback") or {}).get("verified") is True,
        "RUSTUP_RESOLVER_CLEANUP_NOT_CONFIRMED")
    home = Path(os.environ.get("RUSTUP_HOME", str(Path.home()/".rustup")))
    cargo = cargo_output_path(result.stdout, home)
    return cargo, {"rustup_resolver_used": True, "cargo_path": cargo, "owned_resolver_job_profile": dict(profile)}


def current_receipts(root):
    directory = root/inputs.CURRENT_TARGET
    names = sorted(directory.glob("current-issuer-build-r*.json")) if directory.exists() else []
    require(len(names) <= 128, "CURRENT_BUILD_HISTORY_BUDGET")
    return [path.relative_to(root).as_posix() for path in names]


def previous_current_protection(reader, names):
    rows = []
    for name in names:
        old = reader.json(name)
        if old.get("state") != PASS:
            continue
        require(old.get("compiler_build_binding_accepted") is True and old.get("source_freeze_exact_after") is True
            and old.get("build_helper_freeze_exact_after") is True and old.get("protected_executables_exact_after") is True
            and compiler.accepted(old), "PREVIOUS_CURRENT_BUILD_CONTRACT")
        pin = inputs.pin_shape(old["executable_pin"])
        require(re.fullmatch(r"target/p09-149-current-issuer-build/debug/examples/formula_issuer_product_postgres_probe-p143-r[1-9][0-9]*\.exe", pin["path"]),
            "PREVIOUS_CURRENT_EXECUTABLE_SCOPE")
        rows.append(pin)
    if rows:
        inputs.inventory(rows)
    return rows


def build_accepted(row):
    return compiler.accepted(row) and all(row.get(flag) is True for flag in
        ("source_freeze_exact_after", "build_helper_freeze_exact_after", "protected_executables_exact_after")) \
        and isinstance(row.get("executable_pin"), dict) and row["executable_pin"].get("path") == \
        f"{inputs.CURRENT_TARGET}/debug/examples/{compiler.EXAMPLE}-p143-{row.get('variant')}.exe" \
        and row.get("actual_SQL_or_native_product_executed") is False


def bind_inputs(reader, root):
    require(reader.fresh_pin(CANDIDATE_PIN["path"]) == CANDIDATE_PIN, "CANDIDATE_RECEIPT_DRIFT")
    candidate = reader.json(CANDIDATE_PIN["path"])
    source, helper, protected = candidate_contract(candidate)
    for pin in [candidate["baseline_build_pin"]]+candidate["reviewed_delta_evidence_pins"]:
        require(reader.fresh_pin(inputs.pin_shape(pin)["path"]) == pin, "PROVENANCE_RECEIPT_DRIFT")
    baseline, old_protected = inputs.baseline_contract(reader.json(inputs.BASELINE))
    approved, _ = inputs.reviewed_deltas(reader.json(inputs.DRIFT_AUDIT), reader.json(inputs.SUPERVISOR))
    current, changed = inputs.bind_current_sources(reader, baseline, approved)
    require(current == list(source.values()) and sorted(changed) == sorted(candidate["declared_source_delta_paths"])
        and protected == old_protected, "CURRENT_CANDIDATE_BINDING_DRIFT")
    for name, pin in helper.items():
        require(reader.fresh_pin(name) == pin, "CANDIDATE_HELPER_DRIFT")
    legacy_names = inputs.historical_receipts(root)
    require(inputs.protected_closure(reader, legacy_names) == protected, "LEGACY_PROTECTION_CLOSURE_DRIFT")
    prior_names = current_receipts(root)
    prior = previous_current_protection(reader, prior_names)
    all_protected = list(protected.values())+prior
    inputs.inventory(all_protected, 50+len(prior))
    for pin in all_protected:
        require(reader.fresh_pin(pin["path"]) == pin, "PROTECTED_EXECUTABLE_DRIFT")
    helper_rows = list(helper.values())+[reader.fresh_pin(name) for name in OWN_SOURCES]+[CANDIDATE_PIN]
    configuration = [reader.fresh_pin(name) for name in CONFIG_NAMES if (root/name).exists()]
    helper_rows += [pin for pin in configuration if pin["path"] not in {row["path"] for row in helper_rows}]
    inputs.inventory(helper_rows)
    return {"source_freeze": current, "build_helper_freeze": helper_rows, "protected_executables": all_protected,
        "declared_source_delta_paths": changed, "configuration_pins": configuration,
        "baseline_candidate_pin": CANDIDATE_PIN, "historical_parent_archive_verified": True,
        "whole_workspace_Rust_input_coverage_enforced": True}, legacy_names, prior_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True)
    parser.add_argument("--maximum-seconds", type=int, choices=range(30, 601), default=120)
    args = parser.parse_args()
    require(Path.cwd().resolve() == c.ROOT, "WRONG_ROOT")
    target, destination, executable = output_paths(c.ROOT, args.variant)
    resources = CurrentCompilerResources()
    started = time.monotonic()
    reader = mutex = None
    lock_owned = False
    row = {"schema_version": "hwpx-agent.p09-current-issuer-build/v1", "state": "NOT_ACCEPTED_STOP_OR_FAILURE",
        "variant": args.variant, "operation_phase": "admission", "compiler_build_binding_accepted": False,
        "source_freeze_exact_after": False, "build_helper_freeze_exact_after": False,
        "protected_executables_exact_after": False, "executable_pin": None, "mutex_cleanup_confirmed": False,
        "compiler_started": False, "stop_reason": None, "samples": resources.samples,
        "actual_SQL_or_native_product_executed": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False, "maximum_seconds": args.maximum_seconds,
        "total_scope_limit_seconds": 690, "output_limit_bytes_per_stream": compiler.MAX_OUTPUT,
        "logical_cpu_limit": 1, "priority": "BelowNormal", "cargo_jobs": 1,
        "maximum_completed_resource_sample_age_seconds": MAX_OBSERVATION_AGE_SECONDS,
        "target_directory": inputs.CURRENT_TARGET}
    row["last_project_cargo_announcement"] = None
    try:
        ctypes.set_last_error(0)
        mutex = resources.windows.k.CreateMutexW(None, True, compiler.MUTEX)
        duplicate = ctypes.get_last_error() == 183
        require(mutex, "LOCK_FAILED")
        lock_owned = not duplicate
        require(lock_owned, "ALREADY_RUNNING")
        resources.admit()
        validate_environment(compiler.build_environment())
        require(shutil.disk_usage(c.ROOT).free >= 5*1024**3, "TARGET_DISK_HEADROOM")
        def checkpoint():
            require(time.monotonic()-started <= 690, "TOTAL_SCOPE_TIME_LIMIT")
            resources.checkpoint_io()
        reader = inputs.BuildInputReader(c.ROOT, checkpoint)
        row["operation_phase"] = "current_input_binding"
        print("P149_CURRENT_BUILD_PHASE:current_input_binding", flush=True)
        binding, legacy_names, prior_names = bind_inputs(reader, c.ROOT)
        row.update(binding)
        rust_before = inputs.rust_inputs(c.ROOT, checkpoint)
        require(len(rust_before) == 781 and rust_before.issubset({pin["path"] for pin in row["source_freeze"]}), "RUST_INPUT_COVERAGE_DRIFT")
        output_paths(c.ROOT, args.variant)
        target.mkdir(exist_ok=True)  # This exact new target only; never cleans or rewrites the legacy target.
        row["operation_phase"] = "read_only_rustup_cargo_resolution"
        cargo, resolution = resolve_cargo(resources)
        row["toolchain_resolution"] = resolution
        resources.start()
        row["operation_phase"] = "bounded_compiler"
        print("P149_CURRENT_BUILD_PHASE:bounded_compiler", flush=True)
        row.update(compiler.compile_owned(resources, cargo, args.variant, args.maximum_seconds,
            process_factory=lambda command, **kwargs: launch_current(command, cargo=cargo, variant=args.variant, **kwargs),
            capture_factory=lambda *capture_args, **kwargs: ProgressCompilerCapture(*capture_args, receipt=row, **kwargs)))
        row["operation_phase"] = "final_source_helper_protected_binding"
        print("P149_CURRENT_BUILD_PHASE:final_source_helper_protected_binding", flush=True)
        if executable.exists():
            row["executable_pin"] = reader.fresh_pin(executable.relative_to(c.ROOT).as_posix())
        reader.finish()
        row["source_freeze_exact_after"] = row["build_helper_freeze_exact_after"] = row["protected_executables_exact_after"] = True
        require(inputs.rust_inputs(c.ROOT, checkpoint) == rust_before, "RUST_INVENTORY_CHANGED")
        require(inputs.historical_receipts(c.ROOT) == legacy_names and current_receipts(c.ROOT) == prior_names, "HISTORY_INVENTORY_CHANGED")
        inputs.target_contract(c.ROOT)
        if build_accepted(row):
            row["state"] = PASS
            row["compiler_build_binding_accepted"] = True
    except (ValueError, OSError, KeyError, TypeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "CURRENT_COMPILER_INPUT_OR_OBSERVATION_FAILURE"
        row["stop_reason"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "CURRENT_COMPILER_REDACTED_FAILURE"
    finally:
        resources.done.set()
        failed = False
        if resources.thread.ident is not None:
            resources.thread.join(2)
            failed = resources.thread.is_alive()
        if resources.stop.is_set():
            row["stop_reason"] = resources.reason or "resource_stop"
        if mutex is not None:
            if lock_owned and not resources.windows.k.ReleaseMutex(mutex):
                failed = True
            if not resources.windows.k.CloseHandle(mutex):
                failed = True
        row["mutex_cleanup_confirmed"] = not failed
        if failed:
            row["stop_reason"] = "CURRENT_COMPILER_WATCHER_OR_MUTEX_CLEANUP_FAILED"
        if row["stop_reason"]:
            row["state"] = "NOT_ACCEPTED_STOP_OR_FAILURE"
            row["compiler_build_binding_accepted"] = False
        if reader is not None:
            row["bounded_input_IO"] = {"read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
                "bound_inputs": len(reader.snapshots), "final_fresh_hashes": reader.final_fresh_hashes}
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        # Failure before target creation must still leave an exclusive diagnostic receipt in evidence.
        if not target.exists():
            destination = c.ROOT/f"implementation/p09/evidence/p09-149-current-issuer-build-{args.variant}.preflight-failure.v1.json"
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({"state": row["state"], "compiler_started": row["compiler_started"],
            "stop_reason": row["stop_reason"], "elapsed_seconds": row["elapsed_seconds"],
            "receipt": destination.relative_to(c.ROOT).as_posix()}))
    return 0 if row["state"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
