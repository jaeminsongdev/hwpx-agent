"""P140 owned networkless PostgreSQL22 metadata/CAS checks. No operational DB or Rust/native execution."""
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
LABEL = "hwpx-agent.p09-140-owned-sql-test"
FIXTURE = "tools/p09/fixtures/formula_issuer_registry.sql"
ORIGINAL = "tools/p09/fixtures/authorized_full_ir_intent.sql"
PREVIOUS = "implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json"
TABLES = ["formula_issuer_trust_versions", "formula_issuer_trust_revocations", "formula_approval_versions", "formula_approval_revocations"]


def require(ok, code):
    if not ok:
        raise ValueError(code)


def pin(path):
    source = ROOT / path
    require(source.is_file() and not source.is_symlink() and not source.is_junction(), "sql_source_link_or_missing")
    raw = source.read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class Resources:
    def __init__(self):
        require(os.name == "nt", "windows_resource_sampler_required")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.k.GetCurrentProcess.restype = ctypes.c_void_p
        self.handle = self.k.GetCurrentProcess()
        self.k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.k.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        require(self.k.SetPriorityClass(self.handle, 0x4000) and self.k.SetProcessAffinityMask(self.handle, 1), "python_resource_limit_not_applied")
        self.last = self.cpu_times()
        self.samples, self.hot = [], 0
        self.stop, self.done = threading.Event(), threading.Event()
        self.reason = None
        self.thread = threading.Thread(target=self.watch, daemon=True)

    def cpu_times(self):
        values = [ctypes.c_uint64() for _ in range(3)]
        require(self.k.GetSystemTimes(*(ctypes.byref(v) for v in values)), "cpu_sample_failed")
        return tuple(v.value for v in values)

    def sample(self):
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_uint32), ("load", ctypes.c_uint32)] + [(name, ctypes.c_uint64) for name in
                ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
        memory = Memory()
        memory.length = ctypes.sizeof(memory)
        require(self.k.GlobalMemoryStatusEx(ctypes.byref(memory)), "ram_sample_failed")
        now = self.cpu_times()
        idle = now[0] - self.last[0]
        total = now[1] + now[2] - self.last[1] - self.last[2]
        self.last = now
        require(total > 0, "cpu_sample_interval_missing")
        row = {"time_utc": datetime.now(timezone.utc).isoformat(), "system_cpu_percent": round(100 * (total-idle)/total, 2),
            "available_ram_mib": round(memory.available/1048576, 2)}
        self.samples.append(row)
        self.hot = self.hot + 1 if row["system_cpu_percent"] >= 85 else 0
        if row["available_ram_mib"] < 4096:
            self.reason = "STOP_LOW_AVAILABLE_RAM"
        elif self.hot >= 3:
            self.reason = "STOP_SUSTAINED_SYSTEM_CPU"
        if self.reason:
            self.stop.set()
        return row

    def start(self):
        time.sleep(0.25)
        first = self.sample()
        require(first["system_cpu_percent"] < 85 and first["available_ram_mib"] >= 4096, "resource_preflight_deferred")
        self.thread.start()

    def watch(self):
        while not self.done.wait(2):
            try:
                self.sample()
            except (ValueError, OSError):
                self.reason = "STOP_RESOURCE_OBSERVATION_FAILED"
                self.stop.set()
                return


def main():
    require(Path.cwd().resolve() == ROOT.resolve(), "sql_wrong_root")
    docker = shutil.which("docker")
    require(docker is not None, "docker_not_available")
    migrations = []
    for number in range(1, 23):
        matches = list((ROOT / "migrations/postgres").glob(f"{number:04}_*.up.sql"))
        require(len(matches) == 1, "migration_identity_ambiguous")
        migrations.append(matches[0].relative_to(ROOT).as_posix())
    sources = migrations + [FIXTURE, ORIGINAL, PREVIOUS, "tools/p09/run_formula_issuer_registry_sql_checks.py"]
    freeze = [pin(p) for p in sources]
    fixture = (ROOT / FIXTURE).read_text(encoding="utf-8")
    expected = re.findall(r"SELECT pg_temp\.(?:ok|denied)\('([a-z0-9_]+)'", fixture)
    require(len(expected) == len(set(expected)) == 37, "sql_check_inventory_drift")
    run_id = str(uuid.uuid4())
    name = "hwpx-agent-p140-" + run_id.replace("-", "")[:12]
    resources = Resources()
    receipt = {"schema_version": "hwpx-agent.p09-owned-formula-issuer-registry-sql/v1", "state": "PENDING",
        "run_id": run_id, "container": name, "image": IMAGE, "source_freeze": freeze,
        "actual_sql_executed": False, "migrations_applied": [], "sql_check_inventory": expected,
        "sql_checks_committed": [], "provisional_check_markers_before_rollback": [], "concurrency": None,
        "native_application_executed": False, "rust_adapters_executed": False, "operational_database_changed": False,
        "production_key_custody_qualified": False, "real_AEAD_or_signatures_executed": False,
        "atomic_product_publication_qualified": False, "P09_gate": "OPEN", "product_complete": False,
        "container_removed": False, "resource_policy": {"logical_cpu_limit": 1, "priority": "BelowNormal",
            "container_memory_bytes": 536870912, "container_swap_total_bytes": 536870912, "pids_limit": 64,
            "sample_seconds": 2, "cpu_stop_percent": 85, "cpu_stop_consecutive_samples": 3, "minimum_available_ram_mib": 4096}}
    child = None
    created_id = None
    creation_requested = False
    race_workers = []
    stage = "preflight"
    start = time.monotonic()

    def command(args, text=None, timeout=30, env=None, cleanup=False):
        nonlocal child
        if not cleanup:
            require(not resources.stop.is_set(), resources.reason or "resource_stop")
            require(time.monotonic()-start < 240, "sql_run_time_limit")
        process = subprocess.Popen([docker, *args], cwd=ROOT, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        deadline = time.monotonic()+timeout
        first = text
        try:
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
        child = subprocess.CompletedProcess([docker, *args], process.returncode, output, errors)
        return child

    def sql(text, timeout=20):
        result = command(["exec", "-i", name, "psql", "-X", "--no-align", "--tuples-only", "--quiet",
            "--set", "ON_ERROR_STOP=1", "--set", "VERBOSITY=verbose", "--username", "postgres", "--dbname", "postgres"], text, timeout)
        require(result.returncode == 0, "sql_execution_failed")
        return result.stdout.strip()

    def inspect(cleanup=False):
        result = command(["inspect", name], cleanup=cleanup)
        require(result.returncode == 0, "owned_container_not_found")
        rows = json.loads(result.stdout)
        require(len(rows) == 1, "owned_container_ambiguous")
        item = rows[0]
        require(item["Id"] == created_id and item["Name"] == "/"+name
            and item["Config"]["Labels"].get(LABEL) == run_id and item["Config"]["Image"] == IMAGE
            and item["Image"] == receipt["image_id"], "owned_container_identity_mismatch")
        host = item["HostConfig"]
        require(host["NetworkMode"] == "none" and not host["PortBindings"] and not item["Mounts"]
            and host["Memory"] == host["MemorySwap"] == 536870912 and host["NanoCpus"] == 1000000000
            and host["PidsLimit"] == 64 and host["ReadonlyRootfs"] is True
            and set(host["Tmpfs"]) == {"/var/lib/postgresql", "/tmp", "/var/run/postgresql"}, "owned_container_isolation_mismatch")
        return item

    def concurrent_root_cas():
        scope = "BEGIN; SET LOCAL statement_timeout='8s'; SET LOCAL lock_timeout='6s'; SET LOCAL ROLE p140_root; "
        scope += "DO $$BEGIN PERFORM set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true); "
        scope += "PERFORM set_config('hwpx_agent.subject_sha256',repeat('a',64),true); END$$; "

        def registration(version, expected_generation, artifact, digest):
            return "SELECT hwpx_agent.register_formula_issuer_trust_v1('60000000-0000-0000-0000-000000000001'," + \
                "'62000000-0000-0000-0000-000000000002',repeat('a',64),'"+version+"',"+str(expected_generation)+ \
                ",'p140-contended',0,floor(extract(epoch FROM clock_timestamp()))::bigint+3600,600,'"+artifact+"',repeat('"+digest+"',64)); "

        require(sql(scope+registration('75000000-0000-0000-0000-000000000001',0,'71000000-0000-0000-0000-000000000002','b')+'COMMIT;') == '1',
            "contended_scope_seed_failed")

        def spawn(application, version, artifact, digest, hold):
            require(not resources.stop.is_set(), resources.reason or "resource_stop")
            text = "SET application_name='"+application+"'; "+scope+registration(version,1,artifact,digest)
            text += "SELECT pg_sleep(3); " if hold else ""
            text += "COMMIT;"
            process = subprocess.Popen([docker,"exec","-i",name,"psql","-X","--no-align","--tuples-only","--quiet",
                "--set","ON_ERROR_STOP=1","--set","VERBOSITY=verbose","--username","postgres","--dbname","postgres"],
                cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')
            race_workers.append(process)
            process.stdin.write(text)
            process.stdin.close()
            process.stdin = None
            return process

        def observe(application, clause):
            deadline = time.monotonic()+2
            while time.monotonic() < deadline:
                if sql("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='"+application+"' AND "+clause+");",timeout=3) == 't':
                    return True
                time.sleep(0.1)
            return False

        first = spawn('p140-race-A','75000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000004','d',True)
        require(observe('p140-race-A',"wait_event='PgSleep'"), "first_transaction_lock_hold_not_observed")
        second = spawn('p140-race-B','75000000-0000-0000-0000-000000000003','71000000-0000-0000-0000-000000000006','f',False)
        require(observe('p140-race-B',"wait_event_type='Lock'"), "contending_transaction_lock_wait_not_observed")
        deadline = time.monotonic()+10
        while first.poll() is None or second.poll() is None:
            require(not resources.stop.is_set(), resources.reason or "resource_stop")
            require(time.monotonic() < deadline, "owned_race_timeout")
            time.sleep(0.1)
        a_out,a_err = first.communicate()
        b_out,b_err = second.communicate()
        require(first.returncode == 0 and a_out.strip() == '2' and second.returncode != 0
            and re.search(r"ERROR:\s+40001:\s+FORMULA_ISSUER_GENERATION_CHANGED",b_err) is not None,
            "contended_CAS_not_one_commit_one_stale_generation")
        counts = json.loads(sql("SELECT json_build_object('rows',count(*),'latest_generation',max(generation),"+
            "'loser_rows',count(*) FILTER(WHERE trust_version_id='75000000-0000-0000-0000-000000000003')) " +
            "FROM hwpx_agent.formula_issuer_trust_versions WHERE tenant_id='60000000-0000-0000-0000-000000000001' " +
            "AND project_id='62000000-0000-0000-0000-000000000002';"))
        require(counts == {"rows":2,"latest_generation":2,"loser_rows":0}, "contended_CAS_rollback_or_generation_drift")
        live = sql("BEGIN; SET LOCAL ROLE p140_read; DO $$BEGIN " +
            "PERFORM set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true); " +
            "PERFORM set_config('hwpx_agent.subject_sha256',repeat('a',64),true); END$$; " +
            "SELECT count(*)=1 AND bool_and(generation=2 AND trust_version_id='75000000-0000-0000-0000-000000000002' " +
            "AND trust_artifact_sha256=repeat('d',64)) FROM hwpx_agent.read_formula_issuer_trust_v1(" +
            "'60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000002',repeat('a',64)); COMMIT;")
        require(live == 't', "contended_winner_live_readback_missing")
        return {"state":"PASS_ONE_COMMIT_ONE_STALE_GENERATION_AFTER_REAL_LOCK_WAIT", "first_lock_holder_observed":True,
            "second_lock_wait_observed":True,"first_exit_code":first.returncode,"second_exit_code":second.returncode,
            "second_sqlstate":"40001","second_error_code":"FORMULA_ISSUER_GENERATION_CHANGED", **counts,
            "winner_live_named_readback":True, "fixture_only_lock_hold_seconds":3,"production_retry_added":False}

    try:
        resources.start()
        image = command(["image", "inspect", IMAGE])
        require(image.returncode == 0, "pinned_image_not_cached_no_pull")
        images = json.loads(image.stdout)
        require(len(images) == 1 and any(value.endswith("@"+IMAGE.rsplit("@",1)[1]) for value in images[0]["RepoDigests"]), "image_digest_mismatch")
        receipt["image_id"] = images[0]["Id"]
        stage = "create_owned_container"
        creation_requested = True
        result = command(["run", "--detach", "--pull", "never", "--name", name, "--label", LABEL+"="+run_id,
            "--network", "none", "--read-only", "--memory", "512m", "--memory-swap", "512m", "--cpus", "1", "--pids-limit", "64",
            "--tmpfs", "/var/lib/postgresql:rw,noexec,nosuid,size=512m", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "--tmpfs", "/var/run/postgresql:rw,noexec,nosuid,size=16m", "--env", "POSTGRES_PASSWORD", IMAGE],
            env=dict(os.environ, POSTGRES_PASSWORD=secrets.token_hex(32)))
        require(result.returncode == 0 and re.fullmatch(r"[a-f0-9]{64}", result.stdout.strip()), "owned_container_creation_failed")
        created_id = result.stdout.strip()
        inspect()
        stage = "wait_ready"
        ready = False
        for _ in range(30):
            # The image initialization server accepts only Unix sockets; require the final TCP-listening server.
            if command(["exec", name, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "postgres"], timeout=5).returncode == 0:
                ready = True
                break
            time.sleep(0.5)
        require(ready, "owned_database_not_ready")
        receipt["server_version_num"] = int(sql("SHOW server_version_num;"))
        for source in migrations:
            stage = "migration_" + Path(source).name[:4]
            row = next(p for p in freeze if p["path"] == source)
            sql("SELECT set_config('hwpx_agent.migration_sha256','"+row["sha256"]+"',false);\n"+(ROOT/source).read_text(encoding="utf-8"))
            receipt["actual_sql_executed"] = True
            receipt["migrations_applied"].append(row)
        stage = "schema_versions_exact"
        versions = sql("SELECT json_agg(version ORDER BY version) FROM hwpx_agent.schema_versions;")
        receipt["schema_versions"] = json.loads(versions)
        require(receipt["schema_versions"] == list(range(1,23)), "schema_versions_inexact")
        stage = "original_authorized_full_ir_fixture"
        require("P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25" in sql((ROOT/ORIGINAL).read_text(encoding="utf-8")), "original_full_ir_fixture_failed")
        receipt["original_full_ir_metadata_assertions"] = 25
        stage = "SQL22_permission_and_metadata_checks"
        output = sql(fixture)
        found = re.findall(r"^P140_SQL_CHECK:([a-z0-9_]+)$", output, re.MULTILINE)
        require(found == expected, "sql_marker_coverage_or_order_drift")
        receipt["sql_checks_committed"] = found
        stage = "contended_root_CAS_two_sessions"
        receipt["concurrency"] = concurrent_root_cas()
        stage = "finished_metadata_checks"
        require([pin(p) for p in sources] == freeze, "source_freeze_drift")
        inspect()
        receipt["state"] = "PASS_SQL22_ENGINE_METADATA_AND_CONTENDED_CAS_NOT_RUST_CRYPTO_NATIVE_OR_GATE"
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        receipt["state"] = "FAIL_CLOSED"
        receipt["failed_stage"] = stage
        receipt["error_code"] = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+",str(error)) else "redacted"
        if child is not None:
            receipt["last_command_exit_code"] = child.returncode
            state = re.search(r"ERROR:\s+([A-Z0-9]{5}):",child.stderr)
            receipt["sqlstate"] = state.group(1) if state else None
            receipt["provisional_check_markers_before_rollback"] = re.findall(r"^P140_SQL_CHECK:([a-z0-9_]+)$",child.stdout,re.MULTILINE)
    finally:
        for process in race_workers:
            if process.poll() is None:
                process.kill()
                process.communicate()
        resources.done.set()
        if resources.thread.is_alive():
            resources.thread.join(timeout=3)
        if creation_requested and created_id is None:
            try:
                discovered = command(["inspect", name], cleanup=True)
                if discovered.returncode == 0:
                    rows = json.loads(discovered.stdout)
                    require(len(rows) == 1 and rows[0]["Name"] == "/"+name
                        and rows[0]["Config"]["Labels"].get(LABEL) == run_id
                        and rows[0]["Config"]["Image"] == IMAGE and rows[0]["Image"] == receipt["image_id"],
                        "unknown_creation_owner_mismatch")
                    created_id = rows[0]["Id"]
                else:
                    require(re.search(r"no such (object|container)", discovered.stderr, re.IGNORECASE) is not None,
                        "unknown_creation_outcome")
                    receipt["container_removed"] = True
            except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
                receipt["state"] = "FAIL_CLOSED"
                receipt["cleanup_error_code"] = "unknown_creation_outcome_preserve_for_review"
        if created_id is not None:
            try:
                inspect(cleanup=True)
                removed = command(["rm", "--force", created_id], cleanup=True)
                require(removed.returncode == 0, "owned_container_removal_failed")
                remaining = command(["inspect", created_id], cleanup=True)
                receipt["container_removed"] = remaining.returncode != 0 and re.search(
                    r"no such (object|container)", remaining.stderr, re.IGNORECASE) is not None
                require(receipt["container_removed"], "owned_container_still_present")
            except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
                receipt["state"] = "FAIL_CLOSED"
                receipt["cleanup_error_code"] = "owned_container_cleanup_unverified"
        receipt["elapsed_seconds"] = round(time.monotonic()-start,2)
        receipt["resource_samples"] = resources.samples
        receipt["resource_stop_reason"] = resources.reason
        if resources.reason:
            receipt["state"] = "FAIL_CLOSED"
        print(json.dumps(receipt, indent=2))
    return 0 if receipt["state"].startswith("PASS_") and receipt["container_removed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Za-z0-9_]+",str(error)) else "redacted"
        print(json.dumps({"state":"FAIL_CLOSED_BEFORE_OWNED_CONTAINER", "error_code":code,"P09_gate":"OPEN"}))
        raise SystemExit(1) from None
