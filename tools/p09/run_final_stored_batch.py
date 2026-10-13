"""P135 exact current 234-case union, resumable bounded execution; not SQL/native/Gate."""
import argparse
import importlib.util
import json
import re
import subprocess
import time
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p134_preserved", Path(__file__).with_name("verify_formula_policy_revocation.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
ROOT, R, require = PRE.ROOT, PRE.R, PRE.require
DRIVER = "tools/p09/run_final_stored_case.ps1"
CURRENT = "implementation/p09/evidence/p09-135-final-stored-regression.source-progress.v1.json"
EXE = R.RUN + "debug/deps/form_stored_provider-p134-final.exe"
PIN = {"path": EXE, "bytes": 10753536, "sha256": "d406f4693798f6f8ae13982e8f5fcb464721176295a68c53514645df7650252a"}


def preparation():
    require(R.pin(PRE.CURRENT) == {"path": PRE.CURRENT, "bytes": 18919,
            "sha256": "f2d54f2a66c23cd3f2c8cc6049935bd33b735bdf608e99a6f0dd375b63ba89dd"}, "P134_checkpoint_drift")
    require(R.pin(EXE) == PIN, "final_executable_drift")
    names = PRE.expected_names("Stored")
    require(len(names) == 234 and sum(n.startswith("actual_import::") for n in names) == 206
            and sum(n.startswith("full_document::") for n in names) == 20 and sum("::" not in n for n in names) == 8, "final_case_scope_drift")
    listed = R.read(R.RUN + "p134-stored-list-b.json")
    PRE.validate_run(listed, "Stored", "List", names)
    extras = [r["path"] for r in R.read(PRE.CURRENT)["migration_inputs"]] + [PRE.CURRENT, DRIVER,
              "tools/p09/run_final_stored_batch.py", "tools/p09/changed_formula_test_support.ps1"]
    freeze = listed["source_freeze"] + [R.pin(p) for p in extras]
    require(len(freeze) == len({r["path"] for r in freeze}) == 806 and all(R.pin(r["path"]) == r for r in freeze), "final_case_input_inventory_drift")
    return sorted(names, key=lambda n: (n.startswith("actual_import::"), n)), freeze


def protected_pins():
    doc = R.read(PRE.CURRENT)
    return PRE.protected_pins() + doc["current_executables"] + doc["earlier_executables"]


def same_freeze(left, right):
    return len(left) == len(right) == 806 and len({r["path"] for r in left}) == 806 and sorted(left, key=lambda r: r["path"]) == sorted(right, key=lambda r: r["path"])


def accept_case(doc, name, freeze):
    require(doc["schema_version"] == "hwpx-agent.p09-final-stored-case/v1" and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE"
            and doc["exit_code"] == 0 and doc["stop_reason"] is None and doc["test_name"] == name and doc["executable_pin"] == PIN
            and doc["arguments"] == [name, "--exact", "--show-output", "--test-threads=1"], "final_exact_case_not_accepted")
    PRE.resource({**doc, "cargo_jobs": 1})
    require(doc["source_freeze_exact_after"] is True and same_freeze(doc["source_freeze"], freeze)
            and doc["protected_executables_exact_after"] is True and doc["protected_executables"] == protected_pins()
            and len(protected_pins()) == 21 and doc["test_threads"] == 1, "final_case_binding_drift")
    require(doc["P09_gate"] == "OPEN" and doc["product_complete"] is False
            and doc["actual_sql_executed"] is False and doc["native_application_executed"] is False, "final_case_scope_promoted")
    PRE.validate_summary(doc["tests"], {name}, 233)


