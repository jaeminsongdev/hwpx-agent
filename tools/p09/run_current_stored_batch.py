"""P129 current-code stored regression: exact cases, bounded batches, immutable receipts."""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = "target/p09-121-resource-optimized/"
BUILD = RUN + "p129-current-form-build-a.json"
LIST = RUN + "p129-current-form-list-a.json"
OLD_EXE = RUN + "debug/deps/form_stored_provider-658c5ea10a96d565.exe"
ARCHIVE = RUN + "p129-historical-executable/form_stored_provider-658c5ea10a96d565.exe"
NEW_EXE = RUN + "debug/deps/form_stored_provider-p129-current.exe"
OLD_HASH = "04fefdf71582488f4490a5e572203994d89fbc890c1282b5336b3703a581a5ca"
NEW_HASH = "aadf093a65dfc451feda8ae96d64938d51fb0e90af3cf7810e6072c65d073941"
DRIVER = "tools/p09/run_current_form_regression.ps1"


def require(value, code):
    if not value:
        raise ValueError(code)


def pin(path):
    data = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def same_freeze(left, right):
    # rg traversal order is not an input contract; every unique path/hash/size is.
    return (len(left) == len(right) == 761
            and len({r["path"] for r in left}) == 761
            and len({r["path"] for r in right}) == 761
            and sorted(left, key=lambda r: r["path"]) == sorted(right, key=lambda r: r["path"]))


def policy(doc):
    require(doc["schema_version"] == "hwpx-agent.p09-current-form-regression/v1"
            and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["exit_code"] == 0
            and doc["stop_reason"] is None and doc["source_freeze_exact_after"] is True
            and doc["historical_executable_exact_after"] is True, "run_not_accepted")
    require(doc["logical_cpu_limit"] == 1 and doc["affinity_mask"] == 1
            and doc["priority"] == "BelowNormal" and doc["cargo_jobs"] == 1
            and doc["sample_seconds"] == 2 and doc["cpu_stop_percent"] == 85
            and doc["cpu_stop_consecutive_samples"] == 3
            and doc["minimum_available_ram_mib"] == 4096
            and doc["maximum_root_working_set_mib"] == 2048
            and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "resource_policy_drift")
    hot = 0
    require(doc["samples"], "samples_missing")
    require(doc["samples"][0]["system_cpu_percent"] < 85
            and doc["samples"][0]["test_working_set_mib"] == 0
            and doc["samples"][0]["test_cpu_seconds"] == 0, "baseline_not_startable")
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "observed_resource_violation")
    require(doc["product_complete"] is False and doc["P09_gate"] == "OPEN", "scope_promoted")


def inventory(names):
    require(len(names) == 228 and len(set(names)) == 228
            and all(re.fullmatch(r"[A-Za-z0-9_:]+", n) for n in names), "inventory_drift")
    require(sum(n.startswith("actual_import::") for n in names) == 200
            and sum(n.startswith("full_document::") for n in names) == 20
            and sum("::" not in n for n in names) == 8, "inventory_scope_drift")
    # Exercise inexpensive whole-document/root contracts first, then all import cases.
    return sorted(names, key=lambda n: (n.startswith("actual_import::"), n))


def preparation():
    for path, expected in ((OLD_EXE, OLD_HASH), (ARCHIVE, OLD_HASH), (NEW_EXE, NEW_HASH)):
        require(pin(path) == {"path": path, "bytes": 10688512, "sha256": expected}, "executable_drift")
    build, listed = read(BUILD), read(LIST)
    policy(build)
    policy(listed)
    require(build["mode"] == "Build" and build["build_marker"] is True and build["tests"] is None
            and listed["mode"] == "List" and listed["executable_pin"] == pin(NEW_EXE), "preparation_scope_drift")
    freeze = build["source_freeze"]
    paths = subprocess.run(["rg", "--files", "crates"], cwd=ROOT, capture_output=True,
                           text=True, timeout=10, check=True).stdout.splitlines()
    expected = {p.replace("\\", "/") for p in paths} | {"Cargo.toml", "Cargo.lock", DRIVER,
        "implementation/p04/trust/p04-direct-route-attestation.json",
        "implementation/p04/trust/p04-direct-route-attestation.sig"}
    require(len(freeze) == 761 and len(expected) == 761 and {r["path"] for r in freeze} == expected
            and same_freeze(listed["source_freeze"], freeze) and all(pin(r["path"]) == r for r in freeze), "source_freeze_drift")
    driver = (ROOT / DRIVER).read_text(encoding="utf-8")
    for marker in ("extra-filename=-p129-current", "'--profile','test'", "CARGO_PROFILE_TEST_OPT_LEVEL']='1'",
                   "CARGO_PROFILE_TEST_DEBUG_ASSERTIONS']='true'", "CARGO_PROFILE_TEST_OVERFLOW_CHECKS']='true'",
                   "CARGO_PROFILE_TEST_CODEGEN_UNITS']='1'", "'--exact','--nocapture','--test-threads=1'"):
        require(marker in driver, "compiler_or_test_contract_drift")
    return inventory(listed["inventory"]), freeze


