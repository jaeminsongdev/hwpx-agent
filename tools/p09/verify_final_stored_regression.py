"""P135 current exact234-case union with signed original markers; never a native/product Gate."""
import argparse
import importlib.util
import json
import math
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p135_runtime", Path(__file__).with_name("run_final_stored_batch.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
ROOT, R, require = M.ROOT, M.R, M.require
CURRENT = M.CURRENT
MEASUREMENT = "target/p09-122-resource-crosscheck/p135-case27-notstarted-a.json"
MEASUREMENTS = [MEASUREMENT, "target/p09-122-resource-crosscheck/p135-case77-ownedstop-a.json",
                "target/p09-122-resource-crosscheck/p135-case96-ownedstop-a.json",
                "target/p09-122-resource-crosscheck/p135-case96-recheck-b.json"]
DELTA = [M.DRIVER, "tools/p09/run_final_stored_batch.py", "tools/p09/tests/test_final_stored_batch.py",
         "tools/p09/verify_final_stored_regression.py", "implementation/p09/P09-135_FINAL_STORED_REGRESSION_REPORT.md"]
PREFIX = "actual_import::formula_policy_issuer::corpus::"
MARKERS = {
    PREFIX + "all16_actual_formula_sources_and_current_derivatives_keep_native_cell_protection_denial": "protection_derivatives_pass",
    PREFIX + "all16_current_derivatives_are_signed_exact_noops_then_denied_new_policy_and_expired_approval": "current_derivatives_pass",
    PREFIX + "all36_frozen_originals_signed_full_candidates_or_no_formula_denial_and_live_revocation": "corpus_result",
    PREFIX + "changed::all16_changed_original_comparators_reject_an_extra_numeric_input_leaf_change": "outside_leaf_counterexamples_pass",
    PREFIX + "changed::all16_original_numeric_derivatives_have_signed_changed_candidates_exact_current_and_live_revocation": "changed_corpus_result",
    PREFIX + "changed::all32_changed_and_current_numeric_derivatives_keep_valid_signature_cell_protection_denial": "changed_protection_pass",
}


def validate_marker_result(name, tests, original, changed):
    field = MARKERS[name]
    expected = original if field == "corpus_result" else changed if field == "changed_corpus_result" else True
    actual = tests[field]
    require(actual is True if expected is True else
            json.dumps(actual, sort_keys=True, separators=(",", ":")) == json.dumps(expected, sort_keys=True, separators=(",", ":")),
            "current_signed_marker_drift")


def validate_markers(names, accepted):
    require(set(MARKERS) <= set(names), "signed_marker_cases_missing")
    original = R.read("implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json")["result"]
    changed = R.read(R.RUN + "p124-case-051-attempt-001.json")["tests"]["changed_corpus_result"]
    completed = 0
    for name, field in MARKERS.items():
        index = names.index(name) + 1
        if index not in accepted:
            continue
        tests = R.read(accepted[index])["tests"]
        validate_marker_result(name, tests, original, changed)
        completed += 1
    return completed


def validate_measurement(doc):
    require(doc["schema_version"] == "hwpx-agent.p09-122-resource-crosscheck/v1"
            and doc["state"] == "MEASURED_READ_ONLY_NOT_TEST_RUN_OR_MONITOR_REPLACEMENT"
            and doc["logical_processors"] == 16 and doc["measurement_process_cpu_limit"] == 1
            and doc["priority"] == "BelowNormal" and doc["stored_test_started"] is False
            and doc["measurements_have_adjacent_not_identical_windows"] is True
            and doc["pressure_cause"] == "NOT_DETERMINED" and doc["existing_runner_or_thresholds_modified"] is False
            and doc["native_API_is_metrics_only_not_Hangul_or_UI"] is True and doc["system_settings_changed"] is False
            and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False and len(doc["samples"]) == 3,
            "P135_measurement_scope_drift")
    hot = 0
    for index, sample in enumerate(doc["samples"]):
        require(type(sample["index"]) is int and sample["index"] == index
                and type(sample["native_interval_seconds"]) in (int, float)
                and math.isfinite(sample["native_interval_seconds"]) and 1 <= sample["native_interval_seconds"] <= 60,
                "P135_measurement_order_drift")
        for key in ("native_cpu_percent", "cim_cpu_percent", "native_available_ram_mib", "cim_available_ram_mib", "native_total_ram_mib"):
            maximum = 100 if "cpu" in key else 1024 * 1024
            require(type(sample[key]) in (int, float) and math.isfinite(sample[key]) and 0 <= sample[key] <= maximum,
                    "P135_measurement_invalid")
        require(sample["native_total_ram_mib"] > 0 and sample["native_available_ram_mib"] <= sample["native_total_ram_mib"]
                and sample["cim_available_ram_mib"] <= sample["native_total_ram_mib"], "P135_measurement_invalid")
        cpu = max(sample["native_cpu_percent"], sample["cim_cpu_percent"])
        free = min(sample["native_available_ram_mib"], sample["cim_available_ram_mib"])
        hot = hot + 1 if cpu >= 85 else 0
        decision = "STOP_LOW_AVAILABLE_RAM" if free < 4096 else "STOP_SUSTAINED_SYSTEM_CPU" if hot >= 3 else "CONTINUE"
        require(sample["conservative_inputs"] == {"system_cpu_percent": cpu, "available_ram_mib": free}
                and type(sample["consecutive_hot_samples"]) is int and sample["consecutive_hot_samples"] == hot
                and sample["resource_decision"] == decision, "P135_measurement_decision_relaxed")
    return len(doc["samples"])


