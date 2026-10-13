"""Current-r4 SQL receipt contracts; all six replay slots remain mandatory.

DB/native를 실행하지 않는다. 과거 성공과 현재 성공을 구분하고 구성요소 증거를
full authority audit/strict lint/native/product/Gate로 승격하지 않는다.
"""
import math

import conservative_maintenance as c
import issuer_sql_build_contract as build_contract

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-current-authority-receipt-contract/source-preimages.v1.json"
MANIFEST = "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json"
REQUIRED = tuple((case, mode, outcome) for case in ("approval", "trust", "policy")
    for mode, outcome in (("original", "unchanged"), ("numeric_derivative", "changed")))
CURRENT_RUNS = {
    ("approval", "original"): "implementation/p09/evidence/p09-146-corpus-consumer-run09.v1.json",
    ("trust", "original"): "implementation/p09/evidence/p09-148-authority-consumer-run11.v1.json",
    ("policy", "original"): "implementation/p09/evidence/p09-148-authority-consumer-run12.v1.json",
}
EXPECTED_POLICY = {"logical_cpu_limit": 1, "priority": "BelowNormal", "container_memory_bytes": 536870912,
    "container_swap_total_bytes": 536870912, "pids_limit": 64, "sample_seconds": 0.5,
    "start_available_ram_min_percent": 10, "start_consecutive_samples": 2, "maximum_admission_seconds": 3,
    "already_saturated_cpu_percent": 98, "cpu_stop_percent": 98, "cpu_stop_consecutive_samples": 4,
    "minimum_available_ram_percent": 8, "maximum_commit_used_percent": 95,
    "host_child_aggregate_job_enforced": False, "host_job_launch_path_integrated": True,
    "host_primary_job_ram_max_percent": 7, "host_observation_job_ram_max_percent": 1,
    "host_job_SQL_actual_qualification": False, "container_kernel_limits_qualified_by_this_helper": False}


