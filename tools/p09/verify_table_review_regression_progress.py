"""P131 table/review package runtime; no native application/SQL/product qualification."""
import importlib.util
import json
import re
import subprocess
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p130_preserved", Path(__file__).with_name("verify_workspace_lint_progress.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
ROOT, R = PRE.ROOT, PRE.OLD.R
SUITES = {"Create": ("table_create_hwpx", 8), "Context": ("review_table_create_context", 15),
          "Output": ("review_table_output", 21), "Filled": ("review_filled_table_output", 23)}
RUN = R.RUN
DRIVER = "tools/p09/run_current_table_review_regression.ps1"
PREVIOUS = PRE.CURRENT
CURRENT = "implementation/p09/evidence/p09-131-current-table-review-regression.source-progress.v1.json"
DELTA = [DRIVER, "tools/p09/verify_table_review_regression_progress.py", "tools/p09/tests/test_table_review_regression_progress.py",
         "implementation/p09/P09-131_CURRENT_TABLE_REVIEW_REGRESSION_REPORT.md"]
DRIVER_ARCHIVE = RUN + "p131-initial-source-index-runner.ps1.txt"
LEGACY_OMITTED = "crates/artifact-service/src/bin/p14_cleanup_worker.rs"
ARCHIVES = [DRIVER_ARCHIVE, RUN + "p131-initial-direct-index-runner.ps1.txt",
            RUN + "p131-initial-enumeration-audit.py.txt"]
OBSERVATIONS = [RUN + "p131-context-startup-a.observation.json", RUN + "p131-output-test-startup-a.observation.json",
                RUN + "p131-output-source-index-startup-b.observation.json", RUN + "p131-output-source-index-startup-c.observation.json"]


def require(value, code):
    if not value:
        raise ValueError(code)


def runtime_paths():
    return [run_path(suite, mode.title()) for suite in SUITES for mode in ("build", "list", "test")]


def run_path(suite, mode):
    attempt = "d" if (suite, mode) == ("Output", "Test") else "b" if (suite, mode) == ("Context", "Build") else "a"
    return RUN + f"p131-{suite.lower()}-{mode.lower()}-{attempt}.json"


def expected_names():
    own = {}
    for suite, (stem, _) in SUITES.items():
        body = (ROOT / f"crates/hwpx-package/tests/{stem}.rs").read_text(encoding="utf-8")
        own[suite] = set(re.findall(r"#\[test\]\s*fn\s+([A-Za-z0-9_]+)", body))
    require({k: len(v) for k, v in own.items()} == {"Create": 8, "Context": 7, "Output": 6, "Filled": 8}, "direct_test_inventory_drift")
    expected = {"Create": own["Create"], "Context": own["Context"] | {"native::" + n for n in own["Create"]}}
    expected.update({k: own[k] | {"previous::" + n for n in expected["Context"]} for k in ("Output", "Filled")})
    return expected


def source_paths():
    result = subprocess.run(["rg", "--threads", "1", "--files", "crates", "protocol/generated/rust", "tools/xtask"], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=10)
    return {p.replace("\\", "/") for p in result.stdout.splitlines()} | {
        "Cargo.toml", "Cargo.lock", "implementation/p04/trust/p04-direct-route-attestation.json",
        "implementation/p04/trust/p04-direct-route-attestation.sig", DRIVER, "tools/p09/resource_bounded_test_support.ps1"}


def validate_run(doc, suite, mode, names):
    stem, count = SUITES[suite]
    require(doc["schema_version"] == "hwpx-agent.p09-current-table-review-regression/v1"
            and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["mode"] == mode and doc["suite"] == suite
            and doc["expected_test_count"] == count and doc["exit_code"] == 0 and doc["stop_reason"] is None
            and doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True, "runtime_not_accepted")
    require(doc["logical_cpu_limit"] == doc["affinity_mask"] == doc["cargo_jobs"] == 1
            and doc["priority"] == "BelowNormal" and doc["sample_seconds"] == 2 and doc["cpu_stop_percent"] == 85
            and doc["cpu_stop_consecutive_samples"] == 3 and doc["minimum_available_ram_mib"] == 4096
            and doc["maximum_root_working_set_mib"] == 2048 and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "resource_policy_drift")
    require(doc["samples"] and doc["samples"][0]["system_cpu_percent"] < 85, "baseline_not_startable")
    hot = 0
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "resource_observation_violated")
    require(doc["product_complete"] is False and doc["P09_gate"] == "OPEN", "scope_promoted")
    freeze, paths = doc["source_freeze"], source_paths()
    legacy = suite in ("Create", "Context") or (suite == "Output" and mode in ("Build", "List"))
    require(len(paths) == 771 and R.pin(LEGACY_OMITTED)["sha256"] == "78dedad5c76a750962a17394af0e74a94165da773c3ff29d0b6c7c3c94ec5d44",
            "historical_worker_source_changed")
    require(R.pin(DRIVER_ARCHIVE)["sha256"] == "ed2d0901756b3539f2bf82145a6e703aaddbc3bfc0e363726322adb21bd958d4", "legacy_runner_archive_drift")
    if legacy:
        paths = paths - {LEGACY_OMITTED}
    exact = []
    for row in freeze:
        actual = R.pin(DRIVER_ARCHIVE if legacy and row["path"] == DRIVER else row["path"])
        actual["path"] = row["path"]
        exact.append(actual == row)
    require(len(freeze) == len(paths) == (770 if legacy else 771)
            and {r["path"] for r in freeze} == paths and all(exact), "source_inventory_drift")
    protected = R.read(PRE.RUNS[1])["protected_executables"]
    require(doc["protected_executables"] == protected and len(protected) == 6
            and all(R.pin(r["path"]) == r for r in protected), "old_executable_changed")
    if mode == "Build":
        require(doc["build_marker"] is True and doc["tests"] is None, "build_receipt_drift")
    else:
        pin = doc["executable_pin"]
        require(pin["path"] == RUN + f"debug/deps/{stem}-p131-current.exe" and pin == R.pin(pin["path"]), "current_executable_drift")
        if mode == "List":
            require(len(doc["inventory"]) == count and set(doc["inventory"]) == names, "compiled_test_inventory_drift")
        else:
            tests, summary = doc["tests"], doc["tests"]["terminal_summary"]
            require(summary["outcome"] == "ok" and summary["passed"] == count
                    and summary["failed"] == summary["ignored"] == summary["measured"] == summary["filtered"] == 0
                    and len(tests["passed_test_names"]) == count and set(tests["passed_test_names"]) == names
                    and not tests["failed_test_names"], "actual_test_coverage_drift")
    return count if mode == "Test" else 0