def validate_stops(names, freeze, accepted, stopped):
    for index, attempt, path in stopped:
        doc = R.read(path)
        require(doc["test_name"] == names[index-1] and doc["executable_pin"] == M.PIN
                and M.same_freeze(doc["source_freeze"], freeze) and doc["P09_gate"] == "OPEN"
                and doc["product_complete"] is False, "stopped_case_binding_drift")
        if doc["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED":
            require(len(doc["samples"]) == 1 and "exit_code" not in doc
                    and (doc["samples"][0]["system_cpu_percent"] >= 85 or doc["samples"][0]["available_ram_mib"] < 4096), "deferred_case_started_or_promoted")
        else:
            require(doc["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and (doc["exit_code"] != 0 or doc["stop_reason"] is not None), "unaccepted_case_promoted")
            if doc["stop_reason"] == "STOP_SUSTAINED_SYSTEM_CPU":
                require(len(doc["samples"]) >= 3 and all(s["system_cpu_percent"] >= 85 for s in doc["samples"][-3:]), "CPU_stop_observation_lost")
        require(attempt <= 999, "stopped_attempt_bounds_drift")


def audit(complete=False):
    M.PRE.current()
    names, freeze = M.preparation()
    accepted, stopped = M.progress(names, freeze)
    validate_stops(names, freeze, accepted, stopped)
    marker_count = validate_markers(names, accepted)
    measured_samples = sum(validate_measurement(R.read(path)) for path in MEASUREMENTS)
    result = M.status(names, accepted, stopped)
    result["current_signed_marker_cases_accepted"] = marker_count
    result["read_only_resource_pair_samples"] = measured_samples
    if complete:
        require(set(accepted) == set(range(1, 235)) and (result["actual_import"], result["full_document"], result["roots"]) == (206, 20, 8)
                and marker_count == 6, "current_final234_union_incomplete")
        result["state"] = "PASS_CURRENT_FINAL234_DISTINCT_UNION_NOT_NATIVE_SQL_OR_GATE"
    return result, names, accepted, stopped


def groups(accepted, stopped):
    return {"source_delta": DELTA, "predecessor_receipts_added": [M.PRE.CURRENT],
            "accepted_current_case_runs": list(accepted.values()), "unaccepted_case_attempts": [p for _, _, p in stopped],
            "current_executables": [M.EXE], "resource_measurements": MEASUREMENTS}


def current():
    result, _, accepted, stopped = audit(False)
    doc = R.read(CURRENT)
    complete = doc["current_final234_union_accepted"]
    require(type(complete) is bool and complete == (len(accepted) == 234), "P135_union_scope_promoted")
    if complete:
        require(result["current_signed_marker_cases_accepted"] == 6 and (result["actual_import"], result["full_document"], result["roots"]) == (206, 20, 8), "P135_complete_coverage_missing")
        result["state"] = "PASS_CURRENT_FINAL234_DISTINCT_UNION_NOT_NATIVE_SQL_OR_GATE"
    pinned_groups = groups(accepted, stopped)
    for key, paths in pinned_groups.items():
        rows = doc[key]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(R.pin(r["path"]) == r for r in rows), "P135_pin_coverage_drift")
    require(doc["state"] == result["state"] and doc["accepted_current_case_count"] == result["accepted"]
            and doc["remaining_current_case_count"] == result["remaining"] and doc["current_signed_marker_cases_accepted"] == result["current_signed_marker_cases_accepted"]
            and doc["goal_status"] == "active" and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False
            and doc["actual_sql_accepted"] is False and doc["native_application_accepted"] is False
            and doc["current_whole_workspace_runtime_accepted"] is False and doc["single_process_full234_accepted"] is False
            and doc["previous_source_files_count"] == 1174 and doc["current_source_files_count"] == 1179
            and doc["inherited_raw_pin_entries"] == 3043 and doc["guard_units_passed"] == 16 and doc["P10_new_implementation"] is False
            and doc["read_only_resource_pair_samples"] == result["read_only_resource_pair_samples"]
            and doc["declared_input_pin_count"] == 806 and doc["protected_executable_count"] == 21
            and doc["unaccepted_attempts_preserved"] == len(stopped)
            and doc["new_raw_pin_entries"] == sum(len(paths) for paths in pinned_groups.values())
            and doc["remaining_coarse_groups_minimum"] == 6 and doc["remaining_groups_closed_by_slice"] == 0
            and doc["minimum_30_conditions_not_exhaustive"] is True and doc["A12_gate"] == "OPEN" and doc["A13_gate"] == "OPEN",
            "P135_scope_or_inventory_drift")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(args.complete)[0] if args.progress or args.complete else current()
        print(json.dumps(result, separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
