"""P142 owned loopback-only original root AEAD + SQL22 workflow; not approval/consumer/native."""
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

LABEL = "hwpx-agent.p09-142-owned-root-crypto-test"
ROLES = ["p141_reader", "p141_root", "p141_approval", "p141_bad_direct", "p141_bad_helper", "p142_artifact"]
ROOT_CHECKS = [
    "original_artifact_schema22_admission", "registry_exact_admissions",
    "original_root_workflow_AEAD_SQL_commit_readback", "root_named_metadata_exact",
    "real_plaintext_digest_exact", "real_ciphertext_hash_exact", "ciphertext_not_plaintext",
    "generated_public_key_roundtrip", "real_DB_audit_ingested",
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


def main(build_path, receipt_path):
    require(Path.cwd().resolve() == ROOT.resolve(), "adapter_wrong_root")
    destination = (ROOT / receipt_path).resolve()
    require(destination.is_relative_to(ROOT / "implementation/p09/evidence") and destination.suffix == ".json"
        and not destination.exists(), "fresh_adapter_receipt_required")
    build_file = (ROOT / build_path).resolve()
    require(build_file.is_relative_to(ROOT / "target/p09-121-resource-optimized")
        and build_file.suffix == ".json", "build_receipt_outside_target")
    build = json.loads(build_file.read_text(encoding="utf-8-sig"))
    require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["exit_code"] == 0
        and build["source_freeze_exact_after"] and build["protected_executables_exact_after"]
        and build["logical_cpu_limit"] == build["cargo_jobs"] == 1
        and build["priority"] == "BelowNormal" and not build["diagnostics"] and build["catalog_profile"]["test"] is False,
        "accepted_probe_build_missing")
    require(build["whole_workspace_Rust_input_coverage_enforced"] and build["historical_parent_archive_verified"]
        and len(build["source_freeze"]) == 833 and len(build["protected_executables"]) >= 37,
        "new_build_coverage_missing")
    crypto_executable = build["executable_pin"]
    require(re.fullmatch(r"target/p09-121-resource-optimized/debug/examples/formula_registry_crypto_postgres_probe-p142-r[1-9][0-9]*\.exe",
        crypto_executable["path"]) is not None and pin(crypto_executable["path"]) == crypto_executable,
        "crypto_executable_binding_drift")
    historical_build_path = "target/p09-121-resource-optimized/p141-adapter-build-r5.json"
    historical_build = json.loads((ROOT/historical_build_path).read_text(encoding="utf-8-sig"))
    executable = historical_build["executable_pin"]
    require(historical_build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE"
        and executable in build["protected_executables"] and pin(executable["path"]) == executable,
        "original_metadata_probe_not_protected")
    additions = [
        "tools/p09/run_formula_registry_crypto_probe.py", "tools/p09/fixtures/formula_registry_crypto.sql",
        "tools/p09/run_formula_issuer_registry_adapter.py", "tools/p09/fixtures/formula_issuer_registry_adapter.sql",
        "tools/p09/run_formula_issuer_registry_sql_checks.py", "tools/p09/fixtures/formula_issuer_registry.sql",
        "tools/p09/fixtures/authorized_full_ir_intent.sql", build_file.relative_to(ROOT).as_posix(),
    ]
    sources = [p["path"] for p in build["source_freeze"]]
    sources += [path for path in additions if path not in sources]
    require(len(sources) == len(set(sources)) and set(additions).issubset(sources),
        "crypto_source_coverage_drift")
    require(all(pin(p["path"]) == p for p in build["source_freeze"]), "compiled_crypto_source_drift")
    freeze = [pin(p) for p in sources]
    migrations = sorted(p for p in sources if re.fullmatch(r"migrations/postgres/\d{4}_.+\.up\.sql", p))
    require(len(migrations) == 22, "adapter_migration_coverage_drift")
    docker = shutil.which("docker")
    require(docker is not None, "docker_not_available")
    resources = Resources()
    start = time.monotonic()
    run_id = str(uuid.uuid4())
    name = "hwpx-p142-" + run_id
    created_id, requested, stage = None, False, "resource_preflight"
    port, last_child = None, None
    password = secrets.token_hex(32)
    receipt = {
        "schema_version": "hwpx-agent.p09-142-root-crypto-sql22/v1", "state": "NOT_RUN",
        "run_id": run_id, "container_name": name, "container_id": None, "image": IMAGE,
        "source_freeze": freeze, "executable_pin": executable, "crypto_executable_pin": crypto_executable, "protected_executables": build["protected_executables"],
        "source_freeze_exact_after": False, "protected_executables_exact_after": False,
        "migrations_applied": [], "probe_runs": [], "container_removed": False,
        "actual_SQL_executed": False, "actual_Rust_DB_adapter_executed": False,
        "real_AEAD_executed": False, "Ed25519_public_key_generated": False,
        "real_Ed25519_approval_signature_executed": False, "original_product_consumer_executed": False,
        "durable_blob_store_qualified": False, "native_application_executed": False,
        "production_key_custody_qualified": False, "atomic_product_publication_qualified": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "resource_policy": {"logical_cpu_limit": 1, "priority": "BelowNormal", "container_memory_bytes": 536870912,
            "container_swap_total_bytes": 536870912, "pids_limit": 64, "cpu_stop_percent": 85,
            "cpu_stop_consecutive_samples": 3, "minimum_available_ram_mib": 4096, "sample_seconds": 2},
    }

    def command(args, text=None, timeout=20, cleanup=False, env=None, rust=False):
        nonlocal last_child
        if not cleanup:
            require(not resources.stop.is_set(), resources.reason or "resource_stop")
            require(time.monotonic() - start < 240, "adapter_total_time_limit")
        process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        deadline, first = time.monotonic() + timeout, text
        try:
            affinity, system = ctypes.c_size_t(), ctypes.c_size_t()
            resources.k.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
            require(resources.k.GetProcessAffinityMask(int(process._handle), ctypes.byref(affinity), ctypes.byref(system))
                and affinity.value == 1, "owned_child_affinity_not_inherited")
            if rust:
                resources.k.GetPriorityClass.argtypes = [ctypes.c_void_p]
                require(resources.k.GetPriorityClass(int(process._handle)) == 0x4000, "rust_priority_not_applied")
            while True:
                try:
                    output, errors = process.communicate(input=first, timeout=0.25)
                    break
                except subprocess.TimeoutExpired:
                    first = None
                    if not cleanup:
                        require(not resources.stop.is_set(), resources.reason or "resource_stop")
                    require(time.monotonic() < deadline, "owned_command_timeout")
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
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
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + row["sha256"] + "',false);\n" + (ROOT / path).read_text(encoding="utf-8"))
            receipt["migrations_applied"].append(row)
            receipt["actual_SQL_executed"] = True
        stage = "original_full_ir_fixture"
        require("P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25" in sql((ROOT / "tools/p09/fixtures/authorized_full_ir_intent.sql").read_text(encoding="utf-8")),
            "original_full_ir_fixture_failed")
        receipt["original_full_ir_assertions"] = 25
        stage = "original_P140_SQL22_fixture"
        output = sql((ROOT / "tools/p09/fixtures/formula_issuer_registry.sql").read_text(encoding="utf-8"))
        checks = re.findall(r"^P140_SQL_CHECK:([a-z0-9_]+)$", output, re.MULTILINE)
        require(len(checks) == len(set(checks)) == 37, "original_SQL22_fixture_coverage_drift")
        receipt["original_SQL22_checks_committed"] = checks
        stage = "new_credential_profiles"
        sql((ROOT / "tools/p09/fixtures/formula_issuer_registry_adapter.sql").read_text(encoding="utf-8"))
        sql((ROOT / "tools/p09/fixtures/formula_registry_crypto.sql").read_text(encoding="utf-8"))
        # Generated hex only, stdin only. Never print, persist or put passwords in command arguments.
        sql("\n".join("ALTER ROLE " + role + " PASSWORD '" + password + "';" for role in ROLES))
        stage = "Rust_credential_bound_metadata_probe"
        probe("metadata", CHECKS)
        stage = "original_root_AEAD_SQL_workflow"
        require(pin(crypto_executable["path"]) == crypto_executable, "crypto_executable_drift")
        child = command([str(ROOT/crypto_executable["path"])], timeout=60, rust=True,
            env=dict(os.environ, P142_DB_PORT=str(port), P142_DB_PASSWORD=password))
        require(child.stdout.lstrip().startswith("{"), "crypto_probe_not_JSON_protocol")
        result = json.loads(child.stdout)
        allowed = {"state", "checks", "failed_stage", "real_approval_signature_or_product_consumer_executed",
            "durable_blob_store_qualified", "production_key_custody_qualified", "P09_gate", "product_complete"}
        require(set(result) == allowed and result["P09_gate"] == "OPEN" and result["product_complete"] is False
            and result["real_approval_signature_or_product_consumer_executed"] is False
            and result["durable_blob_store_qualified"] is False and result["production_key_custody_qualified"] is False
            and len(set(result["checks"])) == len(result["checks"])
            and all(check in ROOT_CHECKS for check in result["checks"]), "crypto_probe_closed_protocol_drift")
        receipt["crypto_probe"] = {"exit_code": child.returncode, "result": result}
        require(child.returncode == 0
            and result["state"] == "PASS_ORIGINAL_ROOT_AEAD_AND_SQL_NOT_APPROVAL_CONSUMER_OR_GATE"
            and result["checks"] == ROOT_CHECKS and result["failed_stage"] is None,
            "original_root_crypto_workflow_failed")
        receipt["real_AEAD_executed"] = receipt["Ed25519_public_key_generated"] = True
        stage = "owned_schema_control_base_migrations"
        sql("CREATE DATABASE p141_changed_schema;")
        controls = []
        for path in migrations[:-1]:
            fingerprint = next(p["sha256"] for p in freeze if p["path"] == path)
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + fingerprint + "',false);\n" + (ROOT/path).read_text(encoding="utf-8"), "p141_changed_schema")
            controls.append({"path": path, "migration_sha256_setting": fingerprint})
        # Clone the schema21 base before applying SQL22: no UPDATE/DELETE/trigger bypass/constraint weakening.
        sql("CREATE DATABASE p141_correct_schema TEMPLATE p141_changed_schema;")
        path = migrations[-1]
        fingerprint = next(p["sha256"] for p in freeze if p["path"] == path)
        fixture = (ROOT / "tools/p09/fixtures/formula_issuer_registry_adapter.sql").read_text(encoding="utf-8")
        require(fixture.count("GRANT USAGE ON SCHEMA hwpx_agent TO") == 1, "profile_grant_section_ambiguous")
        # Roles are cluster-wide and already exist. Reuse the exact same grant statements in both empty controls.
        grants = "BEGIN; GRANT USAGE ON SCHEMA hwpx_agent TO" + fixture.split("GRANT USAGE ON SCHEMA hwpx_agent TO", 1)[1]
        for database, installed in [("p141_changed_schema", "0"*64), ("p141_correct_schema", fingerprint)]:
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + installed + "',false);\n" + (ROOT/path).read_text(encoding="utf-8"), database)
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
            "'approval_revocations',(SELECT count(*) FROM hwpx_agent.formula_approval_revocations)); COMMIT;").splitlines()[-1])
        require(history == {"root_history": 4, "root_max": 4, "approval_history": 3, "approval_max": 3,
            "root_revocations": 2, "approval_revocations": 2}, "final_history_inexact")
        receipt["final_history"] = history
        require([pin(p) for p in sources] == freeze and pin(executable["path"]) == executable
            and pin(crypto_executable["path"]) == crypto_executable, "adapter_input_freeze_drift")
        require(all(pin(p["path"]) == p for p in build["protected_executables"]), "protected_executable_drift")
        receipt["source_freeze_exact_after"] = receipt["protected_executables_exact_after"] = True
        inspect()
        receipt["state"] = "PASS_ORIGINAL_ROOT_AEAD_SQL22_NOT_APPROVAL_CONSUMER_NATIVE_OR_GATE"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        receipt["state"], receipt["failed_stage"] = "FAIL_CLOSED", stage
        receipt["error_code"] = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        if last_child is not None:
            receipt["last_command_exit_code"] = last_child.returncode
            state = re.search(r"ERROR:\s+([A-Z0-9]{5}):", last_child.stderr)
            receipt["sqlstate"] = state.group(1) if state else None
            constraint = re.search(r"CONSTRAINT NAME:\s+([a-z][a-z0-9_]{0,127})", last_child.stderr)
            receipt["sql_constraint_name"] = constraint.group(1) if constraint else None
    finally:
        resources.done.set()
        if resources.thread.is_alive():
            resources.thread.join(timeout=3)
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
    args = parser.parse_args()
    try:
        raise SystemExit(main(args.build_receipt, args.receipt))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED_BEFORE_OWNED_CONTAINER", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
