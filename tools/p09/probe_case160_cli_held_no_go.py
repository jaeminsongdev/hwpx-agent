"""Exact no-GO CLI with held worker-source subset; not a full Native frame."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import case160_attempt_controller as controller
from bounded_process_progress import BoundedProcessCapture

SELF = "tools/p09/probe_case160_cli_held_no_go.py"
OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-held-no-go-r378.v1.json"
GO = sys.argv[1:] == ["--go"]
if GO:
    OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-held-product-r380.v1.json"


def main():
    c = controller.CURRENT; a = controller.a
    guard = c.FIRST.terminal_metadata_pressure_v1.guard_type(c.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    destination = c.old.c.ROOT/OUTPUT
    a.require(not destination.exists(), "EXCLUSIVE_CLI_NO_GO_REPORT")
    process = capture = job = held = binding = None; empty = False; clean = True
    out = dict(state="FAILED_EXACT_CLI_NO_GO_DIAGNOSTIC_NOT_PRODUCT", GO_sent=False,
        product_or_Native_executed=False, accepted_count_delta=0, P09_gate="OPEN")
    if GO:
        out.update(product_or_Native_executed=None, actual_product_child_executed=None,
            full_Native_frame_executed=False, official_acceptance_claimed=False)
    started = time.monotonic()
    try:
        guard.acquire(); q = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        q.pin(SELF); q.pin(controller.SELF)
        stopped = q.json("implementation/p09/evidence/p09-361-case160-current-runtime-run006.v1.json")
        selected = {p["path"]:p for p in stopped["bootstrap_metadata"]["input_pins"]
            if p["path"].startswith("tools/p09/") and p["path"].endswith(".py")}
        for p in (c.CONFIG_PIN, c.MANIFEST, c.CAPSULE): selected[p["path"]] = p
        if GO:
            executable = stopped["compiled_test_executable_pin"]
            selected[executable["path"]] = executable
            a.exact(stopped["selected_test_names"], ["actual_import::source_review_cell_output::cached_body_callback_rechecks_actual_aead_acl_regrant_and_advanced_head"], "ONE_ORIGINAL_CASE160")
        a.require(0 < len(selected) <= 512, "BOUNDED_HELD_STARTUP_SUBSET")
        for name, pin in selected.items(): a.exact(q.pin(name), pin, "CURRENT_HELD_STARTUP_BYTES")
        held = a.locks.InputLocks(c.old.c.ROOT, q.checkpoint)
        held.acquire(selected)
        out.update(held_source_subset_count=len(selected), original_SHARE_READ_deny_write_delete=True,
            full_Native_frame_or_product_scope_qualification_claimed=False,
            same_actual_worker_argv_without_B=True)
        windows = guard.windows; job = windows.job(); limits = windows.verify_job_limits(job)
        if GO: binding = c.prior.WINDOW.connect(subprocess.Popen, BoundedProcessCapture)
        factory = binding.Popen if GO else subprocess.Popen
        process = factory([sys.executable, str(c.old.c.ROOT/controller.SELF), "--owned-worker", "--task", controller.TASK],
            cwd=c.old.c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
        handle = windows.k.OpenProcess(0x101, False, process.pid)
        try: a.require(handle and windows.k.AssignProcessToJobObject(job, handle), "NO_GO_OWNED_JOB_ASSIGN")
        finally:
            if handle: a.require(windows.k.CloseHandle(handle), "NO_GO_ASSIGN_HANDLE_CLOSE")
        if GO:
            guard.check(); process.stdin.write(b"P149_GO\n"); process.stdin.flush()
            out["GO_sent"] = True
        # No-GO closes empty stdin; GO uses the original strict window/capture.
        capture_type = binding.Capture if GO else BoundedProcessCapture
        capture = capture_type(process, output_limit=8192, parse_markers=False)
        deadline = time.monotonic()+15
        while process.poll() is None:
            time.sleep(.5); guard.check(force=True)
            a.require(windows.accounting(job)["peak_job_private_percent"] < a.c.POLICY["job_memory_stop_percent"], "NO_GO_MEMORY_STOP")
            a.require(time.monotonic() < deadline, "NO_GO_DIAGNOSTIC15_TIMEOUT")
        output, errors = capture.communicate(timeout=3)
        code = None
        if GO:
            a.require(process.returncode == 0 and not errors, "ACTUAL_CASE160_TERMINAL")
            summaries = re.findall(r"test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out", output)
            a.require(len(summaries) == 1 and summaries[0][:4] == ("1", "0", "0", "0"), "ONE_ACTUAL_CASE160_PASS")
            out.update(actual_product_child_executed=True, product_or_Native_executed=True,
                product_summary=dict(passed=1, failed=0, ignored=0, measured=0, filtered_out=int(summaries[0][4])),
                strict_product_window=binding.state.diagnostics())
        else:
            observed = json.loads(output)
            code = observed.get("error_code") if type(observed) is dict else None
            a.require(process.returncode != 0 and not errors and type(code) is str and code.endswith("WORKER_NOT_AUTHORIZED"), "EXACT_ORIGINAL_GO_REJECTION")
        final = windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
        a.require(empty, "NO_GO_JOB_EMPTY")
        q.finish(); guard.check(force=True)
        out.update(state="PASS_EXACT_CLI_HELD_SUBSET_ACTUAL_PRODUCT_NOT_NATIVE_OR_ACCEPTANCE" if GO else "PASS_EXACT_CLI_HELD_SUBSET_GO_REJECTION_NOT_PRODUCT_OR_NATIVE", worker_error_code=code,
            owned_Job_limits=limits, fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            source_pins=list(q.snapshots.values()), stdout_bytes=len(output), stderr_bytes=len(errors))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        out["error_type"] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]): out["error_code"] = error.args[0]
    finally:
        try:
            if process and process.poll() is None: process.kill(); process.wait(timeout=5)
            if capture:
                capture.close()
                with capture.lock:
                    out["stdout_bytes"] = len(capture.buffers["stdout"])
                    out["stderr_bytes"] = len(capture.buffers["stderr"])
            elif process:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream: stream.close()
            if job:
                final = guard.windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
                clean = bool(guard.windows.k.CloseHandle(job)) and empty
        except (ValueError, OSError, subprocess.SubprocessError): clean = False
        if held:
            try: clean = bool(held.close()) and clean
            except (ValueError, OSError): clean = False
        if binding: out["strict_product_window"] = binding.state.diagnostics()
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