def accept_case(doc, name, freeze):
    policy(doc)
    require(doc["mode"] == "Test" and doc["test_name"] == name and doc["expected_test_count"] == 1
            and doc["executable_pin"] == pin(NEW_EXE) and same_freeze(doc["source_freeze"], freeze), "case_identity_drift")
    tests = doc["tests"]
    summary = tests["terminal_summary"]
    require(summary["outcome"] == "ok" and summary["passed"] == 1 and summary["failed"] == 0
            and summary["ignored"] == 0 and summary["measured"] == 0 and summary["filtered"] == 227
            and tests["passed_test_names"] == [name] and tests["failed_test_names"] == [], "case_coverage_drift")


def progress(names, freeze):
    accepted, stopped = {}, []
    for path in sorted((ROOT / RUN).glob("p129-current-case-*-attempt-*.json")):
        match = re.fullmatch(r"p129-current-case-(\d{3})-attempt-(\d{3})\.json", path.name)
        require(match is not None, "receipt_filename_drift")
        index, attempt = map(int, match.groups())
        require(1 <= index <= 228 and 1 <= attempt <= 999, "receipt_index_outside_inventory")
        doc = json.loads(path.read_bytes())
        if doc.get("state") == "PASS_SOURCE_ONLY_NOT_GATE":
            accept_case(doc, names[index - 1], freeze)
            require(index not in accepted, "duplicate_case")
            accepted[index] = path.relative_to(ROOT).as_posix()
        else:
            require(doc.get("state") in ("NOT_ACCEPTED_STOP_OR_FAILURE", "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED"),
                    "unknown_stop_state")
            stopped.append(index)
    return accepted, stopped


def historical():
    spec = importlib.util.spec_from_file_location("p128_preserved", ROOT / "tools/p09/verify_comment_regression_progress.py")
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    previous.P127.current()
    for suite in previous.SUITES:
        for mode in ("Build", "Test"):
            previous.validate_runtime(read(RUN + f"p128-{suite.lower()}-{'build' if mode == 'Build' else 'tests'}-a.json"), suite, mode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--max-cases", type=int, choices=range(1, 31), default=25)
    args = parser.parse_args()
    historical()
    names, freeze = preparation()
    accepted, stopped = progress(names, freeze)
    require(not stopped or not args.run, "stopped_attempt_requires_explicit_followup")
    if args.run:
        for index in [i for i in range(1, 229) if i not in accepted][:args.max_cases]:
            receipt = RUN + f"p129-current-case-{index:03d}-attempt-001.json"
            require(not (ROOT / receipt).exists(), "receipt_already_exists")
            run = subprocess.run(["pwsh", "-NoProfile", "-File", DRIVER, "-Mode", "Test", "-TestName", names[index - 1],
                                  "-ReceiptPath", receipt, "-MaximumSeconds", "600"], cwd=ROOT,
                                 capture_output=True, text=True, check=False)
            require((ROOT / receipt).is_file(), "runner_receipt_missing")
            doc = read(receipt)
            if run.returncode != 0:
                print(json.dumps({"state": "BATCH_STOPPED_NOT_ACCEPTED", "receipt": receipt,
                                  "accepted": len(accepted), "P09_gate": "OPEN"}), flush=True)
                return 2
            accept_case(doc, names[index - 1], freeze)
            accepted[index] = receipt
            print(json.dumps({"state": "CURRENT_EXACT_CASE_PASS", "index": index, "accepted": len(accepted),
                              "remaining": 228-len(accepted), "elapsed_seconds": doc["elapsed_seconds"],
                              "minimum_available_ram_mib": min(s["available_ram_mib"] for s in doc["samples"])}), flush=True)
    historical()
    preparation()
    print(json.dumps({"state": "CURRENT_SCOPED_REGRESSION_PROGRESS_NOT_GATE", "accepted": len(accepted),
                      "remaining": 228-len(accepted), "stopped_attempt_count": len(stopped),
                      "single_process_full228_accepted": False, "whole_workspace_accepted": False,
                      "P09_gate": "OPEN", "product_complete": False}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
