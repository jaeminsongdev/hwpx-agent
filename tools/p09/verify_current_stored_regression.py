"""P129 authoritative current scoped coverage and exact signed-corpus markers; Gate remains OPEN."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p129_current", Path(__file__).with_name("run_current_stored_batch.py"))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)
ROOT = R.ROOT
PREVIOUS = "implementation/p09/evidence/p09-128-current-comment-regression.source-progress.v1.json"
CURRENT = "implementation/p09/evidence/p09-129-current-stored-regression.source-progress.v1.json"
MARKER_DRIVER = "tools/p09/run_current_formula_markers.ps1"
EXTRA = [MARKER_DRIVER, "tools/p09/resource_bounded_test_support.ps1", "tools/p09/changed_formula_test_support.ps1"]
MARKERS = [R.RUN + f"p129-current-marker-{i:02d}-b.json" for i in range(1, 5)]
UNACCEPTED_MARKERS = [R.RUN + f"p129-current-marker-{i:02d}-a.json" for i in range(1, 5)]
DELTA = [R.DRIVER, "tools/p09/run_current_stored_batch.py", "tools/p09/tests/test_current_stored_batch.py",
         MARKER_DRIVER, "tools/p09/verify_current_stored_regression.py", "tools/p09/tests/test_current_stored_regression.py",
         "implementation/p09/P09-129_CURRENT_STORED_REGRESSION_REPORT.md"]


def predecessor():
    R.historical()
    R.require(R.pin(PREVIOUS) == {"path": PREVIOUS, "bytes": 3454,
              "sha256": "64a8ed619d4cbe7c0e2c3f28bff91f9edd872c9f1448e20ab7d167bcff4021ab"}, "P128_checkpoint_drift")
    previous = R.read(PREVIOUS)
    for key, size in {"source_delta": 4, "predecessor_receipts_added": 1, "runtime_runs": 6, "current_executables": 3}.items():
        R.require(len(previous[key]) == size and all(R.pin(row["path"]) == row for row in previous[key]), "P128_pins_drift")
    R.require(previous["current_source_files_count"] == 1140 and previous["inherited_raw_pin_entries"] == 2607
              and previous["product_complete"] is False and previous["P09_gate"] == "OPEN", "P128_scope_drift")


def validate_marker(doc, name, freeze):
    R.require(doc["schema_version"] == "hwpx-agent.p09-current-form-markers/v1", "marker_schema_drift")
    # Delegate the exact unchanged resource policy after checking this closed schema.
    normalized = copy.deepcopy(doc)
    normalized["schema_version"] = "hwpx-agent.p09-current-form-regression/v1"
    R.policy(normalized)
    R.require(doc["mode"] == "Test" and doc["test_name"] == name and doc["executable_pin"] == R.pin(R.NEW_EXE),
              "marker_case_identity_drift")
    expected = freeze + [R.pin(path) for path in EXTRA]
    rows = doc["source_freeze"]
    R.require(len(rows) == 764 and len({r["path"] for r in rows}) == 764
              and sorted(rows, key=lambda r: r["path"]) == sorted(expected, key=lambda r: r["path"])
              and all(R.pin(r["path"]) == r for r in rows), "marker_source_drift")
    tests, summary = doc["tests"], doc["tests"]["terminal_summary"]
    R.require(doc["expected_test_count"] == 1 and summary["outcome"] == "ok" and summary["passed"] == 1
              and summary["failed"] == summary["ignored"] == summary["measured"] == 0 and summary["filtered"] == 227
              and tests["passed_test_names"] == [name] and tests["failed_test_names"] == [], "marker_test_coverage_drift")
    return tests


def validate_signed_markers(tests, original, changed):
    R.require(len(tests) == 4 and tests[0]["corpus_result"] == original
              and tests[1]["outside_leaf_counterexamples_pass"] is True
              and tests[2]["changed_corpus_result"] == changed
              and tests[3]["changed_protection_pass"] is True, "signed_corpus_result_drift")


def source_progress(require_complete=False):
    predecessor()
    names, freeze = R.preparation()
    accepted, stopped = R.progress(names, freeze)
    R.require(not stopped, "stopped_attempt_not_accepted")
    imported = sum(names[i - 1].startswith("actual_import::") for i in accepted)
    documents = sum(names[i - 1].startswith("full_document::") for i in accepted)
    roots = sum("::" not in names[i - 1] for i in accepted)
    if require_complete:
        R.require(set(accepted) == set(range(1, 229)) and (imported, documents, roots) == (200, 20, 8),
                  "current_scoped_inventory_incomplete")
    return names, freeze, accepted, {"actual_import": imported, "documents": documents, "roots": roots}


def audit():
    names, freeze, accepted, counts = source_progress(True)
    tests = [validate_marker(R.read(path), names[76 + i], freeze) for i, path in enumerate(MARKERS)]
    for i, path in enumerate(UNACCEPTED_MARKERS):
        try:
            validate_marker(R.read(path), names[76 + i], freeze)
        except ValueError as error:
            R.require(str(error) == "marker_case_identity_drift", "unaccepted_attempt_reason_drift")
        else:
            raise ValueError("wrong_scope_attempt_promoted")
    original = R.read("implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json")["result"]
    changed = R.read(R.RUN + "p124-case-051-attempt-001.json")["tests"]["changed_corpus_result"]
    validate_signed_markers(tests, original, changed)
    doc = R.read(CURRENT)
    groups = {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS],
              "current_and_archived_executables": [R.NEW_EXE, R.ARCHIVE],
              "runtime_runs": [R.BUILD, R.LIST, *accepted.values(), *MARKERS],
              "unaccepted_marker_scope_attempts": UNACCEPTED_MARKERS}
    for key, paths in groups.items():
        rows = doc[key]
        R.require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                  and all(R.pin(r["path"]) == r for r in rows), "P129_pin_coverage_drift")
    R.require(doc["schema_version"] == "hwpx-agent.p09-current-stored-regression/v1"
              and doc["state"] == "PASS_CURRENT_DISTINCT_SCOPED228_AND_SIGNED_MARKERS_NOT_NATIVE_OR_GATE"
              and doc["runtime_guard_unit_checks_passed"] == 28
              and doc["previous_source_files_count"] == 1140 and doc["current_source_files_count"] == 1147
              and doc["inherited_raw_pin_entries"] == 2621 and doc["accepted_current_scoped_distinct_cases"] == 228
              and doc["current_form_stored228_regression_accepted"] is True
              and doc["single_process_full228_accepted"] is False and doc["whole_workspace_accepted"] is False
              and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False
              and doc["P10_new_implementation"] is False and doc["goal_status"] == "active", "P129_scope_promoted")
    return {"state": "PASS_CURRENT_DISTINCT_SCOPED228_AND_SIGNED_MARKERS_NOT_NATIVE_OR_GATE", **counts,
            "originals": 36, "signed_changed_derivatives": 16, "protected_denials": 32,
            "outside_leaf_counterexamples": 16, "current_source_files": 1147,
            "single_process_full228_accepted": False, "whole_workspace_accepted": False,
            "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()
    try:
        if args.progress:
            _, _, accepted, counts = source_progress()
            result = {"state": "CURRENT_PROGRESS_NOT_GATE", "accepted": len(accepted), "remaining": 228 - len(accepted),
                      **counts, "P09_gate": "OPEN", "product_complete": False}
        else:
            result = audit()
        print(json.dumps(result, separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
