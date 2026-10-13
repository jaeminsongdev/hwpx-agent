"""P125: 보존 전수 audit는 batch 양쪽, source/resource 검사는 원래 runner로 매 case 수행."""
import argparse
import importlib.util
import json
import subprocess
import time
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "p124_audit", Path(__file__).with_name("audit_single_case_formula_progress.py")
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
R = AUDIT.R


def may_start(status, completed, limit, elapsed, start_budget, last_exit):
    R.P123.require(type(limit) is int and 1 <= limit <= 30
                   and type(start_budget) is int and 1 <= start_budget <= 300,
                   "invalid_batch_bound")
    return (last_exit == 0 and status["next_index"] is not None
            and completed < limit and elapsed < start_budget)


def read_progress(names, freeze):
    rows = [(p.name, json.loads(p.read_bytes()))
            for p in sorted((R.ROOT / R.RUN_DIR).glob("p124-case-*-attempt-*.json"))]
    return R.progress(names, rows, freeze)


def resource_summary(doc):
    # 원래 sampler는 baseline/이미 종료된 child에도0을 기록한다. 양수 WS만 실제 관측으로 요약한다.
    observed = [s["test_working_set_mib"] for s in doc["samples"][1:]
                if s["test_working_set_mib"] > 0]
    return {"test_ram_sampled": bool(observed),
            "max_observed_test_ram_mib": max(observed) if observed else None,
            "minimum_available_ram_mib": min(s["available_ram_mib"] for s in doc["samples"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=25)
    parser.add_argument("--start-budget-seconds", type=int, default=120,
                        help="이 시간이 지나면 새 case 시작 금지; 이미 실행 중인 case는 runner600초 상한")
    args = parser.parse_args()
    may_start({"next_index": 1}, 0, args.cases, 0, args.start_budget_seconds, 0)
    AUDIT.audit()  # immutable 이전 전체 source/checkpoint/runtime 검증: batch 시작.
    R.P123.require(R.BASE.pin(R.EXE) == R.PIN, "executable_drift")
    freeze = json.loads((R.ROOT / R.P123.P121.FREEZE).read_bytes())["source_freeze"]
    listed = subprocess.run([str(R.ROOT / R.EXE), "--list"], cwd=R.ROOT,
                            capture_output=True, text=True, timeout=10, check=False)
    R.P123.require(listed.returncode == 0, "inventory_failed")
    names = R.inventory(listed.stdout)
    status = read_progress(names, freeze)
    start = time.monotonic()
    completed, last_exit = 0, 0
    while may_start(status, completed, args.cases, time.monotonic() - start,
                    args.start_budget_seconds, last_exit):
        index, attempt = status["next_index"], status["next_attempt"]
        R.P123.require(attempt <= 999, "attempt_limit_reached")
        name = names[index - 1]
        receipt = f"{R.RUN_DIR}/p124-case-{index:03d}-attempt-{attempt:03d}.json"
        R.P123.require(not (R.ROOT / receipt).exists(), "receipt_already_exists")
        print(json.dumps({"state": "CASE_STARTING", "index": index, "attempt": attempt}), flush=True)
        run = subprocess.run([
            "pwsh", "-NoProfile", "-File", "tools/p09/run_changed_formula_tests.ps1",
            "-TestExecutable", R.EXE, "-ReceiptPath", receipt, "-TestFilter", name,
            "-LogicalCpuLimit", "1", "-SampleSeconds", "2", "-MaximumSeconds", "600"
        ], cwd=R.ROOT, capture_output=True, text=True, check=False)
        R.P123.require((R.ROOT / receipt).is_file(), "runner_receipt_missing")
        doc = json.loads((R.ROOT / receipt).read_bytes())
        if run.returncode == 0:
            R.accept_one(doc, name, freeze)
            completed += 1
        else:
            R.P123.require(doc.get("state") in (
                "NOT_ACCEPTED_STOP_OR_FAILURE", "DEFERRED_BASELINE_RESOURCE_PRESSURE_NOT_STARTED"
            ), "runner_exit_receipt_mismatch")
        last_exit = run.returncode
        status = read_progress(names, freeze)
        print(json.dumps({"state": doc["state"], **status, "receipt": receipt,
                          "elapsed_seconds": doc.get("elapsed_seconds"),
                          "stop_reason": doc.get("stop_reason"),
                          **resource_summary(doc)}),
              flush=True)
    AUDIT.audit()  # batch 종료에도 전체 증거를 확인. 실패하면 batch 성공으로 보고하지 않는다.
    status = read_progress(names, freeze)
    print(json.dumps({"state": "BATCH_COMPLETED" if last_exit == 0 else "BATCH_STOPPED_NO_RETRY",
                      **status, "completed_this_batch": completed,
                      "elapsed_seconds": round(time.monotonic() - start, 2),
                      "single_process_full228_accepted": False, "product_complete": False, "P09_gate": "OPEN"}),
          flush=True)
    return 0 if last_exit == 0 else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}), flush=True)
        raise SystemExit(1) from None
