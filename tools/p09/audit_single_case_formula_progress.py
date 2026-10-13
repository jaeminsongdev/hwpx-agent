"""P124 frozen predecessor + resumable runtime checkpoint; no full/Gate promotion."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "resume_p124", Path(__file__).with_name("resume_single_case_formula_tests.py")
)
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)
CHECKPOINT = "implementation/p09/evidence/p09-124-resumable-formula-tests.source-progress.v1.json"
DELTA = ["tools/p09/resume_single_case_formula_tests.py",
         "tools/p09/tests/test_resume_single_case_formula_tests.py",
         "tools/p09/audit_single_case_formula_progress.py",
         "implementation/p09/P09-124_RESUMABLE_FORMULA_TESTS_REPORT.md"]
STOPPED = R.RUN_DIR + "/p124-actual-import200-resources-20261005-a.json"
RUNTIME = [R.RUN_DIR + f"/p124-case-{i:03d}-attempt-001.json" for i in (1, 2)]
PREVIOUS = R.P123.CURRENT
PREVIOUS_FINAL = "implementation/p09/evidence/p09-123-single-cpu-formula-regression.final-audit.v1.json"


def audit():
    old = R.P123.partial()
    R.P123.require(R.BASE.pin(PREVIOUS) == {
        "path": PREVIOUS, "bytes": 4753,
        "sha256": "18c07751083271d570777f38af3dd04d2da8795308651e8f4fe2128a911a816f"
    } and R.BASE.pin(PREVIOUS_FINAL) == {
        "path": PREVIOUS_FINAL, "bytes": 2683,
        "sha256": "a021ce045718369d8b07b881644f5f0ba49f51be790140c00a3140aaf8ac0bc3"
    }, "P123_checkpoint_drift")
    doc = json.loads((R.ROOT / CHECKPOINT).read_bytes())
    groups = {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS, PREVIOUS_FINAL],
              "runtime_runs": [STOPPED, *RUNTIME]}
    for group, paths in groups.items():
        rows = doc[group]
        R.P123.require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                       and all(R.BASE.exact(r) for r in rows), "checkpoint_pin_drift")
    R.P123.require(old["current_source_files"] == 1121 and doc["current_source_files_count"] == 1125
                   and doc["inherited_raw_pin_entries"] == 2376, "source_coverage_drift")
    freeze = json.loads((R.ROOT / R.P123.P121.FREEZE).read_bytes())["source_freeze"]
    R.P123.require(R.BASE.pin(R.EXE) == R.PIN and len(freeze) == 14
                   and all(R.BASE.exact(row) for row in freeze), "frozen_test_identity_drift")
    stopped = json.loads((R.ROOT / STOPPED).read_bytes())
    R.P123.require(stopped["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE"
                   and stopped["stop_reason"] == "STOP_LOW_AVAILABLE_RAM"
                   and stopped["exit_code"] == -1 and stopped["source_freeze_exact_after"] is True
                   and stopped["source_freeze"] == freeze and stopped["executable_pin"] == R.PIN
                   and stopped["tests"]["terminal_summary"] is None
                   and stopped["samples"][-1]["available_ram_mib"] < 4096,
                   "stopped_run_promoted_or_drifted")
    R.P123.require(len(doc["accepted_case_names"]) == 2
                   and len(set(doc["accepted_case_names"])) == 2
                   and all(n.startswith("actual_import::") for n in doc["accepted_case_names"]),
                   "case_names_drift")
    for path, name in zip(RUNTIME, doc["accepted_case_names"]):
        R.accept_one(json.loads((R.ROOT / path).read_bytes()), name, freeze)
    R.P123.require(doc["accepted_single_cases"] == 2 and doc["remaining_single_cases"] == 198
                   and doc["single_process_full228_accepted"] is False
                   and doc["actual_import200_suite_accepted"] is False and doc["product_complete"] is False
                   and doc["P09_gate"] == "OPEN" and doc["P10_new_implementation"] is False
                   and doc["goal_status"] == "active", "scope_promoted")
    return {"state": "PASS_CHECKPOINT_NOT_PRODUCT_OR_GATE", "accepted_single_cases": 2,
            "remaining_single_cases": 198, "old_source_files": 1121, "current_source_files": 1125,
            "frozen_rust_files": 14, "guard_thresholds_unchanged": True, "P09_gate": "OPEN"}


if __name__ == "__main__":
    try:
        print(json.dumps(audit(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
