"""Run the six exact typed route tests, single CPU/thread. No DB/native/product qualification."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import subprocess
import time

from run_formula_issuer_registry_sql_checks import ROOT, Resources, pin, require
from idle_resource_admission import IdleResources

EXPECTED = sorted("source::route_tests::" + name for name in [
    "accepts_only_exact_unchanged_route_denial", "accepts_only_exact_changed_route_denial",
    "rejects_signature_and_policy_failures_as_route_success", "rejects_wrong_outcome_route_branch",
    "rejects_product_route_success", "rejects_unknown_outcome",
])


def main(build_path, receipt_path):
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    require(re.fullmatch(r"target/p09-121-resource-optimized/p143-typed-route-unit-build-r[1-9][0-9]*\.json", build_path), "build_receipt_scope")
    require(re.fullmatch(r"target/p09-121-resource-optimized/p143-typed-route-unit-run[1-9][0-9]*\.json", receipt_path), "unit_receipt_scope")
    destination = ROOT / receipt_path
    require(not destination.exists(), "fresh_receipt_required")
    build = json.loads((ROOT / build_path).read_text(encoding="utf-8-sig"))
    require(build["state"] == "PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION"
        and build["exit_code"] == 0 and build["catalog_profile"]["test"] is True
        and build["source_freeze_exact_after"] and build["protected_executables_exact_after"]
        and build["logical_cpu_limit"] == build["cargo_jobs"] == 1 and not build["diagnostics"], "unit_build_not_accepted")
    executable = build["executable_pin"]
    require(re.fullmatch(r"target/p09-121-resource-optimized/debug/examples/formula_issuer_product_postgres_probe-p143-unit-r[1-9][0-9]*\.exe", executable["path"]), "unit_executable_scope")
    require(pin(executable["path"]) == executable, "unit_executable_drift")
    freeze = list(build["source_freeze"])
    require(len(freeze) == 843 and all(pin(p["path"]) == p for p in freeze), "unit_source_drift")
    freeze += [pin(build_path), pin("tools/p09/run_formula_issuer_product_unit_probe.py"),
        pin("tools/p09/idle_resource_admission.py"), pin("tools/p09/check_idle_resource_window.py")]
    protected = list(build["protected_executables"]) + [executable]
    require(len(protected) == len({p["path"] for p in protected}) and all(pin(p["path"]) == p for p in protected), "unit_protected_drift")
    resources = IdleResources()
    process = None
    start = time.monotonic()
    result = {
        "schema_version": "hwpx-agent.p09-143-typed-route-unit-run/v1", "state": "NOT_RUN",
        "source_freeze": freeze, "protected_executables": protected, "executable_pin": executable,
        "source_freeze_exact_after": False, "protected_executables_exact_after": False,
        "tests": [], "test_process_started": False, "actual_DB_or_native_executed": False,
        "logical_cpu_limit": 1, "priority": "BelowNormal", "test_threads": 1,
        "post_hash_idle_policy": {"CPU_max_percent": 50, "RAM_min_mib": 8192, "consecutive_samples": 3},
        "P09_gate": "OPEN", "product_complete": False,
    }
    try:
        resources.start()
        process = subprocess.Popen([str(ROOT / executable["path"]), "--test-threads=1"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        result["test_process_started"] = True
        affinity, system = ctypes.c_size_t(), ctypes.c_size_t()
        resources.k.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
        resources.k.GetPriorityClass.argtypes = [ctypes.c_void_p]
        require(resources.k.GetProcessAffinityMask(int(process._handle), ctypes.byref(affinity), ctypes.byref(system))
            and affinity.value == 1 and resources.k.GetPriorityClass(int(process._handle)) == 0x4000, "unit_limits_not_inherited")
        while True:
            try:
                output, errors = process.communicate(timeout=0.25)
                break
            except subprocess.TimeoutExpired:
                require(not resources.stop.is_set(), resources.reason or "resource_stop")
                require(time.monotonic() - start < 30, "unit_duration_limit")
        result["exit_code"] = process.returncode
        require(len(output) <= 16384 and not errors, "unit_closed_output_protocol")
        result["tests"] = sorted(re.findall(r"^test (source::route_tests::[a-z_]+) \.\.\. ok$", output, re.MULTILINE))
        summary = re.search(r"^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;", output, re.MULTILINE)
        require(process.returncode == 0 and result["tests"] == EXPECTED
            and summary is not None and tuple(map(int, summary.groups())) == (6, 0, 0, 0, 0), "exact_unit6_not_passed")
        require(all(pin(p["path"]) == p for p in freeze), "unit_source_changed")
        require(all(pin(p["path"]) == p for p in protected), "unit_executable_changed")
        result["source_freeze_exact_after"] = result["protected_executables_exact_after"] = True
        result["state"] = "PASS_TYPED_ROUTE_UNIT6_NOT_DB_NATIVE_OR_GATE"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["state"] = "FAIL_CLOSED"
        result["error_code"] = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[a-zA-Z0-9_]+", str(error)) else "redacted"
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate()
        resources.done.set()
        if resources.thread.is_alive():
            resources.thread.join(timeout=3)
        result["resource_samples"] = resources.samples
        result["resource_stop_reason"] = resources.reason
        result["elapsed_seconds"] = round(time.monotonic() - start, 2)
        if resources.reason:
            result["state"] = "FAIL_CLOSED"
        with destination.open("x", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"state": result["state"], "tests_passed": len(result["tests"]),
            "elapsed_seconds": result["elapsed_seconds"], "receipt": receipt_path}))
    return 0 if result["state"] == "PASS_TYPED_ROUTE_UNIT6_NOT_DB_NATIVE_OR_GATE" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-receipt", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(main(args.build_receipt, args.receipt))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[a-zA-Z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED_BEFORE_UNIT", "error_code": code}))
        raise SystemExit(1) from None
