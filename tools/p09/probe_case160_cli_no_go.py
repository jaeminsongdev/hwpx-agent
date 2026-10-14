"""Exact owned CLI startup without GO; product can never be authorized."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import case160_attempt_controller as controller
from bounded_process_progress import BoundedProcessCapture

SELF = "tools/p09/probe_case160_cli_no_go.py"
OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-no-go-r377.v1.json"


def main():
    c = controller.CURRENT; a = controller.a
    guard = c.FIRST.terminal_metadata_pressure_v1.guard_type(c.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    destination = c.old.c.ROOT/OUTPUT
    a.require(not destination.exists(), "EXCLUSIVE_CLI_NO_GO_REPORT")
    process = capture = job = None; empty = False; clean = True
    out = dict(state="FAILED_EXACT_CLI_NO_GO_DIAGNOSTIC_NOT_PRODUCT", GO_sent=False,
        product_or_Native_executed=False, accepted_count_delta=0, P09_gate="OPEN")
    started = time.monotonic()
    try:
        guard.acquire(); q = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        q.pin(SELF); q.pin(controller.SELF)
        windows = guard.windows; job = windows.job(); limits = windows.verify_job_limits(job)
        process = subprocess.Popen([sys.executable, "-B", str(c.old.c.ROOT/controller.SELF), "--owned-worker", "--task", controller.TASK],
            cwd=c.old.c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
        handle = windows.k.OpenProcess(0x101, False, process.pid)
        try: a.require(handle and windows.k.AssignProcessToJobObject(job, handle), "NO_GO_OWNED_JOB_ASSIGN")
        finally:
            if handle: a.require(windows.k.CloseHandle(handle), "NO_GO_ASSIGN_HANDLE_CLOSE")
        # Bounded capture closes empty stdin. The original worker must reject EOF.
        capture = BoundedProcessCapture(process, output_limit=8192, parse_markers=False)
        deadline = time.monotonic()+15
        while process.poll() is None:
            time.sleep(.5); guard.check(force=True)
            a.require(windows.accounting(job)["peak_job_private_percent"] < a.c.POLICY["job_memory_stop_percent"], "NO_GO_MEMORY_STOP")
            a.require(time.monotonic() < deadline, "NO_GO_DIAGNOSTIC15_TIMEOUT")
        output, errors = capture.communicate(timeout=3)
        observed = json.loads(output)
        code = observed.get("error_code") if type(observed) is dict else None
        a.require(process.returncode != 0 and not errors and type(code) is str and code.endswith("WORKER_NOT_AUTHORIZED"), "EXACT_ORIGINAL_GO_REJECTION")
        final = windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
        a.require(empty, "NO_GO_JOB_EMPTY")
        q.finish(); guard.check(force=True)
        out.update(state="PASS_EXACT_CLI_ORIGINAL_GO_REJECTION_NOT_PRODUCT_OR_NATIVE", worker_error_code=code,
            owned_Job_limits=limits, fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            source_pins=list(q.snapshots.values()), stdout_bytes=len(output), stderr_bytes=len(errors))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        out["error_type"] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]): out["error_code"] = error.args[0]
    finally:
        try:
            if process and process.poll() is None: process.kill(); process.wait(timeout=5)
            if capture: capture.close()
            elif process:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream: stream.close()
            if job:
                final = guard.windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
                clean = bool(guard.windows.k.CloseHandle(job)) and empty
        except (ValueError, OSError, subprocess.SubprocessError): clean = False
        guard.close()
        out.update(cleanup_confirmed=guard.cleanup and clean and (process is None or empty),
            elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    raw = (json.dumps(out, ensure_ascii=True, allow_nan=False, indent=2)+"\n").encode("utf-8")
    a.require(len(raw) <= 65536, "BOUNDED_CLI_NO_GO_REPORT")
    controller.publish(destination, raw, lambda:None)
    print(json.dumps({k:out.get(k) for k in ("state", "worker_error_code", "error_code", "elapsed_seconds", "cleanup_confirmed", "CPU_max", "RAM_min")}))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(main())
