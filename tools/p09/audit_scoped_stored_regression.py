"""P126: independently terminated cases cover the frozen inventory; never single-process/Gate PASS."""
import importlib.util
import json
import subprocess
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "p125_batch", Path(__file__).with_name("run_resumable_formula_batch.py")
)
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)
R = B.R
PREVIOUS = "implementation/p09/evidence/p09-125-bounded-formula-batch.source-progress.v1.json"
CURRENT = "implementation/p09/evidence/p09-126-scoped-stored-regression.source-progress.v1.json"
DELTA = ["tools/p09/audit_scoped_stored_regression.py",
         "tools/p09/tests/test_scoped_stored_regression.py",
         "implementation/p09/P09-126_SCOPED_STORED_REGRESSION_REPORT.md"]


def validate_coverage(inventory, imported, documents, roots):
    R.P123.require(len(inventory) == 228 and len(set(inventory)) == 228, "inventory_drift")
    R.P123.require(len(imported) == 200 and len(documents) == 20 and len(roots) == 8,
                   "scoped_count_drift")
    R.P123.require(set(imported) == {n for n in inventory if n.startswith("actual_import::")}
                   and set(documents) == {n for n in inventory if n.startswith("full_document::")}
                   and set(roots) == set(R.P123.ROOT_NAMES), "scoped_identity_drift")
    combined = [*imported, *documents, *roots]
    R.P123.require(len(set(combined)) == 228 and set(combined) == set(inventory),
                   "missing_or_duplicate_inventory_case")
    return 228


def predecessor():
    B.AUDIT.audit()
    R.P123.require(R.BASE.pin(PREVIOUS) == {
        "path": PREVIOUS, "bytes": 10794,
        "sha256": "46321fdc8eedde0a8b19b1461313923d53ccc54cb7cb798449aeee70002da48e"
    }, "P125_checkpoint_drift")
    doc = json.loads((R.ROOT / PREVIOUS).read_bytes())
    sizes = {"source_delta": 3, "predecessor_receipts_added": 1,
             "source_archives": 1, "runtime_runs": 46}
    R.P123.require(all(len(doc[k]) == n and all(R.BASE.exact(row) for row in doc[k])
                       for k, n in sizes.items()), "P125_pins_drift")
    return doc


def audit():
    predecessor()
    doc = json.loads((R.ROOT / CURRENT).read_bytes())
    runtime_paths = [f"{R.RUN_DIR}/p124-case-{i:03d}-attempt-001.json" for i in range(49, 201)]
    for key, paths in {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS],
                       "runtime_runs": runtime_paths}.items():
        rows = doc[key]
        R.P123.require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                       and all(R.BASE.exact(r) for r in rows), "P126_pin_coverage_drift")
    R.P123.require(doc["previous_source_files_count"] == 1128
                   and doc["current_source_files_count"] == 1131
                   and doc["inherited_raw_pin_entries"] == 2436, "source_coverage_drift")
    R.P123.require(R.BASE.pin(R.EXE) == R.PIN, "executable_drift")
    freeze = json.loads((R.ROOT / R.P123.P121.FREEZE).read_bytes())["source_freeze"]
    R.P123.require(len(freeze) == 14 and all(R.BASE.exact(row) for row in freeze), "source_freeze_drift")
    listed = subprocess.run([str(R.ROOT / R.EXE), "--list"], cwd=R.ROOT,
                            capture_output=True, text=True, timeout=10, check=False)
    R.P123.require(listed.returncode == 0, "inventory_failed")
    actual_names = R.inventory(listed.stdout)
    all_names = [line[:-6] for line in listed.stdout.splitlines() if line.endswith(": test")]
    imported, runs = [], []
    for i, name in enumerate(actual_names, 1):
        run = json.loads((R.ROOT / f"{R.RUN_DIR}/p124-case-{i:03d}-attempt-001.json").read_bytes())
        R.accept_one(run, name, freeze)
        imported.extend(run["tests"]["passed_test_names"])
        runs.append(run)
    document = json.loads((R.ROOT / R.P123.DOCUMENT_RUN).read_bytes())
    documents = R.P123.validate_scoped(document, 20, 208, freeze, R.PIN, 1)["passed_test_names"]
    roots = []
    for path, name in zip(R.P123.ROOT_RUNS, R.P123.ROOT_NAMES):
        root = json.loads((R.ROOT / path).read_bytes())
        R.accept_one(root, name, freeze)
        roots.extend(root["tests"]["passed_test_names"])
    validate_coverage(all_names, imported, documents, roots)
    original = json.loads((R.ROOT / "implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json").read_bytes())["result"]
    changed = json.loads((R.ROOT / R.P123.P121.RUNS[6]).read_bytes())["tests"]["changed_corpus_result"]
    R.P123.require(runs[48]["tests"]["corpus_result"] == original
                   and runs[49]["tests"]["outside_leaf_counterexamples_pass"] is True
                   and runs[50]["tests"]["changed_corpus_result"] == changed
                   and runs[51]["tests"]["changed_protection_pass"] is True,
                   "original_changed_protection_markers_drift")
    R.P123.require(doc["accepted_actual_import_cases"] == 200 and doc["accepted_scoped_distinct_cases"] == 228
                   and doc["single_process_full228_accepted"] is False
                   and doc["single_process_actual_import200_accepted"] is False
                   and doc["product_complete"] is False and doc["P09_gate"] == "OPEN"
                   and doc["P10_new_implementation"] is False and doc["goal_status"] == "active",
                   "scope_promoted")
    return {"state": "PASS_DISTINCT_SCOPED228_NOT_SINGLE_PROCESS_OR_GATE", "actual_import": 200,
            "documents": 20, "roots": 8, "source_freeze": 14, "originals": 36,
            "changed_derivatives": 16, "protected_denials": 32, "outside_leaf_counterexamples": 16,
            "single_process_full228_accepted": False, "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    try:
        print(json.dumps(audit(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