def progress(names, freeze):
    accepted, stopped = {}, []
    for path in sorted((ROOT / R.RUN).glob("p135-case-*-attempt-*.json")):
        match = re.fullmatch(r"p135-case-(\d{3})-attempt-(\d{3})\.json", path.name)
        require(match is not None, "final_receipt_filename_drift")
        index, attempt = map(int, match.groups())
        require(1 <= index <= 234 and 1 <= attempt <= 999, "final_receipt_index_drift")
        doc = json.loads(path.read_bytes())
        if doc.get("state") == "PASS_SOURCE_ONLY_NOT_GATE":
            accept_case(doc, names[index - 1], freeze)
            require(index not in accepted, "duplicate_final_case")
            accepted[index] = path.relative_to(ROOT).as_posix()
        else:
            require(doc.get("state") in ("NOT_ACCEPTED_STOP_OR_FAILURE", "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED")
                    and doc.get("test_name") == names[index - 1] and doc.get("executable_pin") == PIN
                    and same_freeze(doc["source_freeze"], freeze) and doc.get("P09_gate") == "OPEN"
                    and doc.get("product_complete") is False, "unknown_or_unbound_final_stop")
            stopped.append((index, attempt, path.relative_to(ROOT).as_posix()))
    return accepted, stopped


def next_attempt(index, stopped):
    return 1 + max((attempt for i, attempt, _ in stopped if i == index), default=0)


def may_start(completed, limit, elapsed, budget, last_exit):
    require(type(limit) is int and 1 <= limit <= 30 and type(budget) is int and 1 <= budget <= 300, "invalid_final_batch_bound")
    return last_exit == 0 and completed < limit and elapsed < budget


def status(names, accepted, stopped):
    return {"state": "CURRENT_FINAL234_SCOPED_PROGRESS_NOT_GATE", "accepted": len(accepted), "remaining": 234-len(accepted),
            "actual_import": sum(names[i-1].startswith("actual_import::") for i in accepted),
            "full_document": sum(names[i-1].startswith("full_document::") for i in accepted), "roots": sum("::" not in names[i-1] for i in accepted),
            "unaccepted_attempts_preserved": len(stopped), "whole_workspace_runtime_accepted": False, "P09_gate": "OPEN", "product_complete": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--max-cases", type=int, default=25)
    parser.add_argument("--start-budget-seconds", type=int, default=180)
    parser.add_argument("--retry-stopped", type=int)
    args = parser.parse_args()
    may_start(0, args.max_cases, 0, args.start_budget_seconds, 0)
    PRE.current()
    names, freeze = preparation()
    accepted, stopped = progress(names, freeze)
    completed, last_exit, watch = 0, 0, time.monotonic()
    if args.run:
        for index in [i for i in range(1, 235) if i not in accepted]:
            if not may_start(completed, args.max_cases, time.monotonic()-watch, args.start_budget_seconds, last_exit):
                break
            previous_stops = [i for i, _, _ in stopped if i == index]
            require(not previous_stops or args.retry_stopped == index, "stopped_final_case_requires_explicit_retry")
            attempt = next_attempt(index, stopped)
            require(attempt <= 999, "final_attempt_limit")
            path = R.RUN + f"p135-case-{index:03d}-attempt-{attempt:03d}.json"
            require(not (ROOT / path).exists(), "final_receipt_already_exists")
            print(json.dumps({"state": "FINAL_CASE_STARTING", "index": index, "attempt": attempt}), flush=True)
            run = subprocess.run(["pwsh", "-NoProfile", "-File", DRIVER, "-TestName", names[index-1], "-ReceiptPath", path,
                                  "-MaximumSeconds", "600"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
            require((ROOT / path).is_file(), "final_runner_receipt_missing")
            doc = R.read(path)
            if run.returncode != 0:
                print(json.dumps({"state": "FINAL_BATCH_STOPPED_NOT_ACCEPTED", "index": index, "receipt": path,
                                  "stop_state": doc.get("state"), "stop_reason": doc.get("stop_reason"), "accepted": len(accepted)}), flush=True)
                return 2
            accept_case(doc, names[index-1], freeze)
            accepted[index] = path
            completed += 1
            observed = [s["test_working_set_mib"] for s in doc["samples"] if s["test_working_set_mib"] > 0]
            print(json.dumps({"state": "FINAL_EXACT_CASE_PASS", "index": index, "accepted": len(accepted),
                              "remaining":234-len(accepted), "seconds":doc["elapsed_seconds"],
                              "available_ram_min_mib":min(s["available_ram_mib"] for s in doc["samples"]),
                              "test_ram_observed_mib":max(observed) if observed else None}), flush=True)
    preparation()
    print(json.dumps(status(names, accepted, stopped)), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