def typed_equal(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(typed_equal(actual[key], value)
            for key, value in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(typed_equal(a, b) for a, b in zip(actual, expected))
    return actual == expected


def finite(value, lower=0, upper=math.inf):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper


def inventories(run, build):
    sources, protected, helpers, executable = build_contract.build_contract(build, "current_r4")
    run_sources = build_contract.inputs.inventory(run["source_freeze"])
    run_protected = build_contract.inputs.inventory(run["protected_executables"])
    c.require(all(run_sources.get(name) == pin for name, pin in {**sources, **helpers}.items())
        and all(run_protected.get(name) == pin for name, pin in protected.items())
        and run_protected.get(executable["path"]) == executable, "CURRENT_AUTHORITY_INPUT_COVERAGE")
    return run_sources, run_protected


def validate_current_resources(run, build):
    expected_binding = {"scheme": "current_r4", "build_state": build["state"],
        "receipt_pin": build_contract.CURRENT_BUILD_PIN, "build_helper_pins": build["build_helper_freeze"],
        "actual_SQL_qualified": False}
    c.require(typed_equal(run.get("compiled_build_binding"), expected_binding), "CURRENT_AUTHORITY_BUILD_BINDING")
    inventories(run, build)
    c.require(typed_equal(run["resource_policy"], EXPECTED_POLICY)
        and typed_equal(run["pre_hash_limits"], {"affinity_mask": 1, "priority_class": 16384,
            "logical_cpu_limit": 1, "priority": "BelowNormal"})
        and type(run["pre_hash_stable_samples"]) is int and run["pre_hash_stable_samples"] == 2
        and run["resource_stop_reason"] is None and run["resource_watcher_cleanup_confirmed"] is True,
        "CURRENT_AUTHORITY_RESOURCE_POLICY")
    samples = run["resource_samples"]
    c.require(isinstance(samples, list) and bool(samples) and all(
        finite(row[key], 0, 100) for row in samples for key in
        ("system_cpu_percent", "available_ram_percent", "commit_used_percent")), "CURRENT_AUTHORITY_SAMPLES")
    total = samples[0]["total_ram_mib"]
    c.require(finite(total, 1), "CURRENT_AUTHORITY_TOTAL_RAM")
    profiles = run["owned_host_job_profiles"]
    c.require(isinstance(profiles, list) and bool(profiles), "CURRENT_AUTHORITY_JOBS_MISSING")
    for profile in profiles:
        limits, accounting = profile["limits_readback"], profile["last_job_accounting"]
        wanted = {"verified": True, "cpu_hard_cap_machine_percent": 6.25, "affinity_mask": 1,
            "priority_class": 16384, "active_process_limit": 16, "kill_on_close": True, "breakaway_disabled": True}
        c.require(all(typed_equal(limits.get(key), value) for key, value in wanted.items())
            and all(profile.get(key) is True for key in
                ("worker_created", "job_assigned", "target_authorized", "owned_tree_empty", "cleanup_confirmed", "job_handle_closed"))
            and type(accounting["active_processes"]) is int and accounting["active_processes"] == 0
            and accounting["owned_processes"] == [], "CURRENT_AUTHORITY_JOB_LIMITS_OR_CLEANUP")
        limit = limits["job_private_limit_mib"]
        c.require(finite(limit, 0.001) and (0 < 100*limit/total <= 1.01 or 6.99 <= 100*limit/total <= 7.01)
            and finite(accounting["peak_job_private_mib"], 0, limit)
            and finite(accounting["job_cpu_seconds"]), "CURRENT_AUTHORITY_JOB_MEMORY_OR_ACCOUNTING")


def validate_current_case(run, build, manifest, case, mode, outcome):
    c.require((case, mode, outcome) in REQUIRED, "CURRENT_AUTHORITY_CASE_SLOT")
    import verify_formula_issuer_authority_current as authority
    import verify_formula_issuer_live_current as approval
    validate_current_resources(run, build)
    result = run["product_probe"]["result"]
    wanted_schema = "hwpx-agent.p09-146-live-consumer-approval-sql22/v1" if case == "approval" else \
        "hwpx-agent.p09-148-live-authority-consumer-sql22/v1"
    c.require(run["schema_version"] == wanted_schema and result["state"] == run["state"]
        and result["P09_gate"] == "OPEN" and result["product_complete"] is False
        and result["real_approval_signature_and_original_consumer_executed"] is True
        and run["real_AEAD_executed"] is True, "CURRENT_AUTHORITY_COMPONENT_SCOPE")
    if case == "approval":
        approval.validate_case(run, build, manifest, mode, outcome)
    else:
        authority.validate_case(run, build, manifest, case, mode, outcome, scheme="current_r4")
    expected = [("postgres", "metadata", authority.CHECKS),
        ("p141_changed_schema", "changed_schema_denied", ["changed_schema22_fingerprint_denied"]),
        ("p141_correct_schema", "correct_schema_admitted", ["correct_schema22_fingerprint_control_admitted"])]
    c.require(len(run["probe_runs"]) == 3 and all(row["database"] == database and row["exit_code"] == 0
        and row["result"]["checks"] == checks and row["result"]["mode"] == kind
        and row["result"]["state"] == "PASS_RUST_SQL22_METADATA_NOT_CRYPTO_NATIVE_OR_GATE"
        and row["result"]["failed_stage"] is None and row["result"]["error_code"] is None
        and row["result"]["real_crypto_executed"] is False and row["result"]["product_complete"] is False
        and row["result"]["P09_gate"] == "OPEN" for row, (database, kind, checks) in zip(run["probe_runs"], expected)),
        "CURRENT_AUTHORITY_METADATA_CONTROLS")
    controls = run["schema_controls"]
    c.require(len(run["migrations_applied"]) == 22 and len(controls["base_migrations"]) == 21
        and controls["wrong_fingerprint"] == "0"*64
        and controls["correct_fingerprint"] == controls["SQL22_source_pin"]["sha256"]
        and controls["same_original_migration_and_grants"] is True
        and controls["schema_identity_or_triggers_mutated"] is False, "CURRENT_AUTHORITY_SCHEMA_CONTROLS")


def missing_replays(cases):
    c.require(isinstance(cases, dict) and set(cases).issubset({(case, mode) for case, mode, _ in REQUIRED}),
        "CURRENT_AUTHORITY_REPLAY_INVENTORY")
    return [{"case": case, "input_mode": mode, "expected_outcome": outcome, "state": "NOT_RUN_OR_NOT_ACCEPTED"}
        for case, mode, outcome in REQUIRED if (case, mode) not in cases]


def require_all_replays(cases, build, manifest):
    missing_replays(cases)
    for (case, mode), run in cases.items():
        validate_current_case(run, build, manifest, case, mode, "unchanged" if mode == "original" else "changed")
    c.require(not missing_replays(cases), "CURRENT_AUTHORITY_REQUIRED_REPLAYS_MISSING")


def merge_pins(groups):
    merged = {}
    for rows in groups:
        for raw in rows:
            pin = build_contract.inputs.pin_shape(raw)
            c.require(merged.get(pin["path"], pin) == pin, "CURRENT_AUTHORITY_PIN_CONFLICT")
            merged[pin["path"]] = pin
    return merged
