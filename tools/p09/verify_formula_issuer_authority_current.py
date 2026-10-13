"""P148 current trust/policy SQL audit; no build, DB creation, or native execution."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from idle_resource_admission import IdleResources
from run_formula_issuer_corpus_unit_probe import EXPECTED
from run_formula_issuer_authority_sql_probe import CHECKS, ROOT_CHECKS
from run_formula_issuer_registry_sql_checks import ROOT, require
from audit_evidence_io import AuditEvidenceReader
from bounded_container_absence import inspect_absence
from bounded_audit_tools import run_audit_tool
from run_resource_bounded_python import observed_limits
from verify_formula_issuer_live_current import authenticate_baseline, remove_block, replace_one

BASE = "target/p09-121-resource-optimized/"
EVIDENCE = "implementation/p09/evidence/"
SOURCE = "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"
DRIVER = "tools/p09/run_formula_issuer_authority_sql_probe.py"
PRIOR = EVIDENCE + "p09-147-current-approval.progress.v1.json"
SELF = "tools/p09/verify_formula_issuer_authority_current.py"
REPORT = "implementation/p09/P09-148_LIVE_AUTHORITY_SQL_REVALIDATION_REPORT.md"
ARCHIVES = ["p09-146-pre-live-sql-consumer", "p09-146-pre-timeout-diagnostics",
    "p09-146-pre-unit4-and-marker-normalization", "p09-146-pre-strict-lint-corrections",
    "p09-148-pre-live-authority", "p09-148-initial-method-binding", "p09-148-pre-strict-lint-correction",
    "p09-148-pre-owned-absence-audit", "p09-148-pre-owned-absence-report", "p09-148-pre-admission-diagnostics",
    "p09-148-pre-admission-source-guard", "p09-148-pre-streaming-progress",
    "p09-149-pre-bounded-audit-integration"]
CASES = [(5, "trust", "original", "unchanged"), (6, "trust", "numeric_derivative", "changed"),
         (7, "policy", "original", "unchanged"), (10, "policy", "numeric_derivative", "changed")]


def authenticate_authority_delta(current, original, checkpoint=None):
    current = replace_one(current, "                revocation::postgres::PostgresFormulaPolicyRevoker,\n", "")
    current = replace_one(current,
        "                FormulaApprovalRevocation, FormulaIssuerTrustRevocation,\n"
        "                FormulaRegistryManagementAction, LocalPostgresFormulaRegistryManagementRepository,\n",
        "                FormulaApprovalRevocation, LocalPostgresFormulaRegistryManagementRepository,\n")
    current = replace_one(current, "        revocation::SourceFormulaPolicyRevocationRequest,\n", "")
    current = replace_one(current,
        '    if std::env::var_os("P148_LIVE_CASE").is_some() {\n'
        '        return verify_live_authority(probe, p, provider, prepared, raw, wanted, binding);\n'
        '    }\n', "")
    current = remove_block(current, "fn verify_live_authority(", "fn revocation_race(")
    formatted = run_audit_tool("rustfmt-stdin", current, checkpoint=checkpoint)
    require(formatted.returncode == 0 and not formatted.stderr
        and formatted.stdout.replace("\r\n", "\n") == original.decode("utf-8").replace("\r\n", "\n"),
        "original_approval_consumer_undeclared_delta")
    return formatted.audit_limits


def authenticate_admission_driver_delta(current, original):
    current = remove_block(current, "class AdmissionRefusal(ValueError):", "def main(")
    current = replace_one(current, "pre_hash_stable_samples = admit_or_explain(resources)",
                          "pre_hash_stable_samples = admit(resources)")
    current = replace_one(current,
        '        report = {"state": "FAIL_CLOSED_BEFORE_OWNED_CONTAINER", "error_code": code, "P09_gate": "OPEN"}\n'
        '        if isinstance(error, AdmissionRefusal):\n'
        '            report["admission_diagnostics"] = error.diagnostics\n'
        '        print(json.dumps(report))',
        '        print(json.dumps({"state": "FAIL_CLOSED_BEFORE_OWNED_CONTAINER", "error_code": code, "P09_gate": "OPEN"}))')
    require(current.replace("\r\n", "\n") == original.decode("utf-8").replace("\r\n", "\n"),
            "SQL_driver_undeclared_delta")



def authenticate_streaming_driver_delta(current, original):
    """Reviewed capture-only import, inventory and command delta; no other byte changes."""
    expected = original.decode("utf-8").replace("\r\n", "\n")
    edits = [
        [
            "from run_resource_bounded_python import admit, observed_limits\n",
            "from run_resource_bounded_python import admit, observed_limits\nfrom bounded_process_progress import BoundedProcessCapture\n"
        ],
        [
            "        \"tools/p09/run_formula_issuer_authority_sql_probe.py\",\n",
            "        \"tools/p09/run_formula_issuer_authority_sql_probe.py\",\n        \"tools/p09/bounded_process_progress.py\",\n"
        ],
        [
            "    def command(args, text=None, timeout=20, cleanup=False, env=None, rust=False):\n        nonlocal last_child\n        if not cleanup:\n            require(not resources.stop.is_set(), resources.reason or \"resource_stop\")\n            require(time.monotonic() - start < 240, \"adapter_total_time_limit\")\n        process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE,\n            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding=\"utf-8\", errors=\"replace\",\n            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)\n        deadline, first = time.monotonic() + timeout, text\n        next_observation = time.monotonic() + 10\n        try:\n            affinity, system = ctypes.c_size_t(), ctypes.c_size_t()\n            resources.k.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]\n            require(resources.k.GetProcessAffinityMask(int(process._handle), ctypes.byref(affinity), ctypes.byref(system))\n                and affinity.value == 1, \"owned_child_affinity_not_inherited\")\n            if rust:\n                resources.k.GetPriorityClass.argtypes = [ctypes.c_void_p]\n                require(resources.k.GetPriorityClass(int(process._handle)) == 0x4000, \"rust_priority_not_applied\")\n            while True:\n                try:\n                    output, errors = process.communicate(input=first, timeout=0.25)\n                    break\n                except subprocess.TimeoutExpired as partial:\n                    first = None\n                    if rust and args[0] == str(ROOT / crypto_executable[\"path\"]):\n                        progress = partial.stderr or b\"\"\n                        if isinstance(progress, bytes):\n                            progress = progress.decode(\"utf-8\", errors=\"replace\")\n                        require(len(progress.encode(\"utf-8\")) <= 32768, \"live_progress_output_limit\")\n                        markers = re.findall(r\"(?m)^P146_STAGE:([A-Za-z0-9_]+)$\", progress.replace(\"\\r\\n\", \"\\n\"))\n                        allowed_markers = {\"source_begin\", \"consumer_begin\", \"live_begin\", \"connect_first_begin\",\n                            \"connect_second_begin\", \"stale_CAS_begin\", \"race_begin\", \"race_joined\", \"denied_callback_begin\"}\n                        require(set(markers).issubset(allowed_markers), \"live_progress_marker_scope\")\n                        receipt[\"live_progress_markers\"] = markers\n                        if time.monotonic() >= next_observation and time.monotonic() + 3 < deadline:\n                            next_observation = time.monotonic() + 10\n                            # 자기 UUID/label로 admission한 DB의 read-only 대기 metadata만 수집한다.\n                            activity_sql = \"SELECT coalesce(json_agg(json_build_object('app',application_name,'state',state,'wait_type',wait_event_type,'wait',wait_event,'blocked_count',cardinality(pg_blocking_pids(pid)))),'[]'::json) FROM pg_stat_activity WHERE datname='postgres' AND backend_type='client backend' AND application_name LIKE 'hwpx-agent-%';\"\n                            try:\n                                observed = subprocess.run([docker, \"exec\", created_id, \"psql\", \"-X\", \"-U\", \"postgres\",\n                                    \"-d\", \"postgres\", \"-At\", \"-c\", activity_sql], cwd=ROOT, capture_output=True,\n                                    text=True, timeout=3, check=False,\n                                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)\n                                require(observed.returncode == 0 and len(observed.stdout) <= 16384, \"live_wait_observation_failed\")\n                                rows = json.loads(observed.stdout)\n                                require(isinstance(rows, list) and len(rows) <= 32, \"live_wait_inventory_scope\")\n                                require(all(set(row) == {\"app\", \"state\", \"wait_type\", \"wait\", \"blocked_count\"} for row in rows), \"live_wait_field_scope\")\n                                receipt.setdefault(\"live_wait_observations\", []).append({\"elapsed_seconds\": round(time.monotonic()-start, 2), \"rows\": rows})\n                            except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):\n                                receipt.setdefault(\"live_wait_observations\", []).append({\"observation\": \"unavailable_no_raw_log\"})\n                    if not cleanup:\n                        require(not resources.stop.is_set(), resources.reason or \"resource_stop\")\n                    require(time.monotonic() < deadline, \"owned_command_timeout\")\n        finally:\n            if process.poll() is None:\n                process.kill()\n                process.communicate()\n        last_child = subprocess.CompletedProcess(args, process.returncode, output, errors)\n        return last_child\n\n",
            "    def command(args, text=None, timeout=20, cleanup=False, env=None, rust=False):\n        nonlocal last_child\n        if not cleanup:\n            require(not resources.stop.is_set(), resources.reason or \"resource_stop\")\n            require(time.monotonic() - start < 240, \"adapter_total_time_limit\")\n        process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE,\n            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding=\"utf-8\", errors=\"replace\",\n            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)\n        deadline, first = time.monotonic() + timeout, text\n        next_observation = time.monotonic() + 10\n        capture = None\n        try:\n            affinity, system = ctypes.c_size_t(), ctypes.c_size_t()\n            resources.k.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]\n            require(resources.k.GetProcessAffinityMask(int(process._handle), ctypes.byref(affinity), ctypes.byref(system))\n                and affinity.value == 1, \"owned_child_affinity_not_inherited\")\n            if rust:\n                resources.k.GetPriorityClass.argtypes = [ctypes.c_void_p]\n                require(resources.k.GetPriorityClass(int(process._handle)) == 0x4000, \"rust_priority_not_applied\")\n            if rust and args[0] == str(ROOT / crypto_executable[\"path\"]):\n                require(text is None, \"live_progress_stdin_not_supported\")\n                capture = BoundedProcessCapture(process)\n            while True:\n                try:\n                    if capture is None:\n                        output, errors = process.communicate(input=first, timeout=0.25)\n                    else:\n                        output, errors = capture.communicate(timeout=0.25)\n                    break\n                except subprocess.TimeoutExpired:\n                    first = None\n                    if capture is not None:\n                        markers, observations = capture.progress()\n                        receipt[\"live_progress_markers\"] = markers\n                        receipt[\"live_progress_observations\"] = observations\n                        if time.monotonic() >= next_observation and time.monotonic() + 3 < deadline:\n                            next_observation = time.monotonic() + 10\n                            # 자기 UUID/label로 admission한 DB의 read-only 대기 metadata만 수집한다.\n                            activity_sql = \"SELECT coalesce(json_agg(json_build_object('app',application_name,'state',state,'wait_type',wait_event_type,'wait',wait_event,'blocked_count',cardinality(pg_blocking_pids(pid)))),'[]'::json) FROM pg_stat_activity WHERE datname='postgres' AND backend_type='client backend' AND application_name LIKE 'hwpx-agent-%';\"\n                            try:\n                                observed = subprocess.run([docker, \"exec\", created_id, \"psql\", \"-X\", \"-U\", \"postgres\",\n                                    \"-d\", \"postgres\", \"-At\", \"-c\", activity_sql], cwd=ROOT, capture_output=True,\n                                    text=True, timeout=3, check=False,\n                                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)\n                                require(observed.returncode == 0 and len(observed.stdout) <= 16384, \"live_wait_observation_failed\")\n                                rows = json.loads(observed.stdout)\n                                require(isinstance(rows, list) and len(rows) <= 32, \"live_wait_inventory_scope\")\n                                require(all(set(row) == {\"app\", \"state\", \"wait_type\", \"wait\", \"blocked_count\"} for row in rows), \"live_wait_field_scope\")\n                                receipt.setdefault(\"live_wait_observations\", []).append({\"elapsed_seconds\": round(time.monotonic()-start, 2), \"rows\": rows})\n                            except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):\n                                receipt.setdefault(\"live_wait_observations\", []).append({\"observation\": \"unavailable_no_raw_log\"})\n                    if not cleanup:\n                        require(not resources.stop.is_set(), resources.reason or \"resource_stop\")\n                    require(time.monotonic() < deadline, \"owned_command_timeout\")\n        finally:\n            if process.poll() is None:\n                process.kill()\n                if capture is None:\n                    process.communicate()\n                else:\n                    process.wait(timeout=2)\n            if capture is not None:\n                capture.close()\n                if not capture.error:\n                    markers, observations = capture.progress()\n                    receipt[\"live_progress_markers\"] = markers\n                    receipt[\"live_progress_observations\"] = observations\n        last_child = subprocess.CompletedProcess(args, process.returncode, output, errors)\n        return last_child\n\n"
        ]
    ]
    for before, after in edits:
        expected = replace_one(expected, before, after)
    require(current.replace("\r\n", "\n") == expected, "streaming_driver_undeclared_delta")


def validate_case(run, build, manifest, case, mode, outcome, *, scheme="legacy"):
    require(scheme in {"legacy", "current_r4"}, "authority_build_scheme_invalid")
    result = run["product_probe"]["result"]
    require(run["schema_version"] == "hwpx-agent.p09-148-live-authority-consumer-sql22/v1"
        and run["state"] == result["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
        and run["product_probe"]["exit_code"] == 0 and result["failed_stage"] is None
        and result["checks"] == ROOT_CHECKS and len(ROOT_CHECKS) == len(set(ROOT_CHECKS)) == 33
        and run["product_executable_pin"] == build["executable_pin"]
        and run["source_freeze_exact_after"] is True and run["protected_executables_exact_after"] is True
        and run["container_removed"] is True and run["resource_stop_reason"] is None
        and run["source_index"] == result["source_index"] == 0
        and run["live_case"] == case and run["input_mode"] == result["input_mode"] == mode
        and run["expected_formula_outcome"] == result["formula_outcome"] == outcome
        and run["frozen_original_source_pin"] == manifest["actual_inputs"][0]
        and result["original_source_sha256"] == manifest["actual_inputs"][0]["sha256"],
        "authority_case_identity_or_outcome_drift")
    require((mode == "original" and result["source_sha256"] == result["original_source_sha256"]
             and result["only_one_numeric_leaf_changed"] is False)
        or (mode == "numeric_derivative" and re.fullmatch(r"[0-9a-f]{64}", result["source_sha256"])
            and result["source_sha256"] != result["original_source_sha256"]
            and result["only_one_numeric_leaf_changed"] is True), "original_derivative_boundary")
    require(run["trust_revocation_consumer_component_executed"] is (case == "trust")
        and run["policy_revocation_consumer_component_executed"] is (case == "policy")
        and all(run[key] is True for key in ("actual_SQL_executed", "actual_Rust_DB_adapter_executed",
            "real_AEAD_executed", "real_Ed25519_approval_signature_executed", "original_product_consumer_executed"))
        and result["real_approval_signature_and_original_consumer_executed"] is True
        and run["probe_runs"][0]["result"]["checks"] == CHECKS and len(CHECKS) == 42
        and len(run["probe_runs"]) == 3 and run["original_full_ir_assertions"] == 25
        and len(set(run["original_SQL22_checks_committed"])) == 37
        and run["final_history"] == {"root_history": 4, "root_max": 4, "approval_history": 4,
            "approval_max": 3, "root_revocations": 3 if case == "trust" else 2,
            "approval_revocations": 2, "current_source_policy_revocations": 1 if case == "policy" else 0},
        "authority_SQL_history_or_checks_drift")
    controls = run["schema_controls"]
    expected_metadata = [("postgres", "metadata", CHECKS),
        ("p141_changed_schema", "changed_schema_denied", ["changed_schema22_fingerprint_denied"]),
        ("p141_correct_schema", "correct_schema_admitted", ["correct_schema22_fingerprint_control_admitted"])]
    require(all(row["database"] == database and row["exit_code"] == 0
        and row["result"]["mode"] == mode_name and row["result"]["checks"] == checks
        and row["result"]["state"] == "PASS_RUST_SQL22_METADATA_NOT_CRYPTO_NATIVE_OR_GATE"
        and row["result"]["failed_stage"] is None and row["result"]["error_code"] is None
        and row["result"]["real_crypto_executed"] is False and row["result"]["product_complete"] is False
        and row["result"]["P09_gate"] == "OPEN"
        for row, (database, mode_name, checks) in zip(run["probe_runs"], expected_metadata, strict=True))
        and len(run["migrations_applied"]) == 22 and len(controls["base_migrations"]) == 21
        and controls["wrong_fingerprint"] == "0" * 64
        and controls["correct_fingerprint"] == controls["SQL22_source_pin"]["sha256"]
        and controls["same_original_migration_and_grants"] is True
        and controls["schema_identity_or_triggers_mutated"] is False, "schema_security_controls_drift")
    require(all(run[key] is False for key in ("native_application_executed", "product_complete",
        "all_36_source_inputs_qualified", "durable_blob_store_qualified", "production_key_custody_qualified",
        "atomic_product_publication_qualified", "observed_graph_native_fidelity_qualified",
        "issuer_provisioning_generation_race_qualified", "trust_revocation_consumer_qualified"))
        and run["P09_gate"] == run["A12_gate"] == run["A13_gate"] == "OPEN"
        and result["P09_gate"] == "OPEN" and result["product_complete"] is False,
        "authority_component_scope_promoted")
    policy = run["resource_policy"]
    if scheme == "current_r4":
        from current_authority_sql_receipts import validate_current_resources
        validate_current_resources(run, build)
        return
    require(policy["logical_cpu_limit"] == 1 and policy["priority"] == "BelowNormal"
        and policy["cpu_stop_percent"] == 85 and policy["cpu_stop_consecutive_samples"] == 3
        and policy["minimum_available_ram_mib"] == 4096 and policy["container_memory_bytes"] == 536870912
        and policy["post_hash_idle_CPU_max_percent"] == 50 and policy["post_hash_idle_RAM_min_mib"] == 8192
        and policy["post_hash_idle_consecutive_samples"] == 3 and policy["pids_limit"] == 64
        and run["pre_hash_limits"]["logical_cpu_limit"] == 1
        and run["pre_hash_limits"]["priority"] == "BelowNormal" and run["pre_hash_stable_samples"] == 3,
        "authority_resource_policy_drift")


def validate_timeout_failure(run, build, manifest, *, error_code="owned_command_timeout", observation_count=5):
    """Preserve recorded failures; a previous command exit0 is not consumer success."""
    expected_stop = {"owned_command_timeout": None, "STOP_SUSTAINED_SYSTEM_CPU": "STOP_SUSTAINED_SYSTEM_CPU"}
    require((error_code, observation_count) in {("owned_command_timeout", 5), ("STOP_SUSTAINED_SYSTEM_CPU", 4)},
        "failure_expectation_not_allowlisted")
    require(run["schema_version"] == "hwpx-agent.p09-148-live-authority-consumer-sql22/v1"
        and run["state"] == "FAIL_CLOSED" and run["error_code"] == error_code
        and run["failed_stage"] == "original_source_policy_signature_consumer_SQL_workflow"
        and "product_probe" not in run and "final_history" not in run
        and run["source_index"] == 0 and run["live_case"] == "policy"
        and run["input_mode"] == "numeric_derivative" and run["expected_formula_outcome"] == "changed"
        and run["product_executable_pin"] == build["executable_pin"]
        and run["frozen_original_source_pin"] == manifest["actual_inputs"][0]
        and run["container_removed"] is True and run["resource_stop_reason"] == expected_stop[error_code]
        and run["source_freeze_exact_after"] is False and run["protected_executables_exact_after"] is False,
        "timeout_failure_relabelled_or_wrong_identity")
    require(all(run[k] is False for k in ("trust_revocation_consumer_component_executed",
        "policy_revocation_consumer_component_executed", "original_product_consumer_executed",
        "real_AEAD_executed", "real_Ed25519_approval_signature_executed", "native_application_executed",
        "product_complete", "all_36_source_inputs_qualified", "issuer_provisioning_generation_race_qualified",
        "durable_blob_store_qualified", "production_key_custody_qualified", "atomic_product_publication_qualified",
        "observed_graph_native_fidelity_qualified", "trust_revocation_consumer_qualified"))
        and run["P09_gate"] == run["A12_gate"] == run["A13_gate"] == "OPEN"
        and run["last_command_exit_code"] == 0 and run["sqlstate"] is None
        and run["consumer_error_codes"] == [] and len(run["probe_runs"]) == 1
        and run["probe_runs"][0]["exit_code"] == 0
        and run["probe_runs"][0]["result"]["checks"] == CHECKS,
        "timeout_failure_promoted_or_error_invented")
    require(run["resource_policy"] == {"logical_cpu_limit": 1, "priority": "BelowNormal",
        "container_memory_bytes": 536870912, "post_hash_idle_CPU_max_percent": 50,
        "post_hash_idle_RAM_min_mib": 8192, "post_hash_idle_consecutive_samples": 3,
        "container_swap_total_bytes": 536870912, "pids_limit": 64, "cpu_stop_percent": 85,
        "cpu_stop_consecutive_samples": 3, "minimum_available_ram_mib": 4096, "sample_seconds": 2},
        "timeout_failure_resource_policy_changed")
    observations = run["live_wait_observations"]
    require(len(observations) == observation_count and run["live_progress_markers"] == [], "timeout_diagnostics_inventory_changed")
    if expected_stop[error_code]:
        require(len(run["resource_samples"]) >= 3
            and all(r["system_cpu_percent"] >= 85 for r in run["resource_samples"][-3:]),
            "CPU_stop_not_bound_to_three_actual_hot_samples")
    for observation in observations:
        require(set(observation) == {"elapsed_seconds", "rows"} and len(observation["rows"]) == 4,
            "timeout_diagnostics_fields_changed")
        for row in observation["rows"]:
            require(set(row) == {"app", "state", "wait_type", "wait", "blocked_count"}
                and row["app"] in {"hwpx-agent-local-formula-registry-artifacts-schema22",
                    "hwpx-agent-local-formula-registry-read-schema22", "hwpx-agent-local-formula-registry-management-schema22"}
                and row["state"] in {"idle", "idle in transaction"}
                and row["wait_type"] == "Client" and row["wait"] == "ClientRead"
                and type(row["blocked_count"]) is int and row["blocked_count"] == 0,
                "timeout_diagnostics_raw_or_wrong_observation")


def validate_owned_absence(receipt, runs):
    require(receipt["schema_version"] == "hwpx-agent.p09-148-owned-absence/v1"
        and receipt["state"] == "OWNED_SQL_RUN01_TO05_IDS_AND_NAMES_INDEPENDENTLY_ABSENT_NOT_FULL_AUTHORITY_AUDIT"
        and receipt["read_only_docker_inspect_only"] is True
        and receipt["build_test_SQL_native_started"] is False
        and receipt["current_authority_cases_qualified"] is False
        and receipt["native_application_executed"] is False and receipt["product_complete"] is False
        and receipt["P09_gate"] == "OPEN", "owned_absence_scope_promoted")
    require(set(runs) == set(range(1, 6)), "owned_absence_run_inventory")
    wanted = {(number, reference) for number, run in runs.items()
        for reference in (run["container_id"], run["container_name"])}
    rows = receipt["independent_absence_checks"]
    require(len(rows) == len(wanted) == 10
        and len({(r["run"], r["reference"]) for r in rows}) == 10
        and {(r["run"], r["reference"]) for r in rows} == wanted
        and all(set(r) == {"run", "reference", "absent", "inspect_exit_code"}
            and type(r["run"]) is int and r["absent"] is True
            and type(r["inspect_exit_code"]) is int and r["inspect_exit_code"] != 0 for r in rows),
        "owned_absence_missing_duplicated_or_wrong_reference")
    expected_paths = {EVIDENCE + f"p09-148-authority-consumer-run{n:02}.v1.json" for n in runs}
    require(len(receipt["receipts_freshly_double_hashed"]) == 5
        and {r["path"] for r in receipt["receipts_freshly_double_hashed"]} == expected_paths
        and receipt["limits"]["logical_cpu_limit"] == receipt["limits"]["affinity_mask"] == 1
        and receipt["limits"]["priority"] == "BelowNormal", "owned_absence_receipt_or_limit_inventory")


def audit(resources):
    def checkpoint():
        require(not resources.stop.is_set(), resources.reason or "resource_stop")

    reader = AuditEvidenceReader(ROOT, checkpoint)
    readonly_tool_profiles = []
    snapshots, originals = reader.snapshots, {}
    pin, load = reader.pin, reader.json

    for path in ("tools/p09/bounded_audit_tools.py", "tools/p09/tests/test_bounded_audit_tools.py",
                 "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
                 "tools/p09/verify_bounded_audit_tools_light.py", "tools/p09/tests/test_bounded_audit_tool_integration.py",
                 "tools/p09/verify_bounded_audit_tool_integration_light.py",
                 "implementation/p09/source-archive/p09-149-pre-bounded-audit-integration/source-preimages.v1.json",
                 "implementation/p09/source-archive/p09-149-pre-integration-setup-repair/source-preimages.v1.json",
                 "tools/p09/audit_evidence_io.py", "tools/p09/tests/test_audit_evidence_io.py",
                 "tools/p09/tests/test_live_audit_io_integration.py", "tools/p09/verify_live_audit_io_light.py",
                 "implementation/p09/source-archive/p09-149-pre-live-audit-bound-io/source-preimages.v1.json",
                 "tools/p09/bounded_container_absence.py", "tools/p09/tests/test_bounded_container_absence.py",
                 "tools/p09/bounded_process_progress.py", "tools/p09/tests/test_live_absence_integration.py",
                 "tools/p09/verify_live_absence_light.py",
                 "implementation/p09/source-archive/p09-149-pre-live-bounded-absence/source-preimages.v1.json"):
        pin(path)
    for path in ("rustfmt.toml", ".rustfmt.toml", "rust-toolchain.toml", "rust-toolchain"):
        if (ROOT / path).exists():
            pin(path)

    def exact(rows, historical=False):
        for row in rows:
            actual = pin(row["path"])
            identity = (row["path"], row["bytes"], row["sha256"])
            require(actual == row or (historical and identity in originals), "current_or_archived_pin_drift")

    for name in ARCHIVES:
        archive = load(f"implementation/p09/source-archive/{name}/source-preimages.v1.json")
        require(archive["schema_version"] == "hwpx-agent.source-preimages/v1", "archive_schema_drift")
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "archive_bytes_drift")
            originals[(row["path"], row["bytes"], row["sha256"])] = raw
    prior = load(PRIOR)
    require(prior["state"] == "CURRENT_APPROVAL_SQL27_AND_STRICT_LINT_COMPONENT_PASS_NOT_NATIVE_OR_GATE"
        and prior["unique_files_freshly_double_hashed"] == len(prior["verified_direct_pins"]) == 1023
        and len({r["path"] for r in prior["verified_direct_pins"]}) == 1023
        and prior["product_complete"] is False and prior["P09_gate"] == "OPEN", "P147_checkpoint_drift")
    exact(prior["verified_direct_pins"], historical=True)
    partial = load(EVIDENCE + "p09-148-authority.partial-checkpoint.v1.json")
    require(partial["state"] == "PARTIAL_CURRENT_TRUST_SQL33_PASS_FULL_REPLAY_WAITING_RESOURCE_ADMISSION"
        and partial["selected_files_freshly_double_hashed"] == len(partial["selected_direct_pins"]) == 26
        and partial["whole_workspace_fresh_hash_audit_executed"] is False
        and partial["full_current_authority_audit"] == "NOT_RUN" and partial["product_complete"] is False,
        "partial_checkpoint_promoted")
    exact(partial["selected_direct_pins"], historical=True)
    driver_row = next(r for r in partial["selected_direct_pins"] if r["path"] == DRIVER)
    original_driver = originals[(DRIVER, driver_row["bytes"], driver_row["sha256"])]
    stream_archive = load("implementation/p09/source-archive/p09-148-pre-streaming-progress/source-preimages.v1.json")
    stream_row = stream_archive["files"][0]
    require(stream_row["path"] == DRIVER and stream_row["sha256"] == "6b408bda1f803f6119d56ec77ccff4789e9793dbea9126ab8a09661bc4bef2a5",
        "pre_streaming_driver_identity_changed")
    pre_streaming_driver = originals[(DRIVER, stream_row["bytes"], stream_row["sha256"])]
    authenticate_streaming_driver_delta(reader.text(DRIVER), pre_streaming_driver)
    authenticate_admission_driver_delta(pre_streaming_driver.decode("utf-8"), original_driver)

    def driver_exact(rows):
        for row in rows:
            if row["path"] == DRIVER and row in (driver_row, stream_row):
                exact([row], historical=True)
            else:
                exact([row])
    absence_path = EVIDENCE + "p09-148-owned-absence-run01.v1.json"
    owned_absence = load(absence_path)
    old_runs = {n: load(EVIDENCE + f"p09-148-authority-consumer-run{n:02}.v1.json") for n in range(1, 6)}
    validate_owned_absence(owned_absence, old_runs)
    exact(owned_absence["receipts_freshly_double_hashed"])
    old = next(row for row in prior["verified_direct_pins"] if row["path"] == SOURCE)
    accepted_source = originals[(SOURCE, old["bytes"], old["sha256"])]
    readonly_tool_profiles.append(authenticate_authority_delta(reader.text(SOURCE), accepted_source,
        checkpoint=checkpoint))
    baseline_archive = load("implementation/p09/source-archive/p09-146-pre-live-sql-consumer/source-preimages.v1.json")
    baseline_row = next(r for r in baseline_archive["files"] if r["path"] == SOURCE)
    readonly_tool_profiles.append(authenticate_baseline(accepted_source.decode("utf-8"),
        originals[(SOURCE, baseline_row["bytes"], baseline_row["sha256"])], checkpoint=checkpoint))
    failed = load(BASE + "p143-issuer-product-build-r12.json")
    require(failed["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and failed["exit_code"] == 101
        and len(failed["diagnostics"]) == 2 and all(r["code"] == "E0599" for r in failed["diagnostics"]),
        "initial_compile_failure_not_preserved")
    exact(failed["source_freeze"], historical=True)
    exact(failed["protected_executables"])
    for number in range(1, 5):
        old_run = load(EVIDENCE + f"p09-148-authority-consumer-run{number:02}.v1.json")
        require(old_run["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
            and old_run["container_removed"] is True, "pre_lint_runtime_status_changed")
        exact(old_run["source_freeze"], historical=True)
        exact(old_run["protected_executables"])
    failed_lint = load(BASE + "p148-workspace-lint-r1.json")
    require(failed_lint["state"] == "NOT_ACCEPTED_STOP_OR_FAILURE" and failed_lint["exit_code"] == 101
        and len(failed_lint["diagnostics"]) == 1
        and failed_lint["diagnostics"][0]["code"] == "clippy::too_many_lines", "initial_strict_lint_failure_not_preserved")
    exact(failed_lint["source_freeze"], historical=True)
    exact(failed_lint["protected_executables"])
    build = load(BASE + "p143-issuer-product-build-r14.json")
    unit_build = load(BASE + "p143-typed-route-unit-build-r7.json")
    unit = load(BASE + "p144-corpus-unit-run6.json")
    require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["catalog_profile"]["test"] is False
        and unit_build["state"] == "PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION" and unit_build["catalog_profile"]["test"] is True
        and all(r["exit_code"] == 0 and not r["diagnostics"] and r["source_freeze_exact_after"]
            and r["protected_executables_exact_after"] and r["logical_cpu_limit"] == r["cargo_jobs"] == 1
            and r["priority"] == "BelowNormal" for r in (build, unit_build))
        and len(build["source_freeze"]) == 842 and len(unit_build["source_freeze"]) == 843,
        "current_build_not_accepted")
    require(unit["state"] == "PASS_TYPED_ROUTE_AND_SOURCE_INDEX_UNIT11_NOT_DB_NATIVE_OR_GATE"
        and unit["test_process_started"] is True and unit["tests"] == EXPECTED
        and unit["executable_pin"] == unit_build["executable_pin"] and unit["actual_DB_or_native_executed"] is False,
        "current_unit11_not_accepted")
    for receipt in (build, unit_build, unit):
        exact(receipt["source_freeze"])
        exact(receipt["protected_executables"] + [receipt["executable_pin"]])
    bootstrap = load(EVIDENCE + "p09-145-resource-bootstrap-run07.v1.json")
    require(bootstrap["state"] == "PASS_PRE_HASH_RESOURCE_BOUND_TARGET_ACCEPTED_NOT_NATIVE_OR_GATE"
        and bootstrap["target_exit_code"] == 0 and bootstrap["target_started"] is True, "unit_bootstrap_not_accepted")
    manifest = load(EVIDENCE + "p09-77-document-import-active-security.source-progress.v1.json")
    require(len(manifest["actual_inputs"]) == 36, "original_manifest_inventory")
    timed_out = load(EVIDENCE + "p09-148-authority-consumer-run08.v1.json")
    validate_timeout_failure(timed_out, build, manifest)
    driver_exact(timed_out["source_freeze"])
    exact(timed_out["protected_executables"])
    cpu_stopped = load(EVIDENCE + "p09-148-authority-consumer-run09.v1.json")
    validate_timeout_failure(cpu_stopped, build, manifest, error_code="STOP_SUSTAINED_SYSTEM_CPU", observation_count=4)
    driver_exact(cpu_stopped["source_freeze"])
    exact(cpu_stopped["protected_executables"])
    cases, absence = [], []
    docker = shutil.which("docker")
    require(docker is not None, "absence_tool_missing")
    inspect_absence(docker, [timed_out["container_id"], timed_out["container_name"],
        cpu_stopped["container_id"], cpu_stopped["container_name"]], checkpoint,
        "failed_run_owned_container_present")
    current_references = []
    for number, case, mode, outcome in CASES:
        path = EVIDENCE + f"p09-148-authority-consumer-run{number:02}.v1.json"
        run = load(path)
        validate_case(run, build, manifest, case, mode, outcome)
        if number in (5, 6, 7):
            expected_driver = driver_row if number == 5 else stream_row
            require(next(r for r in run["source_freeze"] if r["path"] == DRIVER) == expected_driver,
                "historical_current_driver_binding_drift")
        driver_exact(run["source_freeze"])
        exact(run["protected_executables"])
        require(len(run["source_freeze"]) == (868 if number == 10 else 867)
            and len(run["protected_executables"]) == 57, "runtime_pin_inventory")
        for reference in (run["container_id"], run["container_name"]):
            current_references.append(reference)
        cases.append({"receipt": pin(path), "live_case": case, "input_mode": mode, "formula_outcome": outcome})
    absence = inspect_absence(docker, current_references, checkpoint, "owned_container_present")
    deferred_lint = load(BASE + "p148-workspace-lint-r2.json")
    require(deferred_lint["state"] == "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED"
        and deferred_lint["lint_started"] is False and deferred_lint["test_or_app_executed"] is False,
        "deferred_lint_status_changed")
    lint = load(BASE + "p148-workspace-lint-r3.json")
    key = lambda row: (row["package_id"], row["name"], tuple(sorted(row["kind"])))
    wanted, actual = {key(r) for r in lint["workspace_inventory"]}, {key(r) for r in lint["workspace_artifacts"]}
    require(lint["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and lint["exit_code"] == 0 and not lint["diagnostics"]
        and lint["source_freeze_exact_after"] and lint["protected_executables_exact_after"]
        and lint["workspace_target_coverage_exact"] and len(wanted) == len(actual) == 361 and wanted == actual
        and len({r["package_id"] for r in lint["workspace_inventory"]}) == 32
        and len(lint["source_freeze"]) == 867 and len(lint["protected_executables"]) == 57
        and not lint["missing_targets"] and not lint["unexpected_targets"]
        and lint["cargo_arguments"][-2:] == ["-D", "warnings"], "current_strict_lint_not_accepted")
    require(next(r for r in lint["source_freeze"] if r["path"] == DRIVER) == stream_row, "strict_lint_driver_epoch_drift")
    driver_exact(lint["source_freeze"])
    exact(lint["protected_executables"])
    indexed = run_audit_tool("rust-input-inventory", checkpoint=checkpoint)
    readonly_tool_profiles.append(indexed.audit_limits)
    require(indexed.returncode == 0 and not indexed.stderr and set(indexed.stdout.replace("\\", "/").splitlines()).issubset(
        {r["path"] for r in build["source_freeze"]}), "whole_Rust_input_coverage")
    from tests.test_authority_sql_consumer_boundary import AuthoritySQLConsumerBoundary
    from tests.test_authority_sql_current_audit import AuthorityCurrentAudit, OwnedAbsenceAudit, AuthorityTimeoutAudit
    from tests.test_live_sql_consumer_boundary import LiveSQLConsumerBoundary
    from tests.test_authority_admission_diagnostics import AuthorityAdmissionDiagnostics
    from tests.test_bounded_process_progress import BoundedProcessProgressTests
    from tests.test_bounded_container_absence import BoundedContainerAbsenceTests
    from tests.test_source_guard_fixture import SourceGuardFixtureTests
    from tests.test_negative_root_copy import NegativeRootCopyTests
    from tests.test_bounded_audit_tools import BoundedAuditToolsTests
    from tests.test_bounded_audit_tool_integration import BoundedAuditToolIntegrationTests
    for cls, count in ((AuthoritySQLConsumerBoundary, 8), (AuthorityCurrentAudit, 8),
                       (OwnedAbsenceAudit, 5), (AuthorityTimeoutAudit, 7),
                       (AuthorityAdmissionDiagnostics, 5), (BoundedProcessProgressTests, 8), (LiveSQLConsumerBoundary, 6),
                       (BoundedContainerAbsenceTests, 21), (SourceGuardFixtureTests, 10),
                       (NegativeRootCopyTests, 4), (BoundedAuditToolsTests, 20),
                       (BoundedAuditToolIntegrationTests, 8)):
        checked = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
        require(checked.testsRun == count and checked.wasSuccessful() and not checked.skipped, "guards_or_negative_tests_failed")
    for path in (SELF, REPORT, "tools/p09/tests/test_authority_sql_consumer_boundary.py",
                 "tools/p09/tests/test_authority_sql_current_audit.py", "tools/p09/verify_formula_issuer_live_current.py",
                 "tools/p09/tests/test_authority_admission_diagnostics.py", "tools/p09/bounded_process_progress.py",
                 "tools/p09/tests/test_bounded_process_progress.py", "tools/p09/audit_evidence_io.py",
                 "tools/p09/tests/test_audit_evidence_io.py", "tools/p09/bounded_container_absence.py",
                 "tools/p09/conservative_maintenance.py", "tools/p09/tests/test_bounded_container_absence.py",
                 "tools/p09/source_guard_fixture.py", "tools/p09/tests/test_source_guard_fixture.py",
                 "tools/p09/tests/test_live_sql_consumer_boundary.py",
                 "tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/tests/test_negative_root_copy.py",
                 "implementation/p09/source-archive/p09-149-pre-root-only-negative-copies/source-preimages.v1.json",
                 "tools/p09/bounded_audit_tools.py", "tools/p09/tests/test_bounded_audit_tools.py",
                 "tools/p09/verify_bounded_audit_tools_light.py", "tools/p09/verify_audit_evidence_io.py",
                 "tools/p09/tests/test_bounded_audit_tool_integration.py",
                 "tools/p09/verify_bounded_audit_tool_integration_light.py",
                 "implementation/p09/source-archive/p09-149-pre-bounded-audit-integration/source-preimages.v1.json"):
        pin(path)
    reader.finish()
    return {"schema_version": "hwpx-agent.p09-148-current-authority-sql-audit/v1",
        "state": "CURRENT_TRUST_POLICY_SQL33_AND_STRICT_LINT_COMPONENT_PASS_NOT_NATIVE_OR_GATE",
        "verified_direct_pins": list(snapshots.values()), "unique_files_freshly_double_hashed": len(snapshots),
        "evidence_read_profile": {"hash_chunk_bytes": 65536, "single_read_json_byte_binding": True,
            "parsed_inputs_cached": False, "read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
            "final_fresh_hashes": reader.final_fresh_hashes,
            "maximum_parse_bytes": reader.maximum_parse_bytes,
            "io_pacing_bytes_per_second": 8388608, "io_pacing_burst_bytes": 65536,
            "io_pacing_charged_bytes": reader.pacer.bytes_paced,
            "requested_pacing_sleep_seconds": reader.pacer.requested_sleep_seconds},
        "historical_P147_direct_pins_preserved": 1023, "historical_receipts_not_rerun_as_current": True,
        "original_approval_and_baseline_consumer_whole_delta_authenticated": True,
        "initial_failed_compile_and_source_preserved": True, "cross_turn_hash_cache_used": False,
        "current_cases": cases, "current_owned_container_absence": absence,
        "absence_query_profile": {"docker_inspect_batches": 2, "failed_references": 4,
            "current_references": 8, "timeout_seconds_per_batch": 10,
            "output_limit_bytes_per_stream": 32768, "owned_job_before_docker": True,
            "generic_object_presence_rejected": True},
        "protected_executables": lint["protected_executables"], "actual_Rust_unit_tests": 11,
        "source_guards": 8, "previous_approval_source_guards": 6, "evidence_negative_checks": 25,
        "bounded_live_pipe_checks": 8, "streaming_driver_closed_delta_authenticated": True,
        "bounded_absence_fixture_checks": 19,
        "source_guard_fixture_profile": {"class_local_source_text": True,
            "fresh_final_hash_per_class": True, "fixture_boundary_checks": 10,
            "no_cross_run_cache": True},
        "negative_root_copy_boundary_checks": 4,
        "readonly_tool_profiles": readonly_tool_profiles,
        "bounded_readonly_tool_checks": 20, "bounded_readonly_integration_checks": 8,
        "timed_out_run08_preserved_as_failed_not_current_success": True,
        "CPU_stopped_run09_preserved_as_failed_not_current_success": True,
        "failed_run08_post_hash_checks_not_reached": True,
        "historical_owned_absence_checks": 10,
        "packages": 32, "targets": 361,
        "original_source_indices_currently_covered": [0], "RAM_derivative_indices_currently_covered": [0],
        "trust_and_policy_revocation_component_executed": True,
        "issuer_provisioning_generation_race_qualified": False, "all_36_original_sources_qualified": False,
        "native_application_executed": False, "durable_blob_store_qualified": False,
        "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "observed_graph_native_fidelity_qualified": False, "P09_gate": "OPEN", "A12_gate": "OPEN",
        "A13_gate": "OPEN", "product_complete": False, "goal_status": "active"}


if __name__ == "__main__":
    resources = None
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--receipt", required=True)
        args = parser.parse_args()
        require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
        require(re.fullmatch(r"implementation/p09/evidence/p09-148-current-authority\.progress\.v[1-9][0-9]*\.json", args.receipt), "receipt_scope")
        destination = ROOT / args.receipt
        require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
            and not destination.parent.is_junction(), "fresh_progress_required")
        resources = IdleResources()
        observed_limits(resources)
        resources.start()
        result = audit(resources)
        result["resource_samples"], result["resource_stop_reason"] = resources.samples, resources.reason
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"state": result["state"], "receipt": args.receipt,
                         "unique_files_freshly_double_hashed": result["unique_files_freshly_double_hashed"]}))
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        failure = {"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}
        tool_profile = getattr(error, "audit_limits", None)
        if tool_profile is not None:
            failure["readonly_tool_failure_profile"] = tool_profile
        print(json.dumps(failure))
        raise SystemExit(1) from None
    finally:
        if resources is not None:
            resources.done.set()
            if resources.thread.is_alive():
                resources.thread.join(timeout=3)
