"""Exact no-GO CLI with held worker-source subset; not a full Native frame."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
if sys.argv[1:] in (["--cpu-budget-child"], ["--cpu-budget-child", "0.8"]):
    import ctypes
    from ctypes import wintypes as w
    if sys.stdin.readline() != "P149_GO\n": raise SystemExit(2)
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = w.HANDLE
    k.IsProcessInJob.argtypes = [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)]
    member = w.BOOL()
    if not k.IsProcessInJob(k.GetCurrentProcess(), None, ctypes.byref(member)) or not member.value:
        raise SystemExit(2)
    target = .8 if sys.argv[-1] == "0.8" else .1
    started_cpu, started_wall = time.process_time(), time.monotonic()
    while time.process_time()-started_cpu < target: pass
    cpu, wall = time.process_time()-started_cpu, time.monotonic()-started_wall
    print(json.dumps(dict(cpu_seconds=cpu, wall_seconds=wall, cpu_per_wall_percent=100*cpu/wall,
        product_or_Native_executed=False, in_owned_Job=True)), flush=True)
    raise SystemExit(0)
if len(sys.argv) == 4 and sys.argv[1:3] == ["--trace-owned-worker", "--task"]:
    import faulthandler
    import runpy
    task = sys.argv[3]
    original = Path(__file__).resolve().with_name("case160_attempt_controller.py")
    sys.argv = [str(original), "--owned-worker", "--task", task]
    faulthandler.dump_traceback_later(5, repeat=False)
    try: runpy.run_path(str(original), run_name="__main__")
    finally: faulthandler.cancel_dump_traceback_later()
    raise SystemExit(0)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import case160_attempt_controller as controller
from bounded_process_progress import BoundedProcessCapture

SELF = "tools/p09/probe_case160_cli_held_no_go.py"
OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-held-no-go-r378.v1.json"
FULL_HELD = sys.argv[1:] == ["--go-full-held"]
BUDGET = sys.argv[1:] in (["--cpu-budget-probe"], ["--cpu-budget-sustained"])
CPU_TARGET = .8 if sys.argv[1:] == ["--cpu-budget-sustained"] else .1
TRACE = sys.argv[1:] == ["--go-evidence-trace"]
EVIDENCE_HELD = sys.argv[1:] in (["--go-evidence-held"], ["--go-evidence-trace"])
GO = BUDGET or sys.argv[1:] in (["--go"], ["--go-full-held"], ["--go-evidence-held"], ["--go-evidence-trace"])
if GO:
    OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-held-product-r380.v1.json"
if FULL_HELD:
    OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-full-held-product-r381-run002.v1.json"
if EVIDENCE_HELD:
    OUTPUT = "implementation/p09/evidence/p09-361-case160-exact-cli-evidence-held-product-r382.v1.json"
if TRACE:
    OUTPUT = "implementation/p09/evidence/p09-361-case160-evidence-held-worker-stack-r384.v1.json"
if BUDGET:
    OUTPUT = "implementation/p09/evidence/p09-361-owned-Job-cpu-budget-r385.v1.json"
    if CPU_TARGET == .8: OUTPUT = "implementation/p09/evidence/p09-361-owned-Job-sustained-cpu-budget-r386.v1.json"


def repository_stack(decoded, root):
    """Only bounded repository frames, including pinned virtual filenames."""
    frames = []
    prefix = root.as_posix()+"/"
    for filename, lineno, function in re.findall(r'File "([^"\n]+)", line ([0-9]+) in ([A-Za-z0-9_<>]+)', decoded):
        normalized = filename.replace("\\", "/")
        if normalized.casefold().startswith(prefix.casefold()):
            normalized = normalized[len(prefix):]
        if not normalized.startswith(("tools/p09/", "implementation/p09/")):
            continue
        if ":" in normalized or any(p in ("", ".", "..") for p in normalized.split("/")):
            continue
        frames.append(dict(path=normalized, line=int(lineno), function=function))
        if len(frames) == 16: break
    return frames


def main():
    c = controller.CURRENT; a = controller.a
    guard = c.FIRST.terminal_metadata_pressure_v1.guard_type(c.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    destination = c.old.c.ROOT/OUTPUT
    a.require(not destination.exists(), "EXCLUSIVE_CLI_NO_GO_REPORT")
    process = capture = job = held = binding = q = None; empty = False; clean = True
    out = dict(state="FAILED_EXACT_CLI_NO_GO_DIAGNOSTIC_NOT_PRODUCT", GO_sent=False,
        product_or_Native_executed=False, accepted_count_delta=0, P09_gate="OPEN")
    phase = "resource_admission"
    if GO:
        out.update(state="FAILED_EXACT_CLI_PRODUCT_DIAGNOSTIC_NOT_NATIVE_OR_ACCEPTANCE",
            product_or_Native_executed=None, actual_product_child_executed=None,
            full_Native_frame_executed=False, official_acceptance_claimed=False)
    job_samples = []
    started = time.monotonic()
    try:
        guard.acquire(); q = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        q.pin(SELF); q.pin(controller.SELF)
        stopped = {} if BUDGET else q.json("implementation/p09/evidence/p09-361-case160-current-runtime-run006.v1.json")
        phase = "worker_input_byte_qualification"
        selected = {p["path"]:p for p in stopped.get("bootstrap_metadata", {}).get("input_pins", [])
            if p["path"].startswith("tools/p09/") and p["path"].endswith(".py")}
        for p in (c.CONFIG_PIN, c.MANIFEST, c.CAPSULE): selected[p["path"]] = p
        if GO and not BUDGET:
            executable = stopped["compiled_test_executable_pin"]
            selected[executable["path"]] = executable
            a.exact(stopped["selected_test_names"], ["actual_import::source_review_cell_output::cached_body_callback_rechecks_actual_aead_acl_regrant_and_advanced_head"], "ONE_ORIGINAL_CASE160")
        a.require(0 < len(selected) <= 512, "BOUNDED_HELD_STARTUP_SUBSET")
        for name, pin in selected.items(): a.exact(q.pin(name), pin, "CURRENT_HELD_STARTUP_BYTES")
        lock_inputs = selected
        if FULL_HELD or EVIDENCE_HELD:
            declared = stopped["source_freeze"]
            a.require(type(declared) is list and len(declared) == 2850, "EXACT_DECLARED_PIN_LIST")
            declared_map = {p["path"]:p for p in declared}
            a.require(len(declared_map) == len(declared), "NO_DUPLICATE_DECLARED_LOCK_PINS")
            original = a.locks.input_pins(declared_map)
            a.require(len(original) == 2850, "EXACT_RUN006_DECLARED_LOCK_COUNT")
            lock_inputs = dict(original) if FULL_HELD else {n:p for n,p in original.items() if n.startswith("implementation/p09/")}
            for name, pin in selected.items():
                if name in lock_inputs: a.exact(lock_inputs[name], pin, "DECLARED_AND_FRESH_LOCK_PIN_AGREE")
                lock_inputs[name] = pin
            out.update(original_declared_file_count=len(original), all_original_declared_files_held=FULL_HELD,
                diagnostic_declared_group="all" if FULL_HELD else "implementation/p09/",
                all_declared_bytes_freshly_hashed=False,
                remaining_declared_bytes_proven_current=False,
                current_byte_verified_subset_count=len(selected))
        held = a.locks.InputLocks(c.old.c.ROOT, q.checkpoint)
        phase = "held_input_acquisition"
        held.acquire(lock_inputs)
        out.update(held_source_subset_count=len(lock_inputs), original_SHARE_READ_deny_write_delete=True,
            held_acquisition_witness=held.acquisition_witness(),
            full_Native_frame_or_product_scope_qualification_claimed=False,
            same_actual_worker_argv_without_B=True)
        windows = guard.windows; job = windows.job(); limits = windows.verify_job_limits(job)
        if BUDGET:
            ctypes = c.old.c.ctypes
            parent_rate = c.old.c.CpuRate()
            ctypes.set_last_error(0)
            observed = bool(windows.k.QueryInformationJobObject(None, 15, ctypes.byref(parent_rate), ctypes.sizeof(parent_rate), None))
            out.update(parent_associated_Job_cpu_query=dict(success=observed, flags=parent_rate.flags,
                rate=parent_rate.rate, win32_error=ctypes.get_last_error()),
                actual_product_child_executed=False, product_or_Native_executed=False,
                requested_cpu_seconds=CPU_TARGET, cpu_rate_or_affinity_changed=False)
        phase = "owned_worker_startup"
        if GO: binding = c.prior.WINDOW.connect(subprocess.Popen, BoundedProcessCapture)
        factory = binding.Popen if GO else subprocess.Popen
        command = [sys.executable, str(c.old.c.ROOT/controller.SELF), "--owned-worker", "--task", controller.TASK]
        if BUDGET:
            command = [sys.executable, str(c.old.c.ROOT/SELF), "--cpu-budget-child"]
            if CPU_TARGET == .8: command.append("0.8")
            out["same_actual_worker_argv_without_B"] = False
        if TRACE:
            command = [sys.executable, str(c.old.c.ROOT/SELF), "--trace-owned-worker", "--task", controller.TASK]
            out.update(same_actual_worker_argv_without_B=False, actual_controller_main_via_runpy=True,
                diagnostic_watchdog_thread_added=True, diagnostic_stack_timeout_seconds=5,
                production_controller_modified=False, raw_stack_or_log_persisted=False)
        process = factory(command,
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
        phase = "running_worker"
        deadline = time.monotonic()+15
        while process.poll() is None:
            time.sleep(.5); guard.check(force=True)
            sample = windows.accounting(job)
            if len(job_samples) < 32: job_samples.append(sample)
            a.require(sample["peak_job_private_percent"] < a.c.POLICY["job_memory_stop_percent"], "NO_GO_MEMORY_STOP")
            if binding: capture.progress()
            a.require(time.monotonic() < deadline, "NO_GO_DIAGNOSTIC15_TIMEOUT")
        output, errors = capture.communicate(timeout=3)
        code = None
        if BUDGET:
            observed = json.loads(output)
            a.require(process.returncode == 0 and not errors and type(observed) is dict
                and observed.get("in_owned_Job") is True and observed.get("product_or_Native_executed") is False,
                "BOUNDED_CPU_PROBE_TERMINAL")
            a.require(CPU_TARGET <= observed["cpu_seconds"] < CPU_TARGET+.1 and 0 < observed["wall_seconds"] < 15, "BOUNDED_CPU_PROBE_MEASUREMENT")
            out["cpu_budget_measurement"] = observed
        elif GO:
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
        held.verify_held_identities()
        q.finish(); guard.check(force=True)
        phase = "completed"
        out.update(state="PASS_EXACT_CLI_HELD_SUBSET_ACTUAL_PRODUCT_NOT_NATIVE_OR_ACCEPTANCE" if GO else "PASS_EXACT_CLI_HELD_SUBSET_GO_REJECTION_NOT_PRODUCT_OR_NATIVE", worker_error_code=code,
            owned_Job_limits=limits, fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            source_pins=list(q.snapshots.values()), stdout_bytes=len(output), stderr_bytes=len(errors))
        if BUDGET: out["state"] = "PASS_MEASURED_OWNED_JOB_CPU_BUDGET_NOT_PRODUCT_OR_POLICY_CHANGE"
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        out["error_type"] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]): out["error_code"] = error.args[0]
    finally:
        # Match the production runner: terminate the complete owned Job before
        # joining pipe readers, since product descendants may still own pipes.
        try:
            if job: clean = bool(guard.windows.k.TerminateJobObject(job, 1)) and clean
            if process and process.poll() is None: process.kill(); process.wait(timeout=5)
        except (ValueError, OSError, subprocess.SubprocessError): clean = False
        try:
            if capture:
                capture.close()
                with capture.lock:
                    out["stdout_bytes"] = len(capture.buffers["stdout"])
                    out["stderr_bytes"] = len(capture.buffers["stderr"])
                    if TRACE:
                        decoded = bytes(capture.buffers["stderr"]).decode("utf-8", errors="replace")
                        out["worker_wait_stack_repository_frames"] = repository_stack(decoded, c.old.c.ROOT)
            elif process:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream: stream.close()
            if job:
                deadline = time.monotonic()+5
                while True:
                    final = guard.windows.accounting(job); empty = final["active_processes"] == 0 and final["owned_processes"] == []
                    if empty or time.monotonic() >= deadline: break
                    time.sleep(.1)
                out["owned_job_final"] = final
                clean = empty and clean
        except (ValueError, OSError, subprocess.SubprocessError): clean = False
        finally:
            if job: clean = bool(guard.windows.k.CloseHandle(job)) and clean
        if held:
            try: clean = bool(held.close()) and clean
            except (ValueError, OSError): clean = False
        if binding: out["strict_product_window"] = binding.state.diagnostics()
        out["owned_job_samples"] = job_samples
        guard.close()
        out.update(cleanup_confirmed=guard.cleanup and clean and (process is None or empty),
            terminal_phase=phase,
            diagnostic_source_pin=q.snapshots.get(SELF) if q else None,
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in guard.samples if s.get("parent_cpu_machine_percent") is not None), default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in guard.samples if s.get("parent_private_mib") is not None), default=None),
            elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    raw = (json.dumps(out, ensure_ascii=True, allow_nan=False, indent=2)+"\n").encode("utf-8")
    a.require(len(raw) <= 65536, "BOUNDED_CLI_NO_GO_REPORT")
    controller.publish(destination, raw, lambda:None)
    print(json.dumps({k:out.get(k) for k in ("state", "worker_error_code", "error_code", "elapsed_seconds", "cleanup_confirmed", "CPU_max", "RAM_min")}))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(main())
