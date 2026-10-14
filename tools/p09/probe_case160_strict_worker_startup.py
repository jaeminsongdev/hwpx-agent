"""Bounded owned worker diagnostic; final Rust call is intercepted."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
EXACT = sys.argv[1:] in (["--exact-controller-child"], ["--exact-controller-diagnostic"])
CHILD = sys.argv[1:] in (["--diagnostic-child"], ["--exact-controller-child"])
if CHILD: print(json.dumps(dict(stage="child_entry")), flush=True)
import case160_attempt_controller as controller
if CHILD: print(json.dumps(dict(stage="controller_import_complete")), flush=True)
from bounded_process_progress import BoundedProcessCapture

SELF = "tools/p09/probe_case160_strict_worker_startup.py"
OUTPUT = "implementation/p09/evidence/p09-361-case160-strict-owned-worker-startup-r378-run002.v1.json"
if EXACT:
    OUTPUT = "implementation/p09/evidence/p09-361-case160-controller-worker-startup-r379.v1.json"


def child():
    c = controller.CURRENT; a = controller.a
    c.old.base.configure(160)
    policy = None
    if EXACT:
        # Same configure and worker call as the controller's __main__ branch.
        # Diagnostic wrapper/argv and parent held scope remain different.
        execute = c.M.worker
    else:
        graph = c._env["graph_value"]()
        print(json.dumps(dict(stage="bounded_graph_complete")), flush=True)
        engine, _ = c.prior.template()
        print(json.dumps(dict(stage="template_complete")), flush=True)
        policy = graph.worker.raw_policy.Policy(c.old.c.ROOT, graph.binding, lambda:True, lambda:None)
        execute, state = graph.worker.connect_worker(engine.worker, policy)
    intercepted = []
    def sink(argv, **kwargs):
        a.exact(argv[1], "actual_import::source_review_cell_output::cached_body_callback_rechecks_actual_aead_acl_regrant_and_advanced_head",
            "EXACT_CASE160_PRODUCT_CALL_INTERCEPTED")
        a.exact(kwargs["stdin"], subprocess.DEVNULL, "ORIGINAL_PRODUCT_STDIN")
        a.exact(kwargs["env"]["RUST_TEST_THREADS"], "1", "ONE_TEST_THREAD")
        intercepted.append(True)
        print(json.dumps(dict(stage="product_call_intercepted")), flush=True)
        return 0
    with patch.object(subprocess, "call", sink): result = execute(controller.TASK)
    a.exact(result, 0, "ORIGINAL_WORKER_DIAGNOSTIC_RETURN")
    a.exact(intercepted, [True], "ONE_INTERCEPTED_CALL")
    if policy is not None: a.require(policy.restored, "WORKER_POLICY_RESTORED")
    print(json.dumps(dict(stage="completed", product_child_executed=False)), flush=True)
    return 0


def main():
    c = controller.CURRENT; a = controller.a
    guard = c.FIRST.terminal_metadata_pressure_v1.guard_type(c.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    destination = c.old.c.ROOT/OUTPUT
    a.require(not destination.exists(), "EXCLUSIVE_STARTUP_REPORT")
    process = capture = job = None
    started = time.monotonic(); empty = False; clean = True; stages = []
    out = dict(state="FAILED_WORKER_STARTUP_DIAGNOSTIC_NOT_PRODUCT", actual_product_or_Native_executed=False,
        accepted_count_delta=0, P09_gate="OPEN", diagnostic_only=True,
        original_controller_worker_called=EXACT, full_parent_Native_input_scope_held=False,
        actual_controller_CLI_argv_reproduced=False)
    try:
        guard.acquire(); q = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        q.pin(SELF); q.pin(controller.SELF)
        windows = guard.windows; job = windows.job(); limits = windows.verify_job_limits(job)
        binding = c.prior.WINDOW.connect(subprocess.Popen, BoundedProcessCapture)
        child_args = [sys.executable, str(c.old.c.ROOT/SELF), "--exact-controller-child"] if EXACT else [sys.executable, "-B", str(c.old.c.ROOT/SELF), "--diagnostic-child"]
        process = binding.Popen(child_args,
            cwd=c.old.c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
        handle = windows.k.OpenProcess(0x101, False, process.pid)
        try: a.require(handle and windows.k.AssignProcessToJobObject(job, handle), "STARTUP_OWNED_JOB_ASSIGN")
        finally:
            if handle: a.require(windows.k.CloseHandle(handle), "STARTUP_ASSIGN_HANDLE_CLOSE")
        guard.check(); process.stdin.write(b"P149_GO\n"); process.stdin.flush()
        capture = binding.Capture(process, output_limit=8192, parse_markers=False)
        deadline = time.monotonic()+15
        while process.poll() is None:
            time.sleep(.5); guard.check(force=True)
            a.require(windows.accounting(job)["peak_job_private_percent"] < a.c.POLICY["job_memory_stop_percent"], "STARTUP_MEMORY_STOP")
            a.require(time.monotonic() < deadline, "STARTUP_DIAGNOSTIC15_TIMEOUT")
        output, errors = capture.communicate(timeout=3)
        for line in output.splitlines():
            try: value = json.loads(line)
            except (ValueError, TypeError): continue
            if type(value) is dict and value.get("stage") in ("child_entry", "controller_import_complete", "bounded_graph_complete",
                    "template_complete", "product_call_intercepted", "completed"):
                stages.append(value["stage"])
        a.require(process.returncode == 0 and not errors and stages[-1:] == ["completed"], "OWNED_STARTUP_TERMINAL")
        final = windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
        a.require(empty, "STARTUP_JOB_EMPTY")
        q.finish(); guard.check(force=True)
        out.update(state="PASS_OWNED_WORKER_STARTUP_PRODUCT_CALL_INTERCEPTED_NOT_PRODUCT_OR_NATIVE",
            strict_product_window=binding.state.diagnostics(), owned_Job_limits=limits, fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            source_pins=list(q.snapshots.values()))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        out["error_type"] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]):
            out["error_code"] = error.args[0]
    finally:
        try:
            if process and process.poll() is None: process.kill(); process.wait(timeout=5)
            if capture:
                # Cleanup must not re-enter the already-expired window through
                # communicate -> self.progress. Close then inspect bounded bytes.
                capture.close()
                with capture.lock:
                    output, errors = tuple(bytes(capture.buffers[name]).decode("utf-8", errors="replace")
                        for name in ("stdout", "stderr"))
                for line in output.splitlines():
                    try: value = json.loads(line)
                    except (ValueError, TypeError): continue
                    stage = value.get("stage") if type(value) is dict else None
                    if stage in ("child_entry", "controller_import_complete", "bounded_graph_complete", "template_complete", "product_call_intercepted", "completed") and stage not in stages:
                        stages.append(stage)
                out["stdout_bytes"] = len(output); out["stderr_bytes"] = len(errors)
                out["stdin_closed_after_capture"] = bool(process.stdin.closed)
            elif process:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream: stream.close()
            if job:
                final = guard.windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
                clean = bool(guard.windows.k.CloseHandle(job)) and empty
        except (ValueError, OSError, subprocess.SubprocessError): clean = False
        guard.close()
        out.update(cleanup_confirmed=guard.cleanup and clean and (process is None or empty), stages=stages,
            elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    raw = (json.dumps(out, ensure_ascii=True, allow_nan=False, indent=2)+"\n").encode("utf-8")
    a.require(len(raw) <= 65536, "BOUNDED_STARTUP_REPORT")
    controller.publish(destination, raw, lambda:None)
    print(json.dumps({k:out.get(k) for k in ("state", "stages", "error_code", "stdout_bytes", "stderr_bytes", "cleanup_confirmed", "CPU_max", "RAM_min")}))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(child() if CHILD else main())
