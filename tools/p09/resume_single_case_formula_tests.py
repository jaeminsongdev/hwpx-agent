"""P124: 검증된 단일-case 영수증만 이어서 실행한다. 전체 suite/Gate 승인과 별개다."""
import argparse
import importlib.util
import json
import re
import subprocess
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "preserved_p123", Path(__file__).with_name("verify_single_cpu_formula_regression.py")
)
P123 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P123)
ROOT, BASE = P123.ROOT, P123.BASE
EXE = P123.P121.EXE
PIN = {"path": EXE, "bytes": 10688512,
       "sha256": "04fefdf71582488f4490a5e572203994d89fbc890c1282b5336b3703a581a5ca"}
RUN_DIR = "target/p09-121-resource-optimized"
PATTERN = re.compile(r"p124-case-(\d{3})-attempt-(\d{3})\.json")


def inventory(output):
    names = []
    for line in output.splitlines():
        if line.endswith(": test"):
            name = line[:-6]
            P123.require(re.fullmatch(r"[A-Za-z0-9_:]+", name) is not None, "unsafe_test_name")
            names.append(name)
    P123.require(len(names) == 228 and len(set(names)) == 228, "inventory_count_drift")
    actual = sorted(n for n in names if n.startswith("actual_import::"))
    documents = [n for n in names if n.startswith("full_document::")]
    roots = [n for n in names if "::" not in n]
    P123.require(len(actual) == 200 and len(documents) == 20
                 and set(roots) == set(P123.ROOT_NAMES), "inventory_scope_drift")
    # 기존 runner는 substring filter다. 정확히 한 case에만 매칭되는 이름만 실행한다.
    P123.require(all(sum(name in other for other in names) == 1 for name in actual),
                 "substring_filter_collision")
    return actual


def accept_one(doc, name, freeze):
    P123.require(isinstance(doc.get("tests", {}).get("terminal_summary"), dict),
                 "single_case_terminal_missing")
    tests = P123.validate_scoped(doc, 1, 227, freeze, PIN, 1)
    P123.require(doc["plan"]["test_arguments"] == [name, "--nocapture", "--test-threads=1"]
                 and tests["passed_test_names"] == [name], "single_case_identity_drift")
    return True


def progress(names, rows, freeze):
    accepted, attempts = set(), {}
    for filename, doc in rows:
        match = PATTERN.fullmatch(filename)
        P123.require(match is not None, "unexpected_receipt_name")
        index, attempt = map(int, match.groups())
        P123.require(1 <= index <= len(names) and 1 <= attempt <= 999, "receipt_index_outside_inventory")
        attempts[index] = max(attempts.get(index, 0), attempt)
        if doc.get("state") == "PASS_RESOURCE_BOUNDED_SCOPED_TESTS_NOT_Gate":
            accept_one(doc, names[index - 1], freeze)
            P123.require(index not in accepted, "duplicate_accepted_case")
            accepted.add(index)
        else:
            # 중단 marker도 최종 성공으로 세지 않는다. 알려진 중단 형태만 보존한다.
            P123.require(doc.get("state") in (
                "NOT_ACCEPTED_STOP_OR_FAILURE", "DEFERRED_BASELINE_RESOURCE_PRESSURE_NOT_STARTED"
            ), "unknown_receipt_state")
    pending = next((i for i in range(1, len(names) + 1) if i not in accepted), None)
    return {"accepted": len(accepted), "remaining": len(names) - len(accepted),
            "next_index": pending, "next_attempt": attempts.get(pending, 0) + 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-next", action="store_true", help="다음 한 case만 실행; 자동 반복 없음")
    args = parser.parse_args()
    P123.partial()  # 수정하지 않은 이전 전수 검증기를 그대로 실행한다.
    P123.require(BASE.pin(EXE) == PIN, "frozen_executable_drift")
    freeze = json.loads((ROOT / P123.P121.FREEZE).read_bytes())["source_freeze"]
    P123.require(len(freeze) == 14 and all(BASE.exact(r) for r in freeze), "frozen_source_drift")
    listed = subprocess.run([str(ROOT / EXE), "--list"], cwd=ROOT, capture_output=True,
                            text=True, timeout=10, check=False)
    P123.require(listed.returncode == 0, "test_inventory_failed")
    names = inventory(listed.stdout)
    rows = [(p.name, json.loads(p.read_bytes()))
            for p in sorted((ROOT / RUN_DIR).glob("p124-case-*-attempt-*.json"))]
    status = progress(names, rows, freeze)
    result = {"state": "PLAN_ONLY", **status, "single_process_full228_accepted": False,
              "product_complete": False, "P09_gate": "OPEN"}
    if args.run_next and status["next_index"] is not None:
        index, attempt = status["next_index"], status["next_attempt"]
        P123.require(attempt <= 999, "attempt_limit_reached")
        name = names[index - 1]
        receipt = f"{RUN_DIR}/p124-case-{index:03d}-attempt-{attempt:03d}.json"
        P123.require(not (ROOT / receipt).exists(), "receipt_already_exists")
        # 원래 resource runner/threshold를 바꾸지 않는다. 한 번 실행한 뒤 즉시 반환한다.
        run = subprocess.run([
            "pwsh", "-NoProfile", "-File", "tools/p09/run_changed_formula_tests.ps1",
            "-TestExecutable", EXE, "-ReceiptPath", receipt, "-TestFilter", name,
            "-LogicalCpuLimit", "1", "-SampleSeconds", "2", "-MaximumSeconds", "600"
        ], cwd=ROOT, capture_output=True, text=True, check=False)
        # stdout/stderr 원문은 출력하거나 저장하지 않는다. 정상 runner의 안전한 JSON만 사용한다.
        P123.require((ROOT / receipt).is_file(), "runner_receipt_missing")
        doc = json.loads((ROOT / receipt).read_bytes())
        if run.returncode == 0:
            accept_one(doc, name, freeze)
        else:
            P123.require(doc.get("state") in (
                "NOT_ACCEPTED_STOP_OR_FAILURE", "DEFERRED_BASELINE_RESOURCE_PRESSURE_NOT_STARTED"
            ), "runner_exit_receipt_mismatch")
        updated = progress(names, [*rows, (Path(receipt).name, doc)], freeze)
        result.update(updated)
        result.update(state=doc["state"], receipt=receipt, stop_reason=doc.get("stop_reason"),
                      elapsed_seconds=doc.get("elapsed_seconds"),
                      test_ram_sampled=len(doc["samples"]) > 1,
                      max_observed_test_ram_mib=(max(s["test_working_set_mib"] for s in doc["samples"][1:])
                                                 if len(doc["samples"]) > 1 else None),
                      minimum_available_ram_mib=min(s["available_ram_mib"] for s in doc["samples"]))
        print(json.dumps(result, separators=(",", ":")))
        return 0 if run.returncode == 0 else 2
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__,
                          "product_complete": False, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
