"""P148 actual SQL trust/policy revocation through the original mandatory consumer."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import time
import uuid

from run_formula_issuer_registry_sql_checks import ROOT, IMAGE, Resources, pin, require
from sql_percentage_resources import admit, resource_policy
from sql_runtime_supervision import SQLRuntimeResources as IdleResources, finish_watcher, LocalDockerJobFactory as OwnedSQLJobFactory
from run_resource_bounded_python import observed_limits
from bounded_process_progress import BoundedProcessCapture, bounded_observation_run, LIMIT, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobFailure, record_owned_jobs
from live_sql_evidence_reader import LiveSQLReader
from issuer_sql_build_contract import bind_probe_build, consumer_sources

LABEL = "hwpx-agent.p09-148-owned-authority-product-test"
ROLES = ["p141_reader", "p141_root", "p141_approval", "p141_bad_direct", "p141_bad_helper", "p142_artifact", "p143_worker"]
ROOT_CHECKS = [
    "original_artifact_schema22_admission", "registry_exact_admissions",
    "original_root_workflow_AEAD_SQL_commit_readback", "root_named_metadata_exact",
    "real_plaintext_digest_exact", "real_ciphertext_hash_exact", "ciphertext_not_plaintext",
    "generated_public_key_roundtrip", "real_DB_audit_ingested",
    "actual_locked_source_and_observed_IR_AEAD", "original_leased_revision_seal_and_IR_link",
    "actual_source_formula_targets_not_caller_AST", "original_generated_policy_SQL_CAS_and_readback",
    "original_signature_approval_SQL_commit_readback",
    "original_consumer_candidate_equals_independent_evaluator", "fresh_consumer_exact_without_cached_trust",
    "full_product_route_not_falsely_enabled", "consumer_preserves_head_and_artifact_ingest_count",
]
ROOT_CHECKS += [
    "live_authority_exact_current_binding",
    "live_authority_stale_CAS_preserves_binding",
    "live_authority_consumer_survives_rejected_CAS",
    "live_authority_revoke_commit_ack_exact",
    "live_authority_duplicate_revoke_denied",
    "live_authority_named_read_denied",
    "live_authority_prepared_verify_denied",
    "live_authority_prepared_callback_denied_zero",
    "live_authority_fresh_prepare_denied",
    "live_authority_route_denied_not_merely_unqualified",
    "live_authority_cached_policy_state_exact",
    "live_authority_original_source_bytes_preserved",
    "live_authority_revision_head_preserved",
    "live_authority_artifact_ingest_count_preserved",
    "live_authority_unrelated_authority_preserved"
]
CHECKS = [
    "reader_exact_admission", "root_exact_admission", "approval_exact_admission",
    "root_credentials_cannot_admit_reader", "approval_credentials_cannot_admit_reader",
    "unsafe_direct_table_grant_denied", "unsafe_helper_execute_grant_denied",
    "reader_credentials_cannot_admit_writer", "root_credentials_cannot_admit_approval_writer",
    "typed_root_read", "typed_root_exact_identity", "typed_approval_read", "typed_approval_exact_identity",
    "fixed_subject_context_denied", "fixed_tenant_context_denied", "nonmember_transport_admitted",
    "nonmember_named_read_denied", "owner_root_preflight", "editor_approval_preflight",
    "management_foreign_context_denied", "management_wrong_capability_denied",
    "root_wrong_artifact_digest_denied", "root_generation_three_commit", "root_commit_ack_exact",
    "root_same_cas_no_retry", "root_fresh_named_readback", "root_readback_all_fields_exact",
    "root_rotation_denies_old_approval", "approval_stale_root_denied",
    "editor_approval_generation_three_commit", "approval_commit_ack_exact", "approval_same_cas_no_retry",
    "approval_fresh_named_readback", "approval_readback_all_fields_exact", "root_revoke_commit",
    "root_revoke_ack_exact", "revoked_root_named_read_denied", "revoked_root_approval_read_denied",
    "root_duplicate_revoke_no_retry", "approval_admin_revoke_after_root_revoked",
    "approval_revoke_ack_exact", "approval_duplicate_revoke_no_retry",
]


class AdmissionRefusal(ValueError):
    """Only bounded aggregate observations; no arguments, credentials or source text."""
    def __init__(self, error, resources):
        code = str(error)
        allowed_codes = {"bootstrap_idle_window_not_admitted", "bootstrap_resource_stop",
            "STOP_LOW_AVAILABLE_RAM", "STOP_SUSTAINED_SYSTEM_CPU", "STOP_RESOURCE_OBSERVATION_FAILED",
            "STOP_SYSTEM_COMMIT_PRESSURE", "STOP_RESOURCE_OBSERVATION_INVALID",
            "DEFERRED_ALREADY_SATURATED_SYSTEM", "STOP_RESOURCE_SAMPLE_BUDGET",
            "RAM_SAMPLE_FAILED", "RAM_SAMPLE_INVALID", "CPU_SAMPLE_FAILED", "CPU_SAMPLE_INTERVAL_MISSING",
            "ram_sample_failed", "cpu_sample_failed", "cpu_sample_interval_missing"}
        code = code if code in allowed_codes else "redacted"
        super().__init__(code)
        rows = resources.samples
        self.diagnostics = {
            "stage": "pre_hash_idle_admission", "samples": len(rows),
            "system_CPU_max_percent": max((r["system_cpu_percent"] for r in rows), default=None),
            "available_RAM_min_mib": min((r["available_ram_mib"] for r in rows), default=None),
            "required_available_RAM_min_percent": resource_policy()["start_available_ram_min_percent"],
            "maximum_commit_used_percent": resource_policy()["maximum_commit_used_percent"],
            "already_saturated_CPU_percent": resource_policy()["already_saturated_cpu_percent"],
            "required_consecutive_samples": resource_policy()["start_consecutive_samples"],
            "maximum_admission_seconds": resource_policy()["maximum_admission_seconds"],
            "heavy_work_started": False,
        }


def admit_or_explain(resources):
    try:
        return admit(resources)
    except (OSError, ValueError) as error:
        raise AdmissionRefusal(error, resources) from None


def main(build_path, receipt_path, source_index, input_mode, expected_outcome, live_case):
    resources = IdleResources()
    pre_hash_limits = observed_limits(resources)
    pre_hash_stable_samples = admit_or_explain(resources)
    reader = LiveSQLReader(resources)
    pin = reader.pin
    require(live_case in {"trust", "policy"}, "live_case_not_allowlisted")
    require(Path.cwd().resolve() == ROOT.resolve(), "adapter_wrong_root")
    destination = (ROOT / receipt_path).resolve()
    require(destination.is_relative_to(ROOT / "implementation/p09/evidence")
        and re.fullmatch(r"p09-148-authority-consumer-run[0-9]{2}\.v1\.json", destination.name)
        and not destination.exists(), "fresh_adapter_receipt_required")
    require(type(source_index) is int and 0 <= source_index < 36 and input_mode in {"original", "numeric_derivative"}
        and expected_outcome in {"changed", "unchanged"}, "corpus_selection_invalid")
    manifest_path = "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json"
    require(pin(manifest_path)["sha256"] == "36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d",
        "locked_original_manifest_drift")
    manifest = reader.json(ROOT/manifest_path)
    require(len(manifest["actual_inputs"]) == 36, "locked_original_coverage_drift")
    original_source_pin = manifest["actual_inputs"][source_index]
    require((ROOT/original_source_pin["path"]).resolve().is_relative_to(ROOT.resolve())
        and pin(original_source_pin["path"]) == original_source_pin, "locked_original_source_drift")
    build_file = (ROOT / build_path).resolve()
    build, crypto_executable, build_binding = bind_probe_build(reader, build_file)
    require(build["whole_workspace_Rust_input_coverage_enforced"] and build["historical_parent_archive_verified"]
        and len(build["source_freeze"]) == 842 and len(build["protected_executables"]) >= 37,
        "new_build_coverage_missing")
    historical_build_path = "target/p09-121-resource-optimized/p141-adapter-build-r5.json"
    historical_build = reader.json(ROOT/historical_build_path)
    executable = historical_build["executable_pin"]
    require(historical_build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE"
        and executable in build["protected_executables"] and pin(executable["path"]) == executable,
        "original_metadata_probe_not_protected")
    protected = list(build["protected_executables"]) + [crypto_executable]
    unit_receipt_paths = [f"target/p09-121-resource-optimized/p143-typed-route-unit-build-r{n}.json" for n in (1, 2, 3, 4, 5, 6, 7)]
    for unit_path in unit_receipt_paths:
        unit = reader.json(ROOT/unit_path)
        require(unit["state"] == "PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION"
            and unit["catalog_profile"]["test"] and unit["exit_code"] == 0, "unit_build_missing")
        protected.append(unit["executable_pin"])
    expected_protected_count = len(build["protected_executables"]) + 1 + len(unit_receipt_paths)
    require(len(protected) == len({row["path"] for row in protected}) == expected_protected_count
        and all(pin(row["path"]) == row for row in protected), "complete_executable_protection_missing")
    additions = [
        "tools/p09/run_formula_issuer_product_probe.py", "tools/p09/run_formula_issuer_corpus_probe.py",
        "tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_resource_bounded_python.py",
        "tools/p09/run_formula_issuer_authority_sql_probe.py",
        "tools/p09/bounded_process_progress.py",
        "tools/p09/sql_percentage_resources.py", "tools/p09/conservative_maintenance.py",
        "tools/p09/owned_sql_job.py", "tools/p09/live_sql_evidence_reader.py",
        "tools/p09/audit_evidence_io.py",
        "implementation/p09/source-archive/p09-148-pre-live-authority/source-preimages.v1.json",
        "implementation/p09/source-archive/p09-148-pre-strict-lint-correction/source-preimages.v1.json",
        original_source_pin["path"], *unit_receipt_paths, "tools/p09/fixtures/formula_registry_crypto.sql",
        "tools/p09/fixtures/formula_issuer_product.sql", "tools/p09/run_postgres_revision_graph_checks.py",
        "tools/p09/idle_resource_admission.py", "tools/p09/check_idle_resource_window.py",
        "tools/p09/run_formula_issuer_registry_adapter.py", "tools/p09/fixtures/formula_issuer_registry_adapter.sql",
        "tools/p09/run_formula_issuer_registry_sql_checks.py", "tools/p09/fixtures/formula_issuer_registry.sql",
        "tools/p09/fixtures/authorized_full_ir_intent.sql", build_file.relative_to(ROOT).as_posix(),
        *consumer_sources(build_binding),
        "tools/p09/sql_runtime_supervision.py",
    ]
    sources = [p["path"] for p in build["source_freeze"]]
    sources += list(dict.fromkeys(path for path in additions if path not in sources))
    require(len(sources) == len(set(sources)) and set(additions).issubset(sources),
        "crypto_source_coverage_drift")
    require(all(pin(p["path"]) == p for p in build["source_freeze"]), "compiled_crypto_source_drift")
    freeze = [pin(p) for p in sources]
    migrations = sorted(p for p in sources if re.fullmatch(r"migrations/postgres/\d{4}_.+\.up\.sql", p))
    require(len(migrations) == 22, "adapter_migration_coverage_drift")
    docker = shutil.which("docker")
    require(docker is not None, "docker_not_available")
    start = time.monotonic()
    run_id = str(uuid.uuid4())
    name = "hwpx-p148-" + run_id
    created_id, requested, stage = None, False, "resource_preflight"
    port, last_child = None, None
    password = secrets.token_hex(32)
    receipt = {
        "schema_version": "hwpx-agent.p09-148-live-authority-consumer-sql22/v1", "state": "NOT_RUN",
        "live_case": live_case, "pre_hash_limits": pre_hash_limits, "pre_hash_stable_samples": pre_hash_stable_samples,
        "trust_revocation_consumer_component_executed": False,
        "policy_revocation_consumer_component_executed": False,
        "issuer_provisioning_generation_race_qualified": False, "trust_revocation_consumer_qualified": False,
        "run_id": run_id, "container_name": name, "container_id": None, "image": IMAGE,
        "source_freeze": freeze, "executable_pin": executable, "product_executable_pin": crypto_executable, "protected_executables": protected,
        "source_freeze_exact_after": False, "protected_executables_exact_after": False,
        "compiled_build_binding": build_binding,
        "migrations_applied": [], "probe_runs": [], "container_removed": False,
        "actual_SQL_executed": False, "actual_Rust_DB_adapter_executed": False,
        "real_AEAD_executed": False, "Ed25519_public_key_generated": False,
        "real_Ed25519_approval_signature_executed": False, "original_product_consumer_executed": False,
        "durable_blob_store_qualified": False, "native_application_executed": False,
        "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "synthetic_scanner_and_baseline_receipt": True, "observed_graph_native_fidelity_qualified": False,
        "source_inputs_covered": 1, "all_36_source_inputs_qualified": False,
        "source_index": source_index, "input_mode": input_mode, "expected_formula_outcome": expected_outcome,
        "frozen_original_source_pin": original_source_pin,
        "numeric_derivative_is_test_only_RAM": input_mode == "numeric_derivative",
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "resource_policy": resource_policy(),
    }

    def command(args, text=None, timeout=20, cleanup=False, env=None, rust=False):
        nonlocal last_child
        if not cleanup:
            require(not resources.stop.is_set(), resources.reason or "resource_stop")
            require(time.monotonic() - start < 240, "adapter_total_time_limit")
        def checkpoint():
            if not cleanup:
                require(not resources.stop.is_set(), resources.reason or "resource_stop")
                require(time.monotonic() - start < 240, "adapter_total_time_limit")
                resources.checkpoint_io()
        factory = OwnedSQLJobFactory(windows=resources.windows,
            allowed_executables=[docker, str(ROOT / executable["path"]), str(ROOT / crypto_executable["path"])],
            checkpoint=checkpoint, record=lambda profiles: record_owned_jobs(receipt, profiles))
        process = factory(args, cwd=ROOT, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        deadline = time.monotonic() + timeout
        next_observation = time.monotonic() + 10
        capture = None
        try:
            affinity, system = ctypes.c_size_t(), ctypes.c_size_t()
            resources.k.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
            require(resources.k.GetProcessAffinityMask(int(process._handle), ctypes.byref(affinity), ctypes.byref(system))
                and affinity.value == 1, "owned_child_affinity_not_inherited")
            if rust:
                resources.k.GetPriorityClass.argtypes = [ctypes.c_void_p]
                require(resources.k.GetPriorityClass(int(process._handle)) == 0x4000, "rust_priority_not_applied")
            marker_mode = rust and args[0] == str(ROOT / crypto_executable["path"])
            if marker_mode:
                require(text is None, "live_progress_stdin_not_supported")
            capture = BoundedProcessCapture(process, input_text=text,
                output_limit=LIMIT if marker_mode else MAX_OUTPUT, parse_markers=marker_mode)
            while True:
                try:
                    output, errors = capture.communicate(timeout=0.25)
                    process.observe()
                    if not marker_mode:
                        output = output.replace("\r\n", "\n").replace("\r", "\n")
                        errors = errors.replace("\r\n", "\n").replace("\r", "\n")
                    if not cleanup:
                        require(not resources.stop.is_set(), resources.reason or "resource_stop")
                    require(time.monotonic() < deadline, "owned_command_timeout")
                    break
                except subprocess.TimeoutExpired:
                    process.observe()
                    markers, observations = capture.progress()
                    if marker_mode:
                        receipt["live_progress_markers"] = markers
                        receipt["live_progress_observations"] = observations
                        if time.monotonic() >= next_observation and time.monotonic() + 3 < deadline:
                            next_observation = time.monotonic() + 10
                            # 자기 UUID/label로 admission한 DB의 read-only 대기 metadata만 수집한다.
                            activity_sql = "SELECT coalesce(json_agg(json_build_object('app',application_name,'state',state,'wait_type',wait_event_type,'wait',wait_event,'blocked_count',cardinality(pg_blocking_pids(pid)))),'[]'::json) FROM pg_stat_activity WHERE datname='postgres' AND backend_type='client backend' AND application_name LIKE 'hwpx-agent-%';"
                            try:
                                observed = bounded_observation_run([docker, "exec", created_id, "psql", "-X", "-U", "postgres",
                                    "-d", "postgres", "-At", "-c", activity_sql], cwd=ROOT, timeout=3,
                                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS,
                                    process_factory=factory)
                                require(observed.returncode == 0 and len(observed.stdout) <= 16384, "live_wait_observation_failed")
                                rows = json.loads(observed.stdout)
                                require(isinstance(rows, list) and len(rows) <= 32, "live_wait_inventory_scope")
                                require(all(set(row) == {"app", "state", "wait_type", "wait", "blocked_count"} for row in rows), "live_wait_field_scope")
                                receipt.setdefault("live_wait_observations", []).append({"elapsed_seconds": round(time.monotonic()-start, 2), "rows": rows})
                            except OwnedSQLJobFailure:
                                raise
                            except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
                                receipt.setdefault("live_wait_observations", []).append({"observation": "unavailable_no_raw_log"})
                    if not cleanup:
                        require(not resources.stop.is_set(), resources.reason or "resource_stop")
                    require(time.monotonic() < deadline, "owned_command_timeout")
        finally:
            try:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=2)
            finally:
                try:
                    if capture is not None:
                        capture.close()
                        if marker_mode and not capture.error:
                            markers, observations = capture.progress()
                            receipt["live_progress_markers"] = markers
                            receipt["live_progress_observations"] = observations
                    else:
                        for stream in (process.stdin, process.stdout, process.stderr):
                            stream.close()
                finally:
                    factory.close()
        last_child = subprocess.CompletedProcess(args, process.returncode, output, errors)
        return last_child

    def sql(text, database="postgres"):
        require(database in {"postgres", "p141_changed_schema", "p141_correct_schema"}, "owned_database_name_invalid")
        child = command([docker, "exec", "-i", name, "psql", "-X", "--quiet", "--no-align", "--tuples-only",
            "--set", "ON_ERROR_STOP=1", "--set", "VERBOSITY=verbose", "--username", "postgres", "--dbname", database], text)
        require(child.returncode == 0, "owned_sql_execution_failed")
        return child.stdout.strip()

    def inspect(cleanup=False):
        child = command([docker, "inspect", name], cleanup=cleanup)
        require(child.returncode == 0, "owned_container_missing")
        rows = json.loads(child.stdout)
        require(len(rows) == 1, "owned_container_ambiguous")
        item, host = rows[0], rows[0]["HostConfig"]
        require(item["Id"] == created_id and item["Name"] == "/" + name
            and item["Config"]["Labels"].get(LABEL) == run_id and item["Config"]["Image"] == IMAGE
            and item["Image"] == receipt["image_id"], "owned_container_identity_mismatch")
        bindings = host["PortBindings"]
        require(host["NetworkMode"] == "bridge" and set(bindings) == {"5432/tcp"}
            and len(bindings["5432/tcp"]) == 1 and bindings["5432/tcp"][0]["HostIp"] == "127.0.0.1"
            and not item["Mounts"] and host["ReadonlyRootfs"] is True and host["NanoCpus"] == 1000000000
            and host["Memory"] == host["MemorySwap"] == 536870912 and host["PidsLimit"] == 64
            and set(host["Tmpfs"]) == {"/var/lib/postgresql", "/tmp", "/var/run/postgresql"}, "owned_container_isolation_mismatch")
        return item

    def probe(mode, expected, database="postgres"):
        require(pin(executable["path"]) == executable, "probe_executable_drift")
        child = command([str(ROOT / executable["path"]), mode], timeout=60, rust=True,
            env=dict(os.environ, P141_DB_PORT=str(port), P141_DB_PASSWORD=password, P141_DB_DATABASE=database))
        require(child.stdout.lstrip().startswith("{"), "probe_not_JSON_protocol")
        doc = json.loads(child.stdout)
        require(doc["mode"] == mode and doc["real_crypto_executed"] is False and doc["P09_gate"] == "OPEN"
            and doc["product_complete"] is False and len(set(doc["checks"])) == len(doc["checks"]), "probe_protocol_drift")
        receipt["probe_runs"].append({"database": database, "exit_code": child.returncode, "result": doc})
        receipt["actual_Rust_DB_adapter_executed"] = True
        require(child.returncode == 0 and doc["state"] == "PASS_RUST_SQL22_METADATA_NOT_CRYPTO_NATIVE_OR_GATE"
            and doc["checks"] == expected and doc["failed_stage"] is None and doc["error_code"] is None, "rust_adapter_probe_failed")

    try:
        resources.start()
        stage = "cached_image_identity"
        image = command([docker, "image", "inspect", IMAGE])
        require(image.returncode == 0, "pinned_local_image_missing")
        image_rows = json.loads(image.stdout)
        require(len(image_rows) == 1 and image_rows[0]["Id"] == "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568",
            "cached_image_identity_drift")
        receipt["image_id"] = image_rows[0]["Id"]
        stage, requested = "owned_container_create", True
        child = command([docker, "run", "--detach", "--pull", "never", "--name", name, "--label", LABEL + "=" + run_id,
            "--network", "bridge", "--publish", "127.0.0.1::5432", "--read-only", "--memory", "512m", "--memory-swap", "512m",
            "--cpus", "1", "--pids-limit", "64", "--tmpfs", "/var/lib/postgresql:rw,noexec,nosuid,size=512m",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "--tmpfs", "/var/run/postgresql:rw,noexec,nosuid,size=16m",
            "--env", "POSTGRES_PASSWORD", IMAGE], env=dict(os.environ, POSTGRES_PASSWORD=secrets.token_hex(32)))
        require(child.returncode == 0 and re.fullmatch(r"[a-f0-9]{64}", child.stdout.strip()), "owned_container_creation_failed")
        created_id = child.stdout.strip()
        receipt["container_id"] = created_id
        item = inspect()
        published = item["NetworkSettings"]["Ports"]["5432/tcp"]
        require(len(published) == 1 and published[0]["HostIp"] == "127.0.0.1", "host_loopback_binding_inexact")
        port = int(published[0]["HostPort"])
        require(0 < port <= 65535, "host_port_invalid")
        receipt["loopback_port"] = port
        stage, ready = "final_tcp_ready", False
        for _ in range(30):
            if command([docker, "exec", name, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "postgres"], timeout=5).returncode == 0:
                ready = True
                break
            time.sleep(0.5)
        require(ready, "owned_database_not_ready")
        receipt["server_version_num"] = int(sql("SHOW server_version_num;"))
        require(receipt["server_version_num"] == 180004, "database_version_drift")
        for path in migrations:
            stage = "migration_" + Path(path).name[:4]
            row = next(p for p in freeze if p["path"] == path)
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + row["sha256"] + "',false);\n" + reader.text(ROOT / path))
            receipt["migrations_applied"].append(row)
            receipt["actual_SQL_executed"] = True
        stage = "original_full_ir_fixture"
        require("P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25" in sql(reader.text(ROOT / "tools/p09/fixtures/authorized_full_ir_intent.sql")),
            "original_full_ir_fixture_failed")
        receipt["original_full_ir_assertions"] = 25
        stage = "original_P140_SQL22_fixture"
        output = sql(reader.text(ROOT / "tools/p09/fixtures/formula_issuer_registry.sql"))
        checks = re.findall(r"^P140_SQL_CHECK:([a-z0-9_]+)$", output, re.MULTILINE)
        require(len(checks) == len(set(checks)) == 37, "original_SQL22_fixture_coverage_drift")
        receipt["original_SQL22_checks_committed"] = checks
        stage = "new_credential_profiles"
        sql(reader.text(ROOT / "tools/p09/fixtures/formula_issuer_registry_adapter.sql"))
        sql(reader.text(ROOT / "tools/p09/fixtures/formula_registry_crypto.sql"))
        sql(reader.text(ROOT / "tools/p09/fixtures/formula_issuer_product.sql"))
        # Generated hex only, stdin only. Never print, persist or put passwords in command arguments.
        sql("\n".join("ALTER ROLE " + role + " PASSWORD '" + password + "';" for role in ROLES))
        stage = "Rust_credential_bound_metadata_probe"
        probe("metadata", CHECKS)
        stage = "original_source_policy_signature_consumer_SQL_workflow"
        require(pin(crypto_executable["path"]) == crypto_executable, "crypto_executable_drift")
        child = command([str(ROOT/crypto_executable["path"])], timeout=60, rust=True,
            env=dict(os.environ, P143_DB_PORT=str(port), P143_DB_PASSWORD=password,
                P143_SOURCE_INDEX=str(source_index), P144_INPUT_MODE=input_mode, P148_LIVE_CASE=live_case))
        require(child.stdout.lstrip().startswith("{"), "crypto_probe_not_JSON_protocol")
        result = json.loads(child.stdout)
        allowed = {"state", "checks", "failed_stage", "formula_outcome", "real_approval_signature_and_original_consumer_executed",
            "durable_blob_store_qualified", "production_key_custody_qualified", "P09_gate", "product_complete",
            "source_index", "source_sha256", "original_source_sha256", "input_mode", "only_one_numeric_leaf_changed"}
        require(set(result) == allowed and result["P09_gate"] == "OPEN" and result["product_complete"] is False
            and isinstance(result["real_approval_signature_and_original_consumer_executed"], bool)
            and result["durable_blob_store_qualified"] is False and result["production_key_custody_qualified"] is False
            and len(set(result["checks"])) == len(result["checks"])
            and all(check in ROOT_CHECKS for check in result["checks"]), "crypto_probe_closed_protocol_drift")
        receipt["product_probe"] = {"exit_code": child.returncode, "result": result}
        require(result["source_index"] == source_index and result["input_mode"] == input_mode
            and result["original_source_sha256"] == original_source_pin["sha256"]
            and re.fullmatch(r"[0-9a-f]{64}", result["source_sha256"] or "")
            and result["formula_outcome"] == expected_outcome, "actual_corpus_identity_or_outcome_drift")
        require((input_mode == "original" and result["source_sha256"] == original_source_pin["sha256"]
                and result["only_one_numeric_leaf_changed"] is False)
            or (input_mode == "numeric_derivative" and result["source_sha256"] != original_source_pin["sha256"]
                and result["only_one_numeric_leaf_changed"] is True), "original_or_numeric_derivative_boundary_drift")
        require(child.returncode == 0
            and result["state"] == "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
            and result["checks"] == ROOT_CHECKS and result["failed_stage"] is None
            and result["real_approval_signature_and_original_consumer_executed"] is True,
            "original_root_crypto_workflow_failed")
        receipt["trust_revocation_consumer_component_executed"] = live_case == "trust"
        receipt["policy_revocation_consumer_component_executed"] = live_case == "policy"
        receipt["real_AEAD_executed"] = receipt["Ed25519_public_key_generated"] = True
        receipt["real_Ed25519_approval_signature_executed"] = receipt["original_product_consumer_executed"] = True
        stage = "owned_schema_control_base_migrations"
        sql("CREATE DATABASE p141_changed_schema;")
        controls = []
        for path in migrations[:-1]:
            fingerprint = next(p["sha256"] for p in freeze if p["path"] == path)
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + fingerprint + "',false);\n" + reader.text(ROOT / path), "p141_changed_schema")
            controls.append({"path": path, "migration_sha256_setting": fingerprint})
        # Clone the schema21 base before applying SQL22: no UPDATE/DELETE/trigger bypass/constraint weakening.
        sql("CREATE DATABASE p141_correct_schema TEMPLATE p141_changed_schema;")
        path = migrations[-1]
        fingerprint = next(p["sha256"] for p in freeze if p["path"] == path)
        fixture = reader.text(ROOT / "tools/p09/fixtures/formula_issuer_registry_adapter.sql")
        require(fixture.count("GRANT USAGE ON SCHEMA hwpx_agent TO") == 1, "profile_grant_section_ambiguous")
        # Roles are cluster-wide and already exist. Reuse the exact same grant statements in both empty controls.
        grants = "BEGIN; GRANT USAGE ON SCHEMA hwpx_agent TO" + fixture.split("GRANT USAGE ON SCHEMA hwpx_agent TO", 1)[1]
        for database, installed in [("p141_changed_schema", "0"*64), ("p141_correct_schema", fingerprint)]:
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + installed + "',false);\n" + reader.text(ROOT / path), database)
            sql(grants, database)
            observed = sql("SELECT migration_sha256::text FROM hwpx_agent.schema_versions WHERE version=22;", database)
            require(observed == installed, "schema_control_installed_fingerprint_inexact")
        receipt["schema_controls"] = {"base_migrations": controls, "SQL22_source_pin": pin(path),
            "wrong_fingerprint": "0"*64, "correct_fingerprint": fingerprint,
            "same_original_migration_and_grants": True, "schema_identity_or_triggers_mutated": False}
        stage = "owned_schema22_fingerprint_negative"
        probe("changed_schema_denied", ["changed_schema22_fingerprint_denied"], "p141_changed_schema")
        probe("correct_schema_admitted", ["correct_schema22_fingerprint_control_admitted"], "p141_correct_schema")
        stage = "observer_final_history_and_revocations"
        history = json.loads(sql("BEGIN; SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true); "
            "SELECT json_build_object('root_history',(SELECT count(*) FROM hwpx_agent.formula_issuer_trust_versions),"
            "'root_max',(SELECT max(generation) FROM hwpx_agent.formula_issuer_trust_versions),"
            "'approval_history',(SELECT count(*) FROM hwpx_agent.formula_approval_versions),"
            "'approval_max',(SELECT max(generation) FROM hwpx_agent.formula_approval_versions),"
            "'root_revocations',(SELECT count(*) FROM hwpx_agent.formula_issuer_trust_revocations),"
            "'approval_revocations',(SELECT count(*) FROM hwpx_agent.formula_approval_revocations),"
            "'current_source_policy_revocations',(SELECT count(*) FROM hwpx_agent.source_formula_policy_revocations r "
            "JOIN hwpx_agent.source_formula_policy_versions v ON v.tenant_id=r.tenant_id AND v.project_id=r.project_id "
            "AND v.policy_version_id=r.policy_version_id WHERE v.document_id='p143-source-document')); COMMIT;").splitlines()[-1])
        require(history == {"root_history": 4, "root_max": 4, "approval_history": 4, "approval_max": 3,
            "root_revocations": 3 if live_case == "trust" else 2, "approval_revocations": 2,
            "current_source_policy_revocations": 1 if live_case == "policy" else 0}, "final_history_inexact")
        receipt["final_history"] = history
        require([pin(p) for p in sources] == freeze and pin(executable["path"]) == executable
            and pin(crypto_executable["path"]) == crypto_executable, "adapter_input_freeze_drift")
        require(all(pin(p["path"]) == p for p in protected), "protected_executable_drift")
        reader.finish()
        receipt["bounded_input_IO"] = reader.summary()
        receipt["source_freeze_exact_after"] = receipt["protected_executables_exact_after"] = True
        inspect()
        receipt["state"] = "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        receipt["state"], receipt["failed_stage"] = "FAIL_CLOSED", stage
        receipt["error_code"] = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        if last_child is not None:
            receipt["last_command_exit_code"] = last_child.returncode
            state = re.search(r"ERROR:\s+([A-Z0-9]{5}):", last_child.stderr)
            rust_state = re.search(r"^P143_DB_SQLSTATE code=([A-Z0-9_]{5,16})$", last_child.stderr, re.MULTILINE)
            receipt["sqlstate"] = state.group(1) if state else (rust_state.group(1) if rust_state else None)
            receipt["worker_stage_codes"] = re.findall(r"^P143_WORKER_STAGE code=(RECEIVE_LEASE|ADVANCE)$", last_child.stderr, re.MULTILINE)
            receipt["consumer_error_codes"] = re.findall(r"^P143_CONSUMER_ERROR code=(ISSUER|ISSUER_DRIFT|KIND|PRODUCT_DRIFT|POLICY|REQUEST|PROVIDER|SOURCE|COMPILER|ORIGINAL_PRODUCT)$", last_child.stderr, re.MULTILINE)
            constraint = re.search(r"CONSTRAINT NAME:\s+([a-z][a-z0-9_]{0,127})", last_child.stderr)
            receipt["sql_constraint_name"] = constraint.group(1) if constraint else None
    finally:
        finish_watcher(resources, receipt)
        if requested and created_id is None:
            try:
                child = command([docker, "inspect", name], cleanup=True)
                if child.returncode == 0:
                    rows = json.loads(child.stdout)
                    require(len(rows) == 1 and rows[0]["Name"] == "/" + name
                        and rows[0]["Config"]["Labels"].get(LABEL) == run_id and rows[0]["Config"]["Image"] == IMAGE
                        and rows[0]["Image"] == receipt["image_id"], "unknown_creation_identity_mismatch")
                    created_id = rows[0]["Id"]
                    receipt["container_id"] = created_id
                else:
                    require(re.search(r"no such (object|container)", child.stderr, re.IGNORECASE), "unknown_creation_outcome")
                    receipt["container_removed"] = True
            except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError):
                receipt["state"], receipt["cleanup_error_code"] = "FAIL_CLOSED", "unknown_creation_preserved_for_review"
        if created_id is not None:
            try:
                inspect(cleanup=True)
                removed = command([docker, "rm", "--force", created_id], cleanup=True)
                require(removed.returncode == 0, "owned_container_removal_failed")
                remaining = command([docker, "inspect", created_id], cleanup=True)
                receipt["container_removed"] = remaining.returncode != 0 and re.search(
                    r"no such (object|container)", remaining.stderr, re.IGNORECASE) is not None
                require(receipt["container_removed"], "owned_container_removal_unverified")
            except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError):
                receipt["state"], receipt["cleanup_error_code"] = "FAIL_CLOSED", "owned_container_cleanup_unverified"
        receipt["elapsed_seconds"] = round(time.monotonic() - start, 2)
        receipt["resource_samples"], receipt["resource_stop_reason"] = resources.samples, resources.reason
        if resources.reason:
            receipt["state"] = "FAIL_CLOSED"
        # Runtime evidence output only; exclusive create never overwrites a historical receipt.
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({"state": receipt["state"], "stage": stage, "container_removed": receipt["container_removed"],
            "receipt": receipt_path, "elapsed_seconds": receipt["elapsed_seconds"]}))
    return 0 if receipt["state"].startswith("PASS_") and receipt["container_removed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-receipt", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--source-index", type=int, choices=range(36), required=True)
    parser.add_argument("--input-mode", choices=["original", "numeric_derivative"], required=True)
    parser.add_argument("--expected-outcome", choices=["changed", "unchanged"], required=True)
    parser.add_argument("--live-case", choices=["trust", "policy"], required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(main(args.build_receipt, args.receipt, args.source_index, args.input_mode, args.expected_outcome, args.live_case))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        report = {"state": "FAIL_CLOSED_BEFORE_OWNED_CONTAINER", "error_code": code, "P09_gate": "OPEN"}
        if isinstance(error, AdmissionRefusal):
            report["admission_diagnostics"] = error.diagnostics
        print(json.dumps(report))
        raise SystemExit(1) from None
