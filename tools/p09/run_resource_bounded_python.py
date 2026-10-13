"""P145 opt-in in-process launch: CPU/priority limits precede all target hashes.

기존 P144 증거와 검증 코드를 수정하지 않는다. 이 진입점의 안정 구간은
사전 검사 전 admission이며, 대상의 post-hash admission/continuous stop을
대체하지 않는다. 새로운 DB/native/product qualification이 아니다.
"""
import argparse
import contextlib
import ctypes
import json
from pathlib import Path
import re
import runpy
import sys
import time

from check_idle_resource_window import MAX_SECONDS, REQUIRED, SAMPLE_SECONDS, stable_count
from run_formula_issuer_registry_sql_checks import ROOT, Resources, pin, require

SELF = "tools/p09/run_resource_bounded_python.py"
HELPERS = [
    "tools/p09/run_formula_issuer_registry_sql_checks.py",
    "tools/p09/check_idle_resource_window.py",
    "tools/p09/idle_resource_admission.py",
]
TARGETS = {
    "current-audit": (
        "tools/p09/verify_formula_issuer_corpus_current.py",
        r"implementation/p09/evidence/p09-144-corpus-consumer\.progress\.v[1-9][0-9]*\.json",
        "CURRENT_ORIGINAL_AND_RAM_DERIVATIVE_CHANGED_SQL22_COMPONENT_PASS_NOT_NATIVE_OR_GATE",
    ),
    "unit": (
        "tools/p09/run_formula_issuer_corpus_unit_probe.py",
        r"target/p09-121-resource-optimized/p144-corpus-unit-run[1-9][0-9]*\.json",
        "PASS_TYPED_ROUTE_AND_SOURCE_INDEX_UNIT11_NOT_DB_NATIVE_OR_GATE",
    ),
    "sql": (
        "tools/p09/run_formula_issuer_corpus_probe.py",
        r"implementation/p09/evidence/p09-144-corpus-consumer-run[0-9]{2}\.v1\.json",
        "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE",
    ),
}


class BoundedOutput:
    """대상 로그는 전달하지 않으며 과도한 출력은 fail-closed한다."""

    def __init__(self, limit=32768):
        self.limit = limit
        self.count = 0

    def write(self, value):
        self.count += len(value.encode("utf-8"))
        require(self.count <= self.limit, "target_output_limit_exceeded")
        return len(value)

    def flush(self):
        pass


def observed_limits(resources):
    affinity, system = ctypes.c_size_t(), ctypes.c_size_t()
    resources.k.GetProcessAffinityMask.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
    ]
    resources.k.GetProcessAffinityMask.restype = ctypes.c_int
    resources.k.GetPriorityClass.argtypes = [ctypes.c_void_p]
    resources.k.GetPriorityClass.restype = ctypes.c_uint32
    require(resources.k.GetProcessAffinityMask(resources.handle, ctypes.byref(affinity), ctypes.byref(system)),
        "bootstrap_affinity_observation_failed")
    priority = resources.k.GetPriorityClass(resources.handle)
    require(affinity.value == 1 and priority == 0x4000, "bootstrap_limits_not_exact")
    return {"affinity_mask": affinity.value, "priority_class": priority,
        "logical_cpu_limit": 1, "priority": "BelowNormal"}


def admit(resources, sleep=time.sleep, clock=time.monotonic):
    deadline, count = clock() + MAX_SECONDS, 0
    while clock() < deadline:
        sleep(SAMPLE_SECONDS)
        sample = resources.sample()
        require(not resources.stop.is_set(), resources.reason or "bootstrap_resource_stop")
        count = stable_count(count, sample)
        if count >= REQUIRED:
            return count
    require(False, "bootstrap_idle_window_not_admitted")


def target_arguments(args):
    require(args.mode in TARGETS, "target_not_allowlisted")
    target, receipt_pattern, _ = TARGETS[args.mode]
    require(re.fullmatch(receipt_pattern, args.target_receipt), "target_receipt_scope")
    result = ["--receipt", args.target_receipt]
    if args.mode == "current-audit":
        require(args.build_receipt is None and args.source_index is None and args.input_mode is None
            and args.expected_outcome is None, "audit_accepts_no_execution_options")
    else:
        build_pattern = (r"target/p09-121-resource-optimized/p143-typed-route-unit-build-r[1-9][0-9]*\.json"
            if args.mode == "unit" else r"target/p09-121-resource-optimized/p143-issuer-product-build-r[1-9][0-9]*\.json")
        require(isinstance(args.build_receipt, str) and re.fullmatch(build_pattern, args.build_receipt), "build_receipt_scope")
        result += ["--build-receipt", args.build_receipt]
        if args.mode == "unit":
            require(args.source_index is None and args.input_mode is None and args.expected_outcome is None,
                "unit_accepts_no_SQL_options")
        else:
            require(type(args.source_index) is int and 0 <= args.source_index < 36, "source_index_scope")
            require(args.input_mode in ("original", "numeric_derivative"), "input_mode_scope")
            require(args.expected_outcome in ("changed", "unchanged"), "outcome_scope")
            result += ["--source-index", str(args.source_index), "--input-mode", args.input_mode,
                "--expected-outcome", args.expected_outcome]
    return target, result