def historical_previous():
    require(R.pin(PREVIOUS) == {"path": PREVIOUS, "bytes": 3109,
            "sha256": "083399ed335ba1b187f2fafb4a04d7c1ab97d31882628d0f044beb34da4338f5"}, "P130_checkpoint_drift")
    require(R.pin(LEGACY_OMITTED)["sha256"] == "78dedad5c76a750962a17394af0e74a94165da773c3ff29d0b6c7c3c94ec5d44",
            "historical_worker_source_changed")
    original_run = subprocess.run
    scopes = {("rg", "--files", "crates", "protocol/generated/rust", "tools/xtask")}

    def historical_enumeration(args, *positional, **kwargs):
        if isinstance(args, (list, tuple)) and tuple(args) in scopes:
            result = original_run([args[0], "--threads", "1", *args[1:]], *positional, **kwargs)
            require(result.returncode == 0 and isinstance(result.stdout, str), "historical_enumeration_failed")
            lines = result.stdout.splitlines()
            require(sum(p.replace("\\", "/") == LEGACY_OMITTED for p in lines) == 1, "historical_worker_enumeration_drift")
            # The old receipts excluded exactly this unchanged, separately hash-bound
            # worker. Reproduce that declared historical input scope, not current scope.
            result.stdout = "\n".join(p for p in lines if p.replace("\\", "/") != LEGACY_OMITTED) + "\n"
            return result
        return original_run(args, *positional, **kwargs)

    try:
        subprocess.run = historical_enumeration
        result = PRE.current()
    finally:
        subprocess.run = original_run
    return result


def runtime():
    historical_previous()
    before = (ROOT / DRIVER_ARCHIVE).read_text(encoding="utf-8")
    after = (ROOT / DRIVER).read_text(encoding="utf-8")
    old_start, old_end = before.index("$sources=@("), before.index("$freeze=")
    new_start, new_end = after.index("$indexProc="), after.index("$freeze=")
    require(after[:new_start] + before[old_start:old_end] + after[new_end:] == before,
            "undeclared_runner_transition")
    names, total = expected_names(), 0
    for suite in SUITES:
        for mode in ("Build", "List", "Test"):
            total += validate_run(R.read(run_path(suite, mode)), suite, mode, names[suite])
    require(total == 67, "execution_total_drift")
    return {"state": "PASS_CURRENT_TABLE_REVIEW67_EXECUTIONS_29_DEFINITIONS_NOT_NATIVE_OR_GATE",
            "test_executions": 67, "unique_source_test_definitions": 29, "repeated_helper_executions": 38,
            "P09_gate": "OPEN", "product_complete": False}


def checkpoint_groups():
    return {"source_delta": DELTA, "predecessor_receipts_added": [PREVIOUS],
            "runtime_runs": runtime_paths(),
            "current_executables": [RUN + f"debug/deps/{stem}-p131-current.exe" for stem, _ in SUITES.values()],
            "source_archives": ARCHIVES, "startup_observations": OBSERVATIONS}


def current():
    result = runtime()
    doc = R.read(CURRENT)
    for key, paths in checkpoint_groups().items():
        rows = doc[key]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(R.pin(r["path"]) == r for r in rows), "P131_pin_coverage_drift")
    require(doc["schema_version"] == "hwpx-agent.p09-current-table-review-regression/v1"
            and doc["state"] == result["state"] and doc["goal_status"] == "active"
            and doc["previous_source_files_count"] == 1151 and doc["current_source_files_count"] == 1155
            and doc["inherited_raw_pin_entries"] == 2881 and doc["runtime_guard_units_passed"] == 18
            and doc["test_executions"] == 67 and doc["unique_source_test_definitions"] == 29
            and doc["repeated_helper_executions"] == 38 and doc["legacy_source_inputs"] == 770
            and doc["current_source_inputs"] == 771 and doc["startup_failures_preserved"] == 4
            and doc["current_table_review_runtime_accepted"] is True
            and doc["current_whole_workspace_runtime_accepted"] is False
            and doc["actual_sql_accepted"] is False and doc["native_application_accepted"] is False
            and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False
            and doc["P10_new_implementation"] is False, "P131_scope_promoted")
    result.update({"current_source_files": 1155, "guard_units": 18, "startup_failures_preserved": 4})
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(current(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