def run_target(target, arguments, runner=runpy.run_path):
    # 동일 프로세스이므로 대상의 import/사전 hash도 이미 제한된 CPU에서 실행된다.
    saved = sys.argv
    stdout, stderr = BoundedOutput(), BoundedOutput()
    code = 0
    try:
        sys.argv = [str(ROOT / target), *arguments]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                runner(str(ROOT / target), run_name="__main__")
            except SystemExit as error:
                require(error.code is None or type(error.code) is int, "target_exit_not_numeric")
                code = 0 if error.code is None else error.code
    finally:
        sys.argv = saved
    return code, {"stdout_bytes_discarded": stdout.count, "stderr_bytes_discarded": stderr.count}


def fresh_file(path):
    destination = ROOT / path
    require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "fresh_local_receipt_required")
    return destination


def main(args):
    # 첫 영향 있는 작업: 대상/manifest/EXE를 읽기 전에 현재 프로세스를 제한한다.
    resources = Resources()
    limits_before = observed_limits(resources)
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    require(re.fullmatch(r"implementation/p09/evidence/p09-145-resource-bootstrap-run[0-9]{2}\.v1\.json", args.receipt),
        "bootstrap_receipt_scope")
    destination = fresh_file(args.receipt)
    target, arguments = target_arguments(args)
    target_destination = fresh_file(args.target_receipt)
    result = {"schema_version": "hwpx-agent.p09-145-resource-bootstrap/v1", "state": "PENDING",
        "mode": args.mode, "limits_before_target_and_hashes": limits_before,
        "target_started": False, "target_exit_code": None, "target_receipt": None,
        "P09_gate": "OPEN", "product_complete": False,
        "target_post_hash_and_continuous_guards_replaced": False,
        "bootstrap_continuous_stop_implemented": False,
        "native_application_started_by_bootstrap": False}
    started = time.monotonic()
    try:
        result["pre_hash_stable_samples"] = admit(resources)
        sources = [SELF, *HELPERS, target]
        freeze = [pin(path) for path in sources]
        result["source_freeze"] = freeze
        result["limits_immediately_before_target"] = observed_limits(resources)
        result["target_started"] = True
        code, discarded = run_target(target, arguments)
        result["target_exit_code"], result["output"] = code, discarded
        result["limits_after_target"] = observed_limits(resources)
        require(code == 0, "target_failed_no_bootstrap_acceptance")
        require(target_destination.is_file() and target_destination.stat().st_size <= 1048576, "target_receipt_missing_or_oversized")
        target_result = json.loads(target_destination.read_text(encoding="utf-8-sig"))
        require(target_result.get("state") == TARGETS[args.mode][2]
            and target_result.get("P09_gate") == "OPEN" and target_result.get("product_complete") is False,
            "target_acceptance_or_scope_not_exact")
        result["target_receipt"] = pin(args.target_receipt)
        result["target_state"] = target_result["state"]
        result["source_freeze_exact_after"] = [pin(path) for path in sources] == freeze
        require(result["source_freeze_exact_after"], "bootstrap_or_target_source_drift")
        result["state"] = "PASS_PRE_HASH_RESOURCE_BOUND_TARGET_ACCEPTED_NOT_NATIVE_OR_GATE"
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        result["state"] = "FAIL_CLOSED_RESOURCE_BOOTSTRAP_NOT_PRODUCT_ACCEPTANCE"
        result["error_code"] = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
    finally:
        result["pre_hash_admission_samples"] = resources.samples
        result["pre_hash_admission_stop_reason"] = resources.reason
        result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"state": result["state"], "target_started": result["target_started"],
        "target_exit_code": result["target_exit_code"], "receipt": args.receipt,
        "error_code": result.get("error_code"), "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=list(TARGETS), required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--target-receipt", required=True)
    parser.add_argument("--build-receipt")
    parser.add_argument("--source-index", type=int)
    parser.add_argument("--input-mode")
    parser.add_argument("--expected-outcome")
    args = parser.parse_args()
    try:
        raise SystemExit(main(args))
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED_BEFORE_TARGET", "error_code": code}))
        raise SystemExit(1) from None
