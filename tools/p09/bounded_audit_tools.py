"""Closed read-only tools, bounded pipes and pre-GO owned Job limits; never Cargo/SQL/native."""
import ctypes
from ctypes import wintypes as w
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

from conservative_maintenance import ROOT, Windows, decision, require

INPUT_LIMIT = 262144
OUTPUT_LIMITS = {"stdout": 1048576, "stderr": 32768}
TIMEOUT_SECONDS = 10
TASKS = {
    "rustfmt-stdin": ("rustfmt", ["--edition", "2024", "--emit", "stdout"]),
    "rust-input-inventory": ("rg", ["--threads", "1", "--files", "crates", "protocol/generated/rust",
        "tools/xtask", "-g", "*.rs", "-g", "Cargo.toml"]),
}


def payload_for(task, text):
    require(isinstance(task, str) and task in TASKS, "audit_tool_task_scope")
    if task == "rustfmt-stdin":
        require(isinstance(text, str), "audit_tool_input_scope")
        require(len(text) <= INPUT_LIMIT, "audit_tool_input_budget")
        try:
            data = text.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("audit_tool_input_encoding") from None
        require(len(data) <= INPUT_LIMIT, "audit_tool_input_budget")
        return data
    require(text is None, "audit_tool_input_scope")
    return b""


class AuditToolCapture:
    def __init__(self, process, request):
        require(isinstance(request, bytes) and len(request) <= INPUT_LIMIT+64, "audit_tool_wire_budget")
        self.process, self.request = process, request
        self.lock = threading.Lock()
        self.buffers = {"stdout": bytearray(), "stderr": bytearray()}
        self.error = None
        self.threads = [threading.Thread(target=self._read, args=(name,), daemon=True)
            for name in ("stdout", "stderr")]
        self.threads.append(threading.Thread(target=self._write, daemon=True))
        for thread in self.threads:
            thread.start()

    def _fail(self, code):
        with self.lock:
            self.error = self.error or code

    def _accept(self, name, chunk):
        with self.lock:
            if self.error:
                return
            if len(self.buffers[name])+len(chunk) > OUTPUT_LIMITS[name]:
                self.error = "audit_tool_output_budget"
                return
            self.buffers[name].extend(chunk)

    def _read(self, name):
        stream = getattr(self.process, name)
        try:
            while chunk := stream.read1(4096):
                self._accept(name, chunk)
        except (OSError, ValueError):
            self._fail("audit_tool_pipe_read_failed")
        finally:
            stream.close()

    def _write(self):
        try:
            view = memoryview(self.request)
            offset = 0
            while offset < len(view):
                count = self.process.stdin.write(view[offset:offset+65536])
                require(type(count) is int and 0 < count <= min(65536, len(view)-offset), "audit_tool_pipe_write_failed")
                offset += count
            self.process.stdin.flush()
        except (OSError, ValueError):
            self._fail("audit_tool_pipe_write_failed")
        finally:
            self.request = b""
            self.process.stdin.close()

    def check(self):
        with self.lock:
            require(self.error is None, self.error)

    def communicate(self, timeout):
        self.check()
        deadline = time.monotonic()+timeout
        self.process.wait(timeout=timeout)
        for thread in self.threads:
            thread.join(max(0, deadline-time.monotonic()))
        if any(thread.is_alive() for thread in self.threads):
            raise subprocess.TimeoutExpired("owned_readonly_audit_tool", timeout)
        self.check()
        try:
            return tuple(bytes(self.buffers[name]).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
                for name in ("stdout", "stderr"))
        except UnicodeDecodeError:
            raise ValueError("audit_tool_output_encoding") from None

    def close(self):
        for thread in self.threads:
            thread.join(2)
        require(not any(thread.is_alive() for thread in self.threads), "audit_tool_pipe_cleanup_timeout")


def sample(windows):
    for attempt in range(6):
        try:
            return windows.sample()
        except ValueError as error:
            if str(error) != "CPU_SAMPLE_INTERVAL_MISSING" or attempt == 5:
                raise
            time.sleep(0.02)


def executable_for(task):
    executable, _ = TASKS[task]
    located = shutil.which(executable)
    require(located is not None, "audit_tool_executable_missing")
    invoked = Path(located).absolute()
    resolved = invoked.resolve()
    require(invoked.name.lower() == executable+".exe" and invoked.is_file()
        and not invoked.is_junction() and resolved.is_file() and not resolved.is_symlink()
        and not resolved.is_junction(), "audit_tool_executable_scope")
    if invoked.is_symlink():
        require(executable == "rustfmt" and resolved.name.lower() == "rustup.exe"
            and resolved.parent == invoked.parent.resolve(), "audit_tool_executable_scope")
    else:
        require(resolved.name.lower() == executable+".exe", "audit_tool_executable_scope")
    # Preserve argv[0]=rustfmt.exe; resolving to rustup.exe would change proxy dispatch.
    return str(invoked)


def worker(task):
    windows = Windows()
    stream = sys.stdin.buffer
    require(stream.readline(32) == b"P149_AUDIT_GO\n", "audit_tool_worker_not_authorized")
    member = w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(), None, ctypes.byref(member)) and member.value,
        "audit_tool_worker_not_in_job")
    header = stream.readline(16)
    require(re.fullmatch(rb"[0-9]{1,6}\n", header), "audit_tool_wire_scope")
    size = int(header)
    require(size <= INPUT_LIMIT and (task == "rustfmt-stdin" or size == 0), "audit_tool_input_budget")
    data = stream.read(size)
    require(len(data) == size and stream.read(1) == b"", "audit_tool_wire_incomplete_or_extra")
    path = executable_for(task)
    _, args = TASKS[task]
    # Child-only environment. No rustup settings write or implicit toolchain installation.
    env = dict(os.environ, RUSTUP_AUTO_INSTALL="0")
    child = subprocess.Popen([path, *args], cwd=ROOT, env=env,
        stdin=subprocess.PIPE if task == "rustfmt-stdin" else subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    child.communicate(input=data if task == "rustfmt-stdin" else None)
    return child.returncode


def record_system(profile, row):
    # Keep closed numeric/time fields only, never caller diagnostics or command lines.
    observed = {key: row[key] for key in ("time_utc", "system_cpu_percent",
        "available_ram_percent", "available_ram_mib", "total_ram_mib", "commit_used_percent") if key in row}
    profile.setdefault("system_first", observed)
    profile["system_last"] = observed
    profile["system_sample_count"] = profile.get("system_sample_count", 0)+1


def record_job(profile, info):
    profile["job_accounting_observed"] = True
    peak = info["peak_job_private_mib"]
    previous = profile["job_private_peak_mib"]
    profile["job_private_peak_mib"] = peak if previous is None else max(previous, peak)
    observed = {key: info[key] for key in ("active_processes", "job_cpu_seconds",
        "peak_job_private_mib", "peak_job_private_percent") if key in info}
    processes = info.get("owned_processes", [])
    require(len(processes) <= 64, "audit_tool_accounting_budget")
    observed["owned_processes"] = [{key: child[key] for key in
        ("pid", "memory_observed", "working_set_mib", "private_mib") if key in child}
        | {"role": child.get("role") if child.get("role") in
            {"python.exe", "python3.exe", "rustc.exe", "cargo.exe", "conhost.exe", "other-owned", "unavailable"}
            else "other-owned"} for child in processes]
    profile["job_last"] = observed
    if info["active_processes"]:
        profile["job_last_active"] = observed


def run_audit_tool(task, text=None, checkpoint=None):
    profile = {"task": task if isinstance(task, str) and task in TASKS else "unavailable",
        "input_bytes": None, "timeout_seconds": TIMEOUT_SECONDS,
        "output_limits": dict(OUTPUT_LIMITS), "job_private_peak_mib": None,
        "job_accounting_observed": False, "worker_created": False, "job_assigned": False,
        "writer_authorized": False, "owned_tree_empty": None, "cleanup_confirmed": False,
        "logical_cpu_limit": 1, "priority": "BelowNormal", "operation_phase": "input"}
    started = time.monotonic()
    try:
        return _run_audit_tool(task, text, checkpoint, profile)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) else "audit_tool_os_or_subprocess_failure"
        profile["failure_code"] = code if re.fullmatch(r"audit_tool_[a-z_]+|STOP_[A-Z_]+", code) \
            else "audit_tool_failure"
        if not profile["worker_created"]:
            profile["owned_tree_empty"] = True
            profile["no_owned_worker_started"] = True
        error.audit_limits = profile
        raise
    finally:
        profile["elapsed_seconds"] = round(time.monotonic()-started, 4)


def _run_audit_tool(task, text, checkpoint, profile):
    data = payload_for(task, text)
    profile["input_bytes"] = len(data)
    checkpoint = (lambda: None) if checkpoint is None else checkpoint
    require(callable(checkpoint), "audit_tool_checkpoint_scope")
    checkpoint()
    profile["operation_phase"] = "preflight"
    windows = Windows()
    profile.update(job_cpu_hard_cap_machine_percent=windows.cpu_rate/100,
        job_private_limit_mib=windows.memory_limit/1048576)
    row = sample(windows)
    record_system(profile, row)
    hot, reason = decision(row, 0)
    require(reason is None, reason)
    profile["operation_phase"] = "lock"
    ctypes.set_last_error(0)
    mutex = windows.k.CreateMutexW(None, True, "Local\\HwpxAgentP149ReadonlyAuditTools")
    duplicate = ctypes.get_last_error() == 183
    require(mutex, "audit_tool_lock_failed")
    if duplicate:
        windows.k.CloseHandle(mutex)
        raise ValueError("audit_tool_already_running")
    job = process = capture = None
    try:
        profile["operation_phase"] = "job_creation"
        job = windows.job()
        profile["operation_phase"] = "waiting_worker"
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--owned-worker", task],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        profile["worker_created"] = True
        require(windows.k.AssignProcessToJobObject(job, int(process._handle)), "audit_tool_job_assignment_failed")
        profile["job_assigned"] = True
        checkpoint()
        profile["operation_phase"] = "pre_go"
        row = sample(windows)
        record_system(profile, row)
        hot, reason = decision(row, hot)
        require(reason is None, reason)
        # Writer is asynchronous and deadline-bound: a full stdin pipe must not block the supervisor.
        request = b"P149_AUDIT_GO\n"+str(len(data)).encode("ascii")+b"\n"+data
        deadline = time.monotonic()+TIMEOUT_SECONDS
        capture = AuditToolCapture(process, request)
        profile["writer_authorized"] = True
        profile["operation_phase"] = "running"
        while True:
            checkpoint()
            capture.check()
            require(time.monotonic() < deadline, "audit_tool_command_timeout")
            try:
                output, errors = capture.communicate(min(0.25, max(0.001, deadline-time.monotonic())))
                completed = True
            except subprocess.TimeoutExpired:
                capture.check()
                completed = False
            # Fast completion is not permission to skip final resource/Job observation.
            info = windows.accounting(job)
            record_job(profile, info)
            row = sample(windows)
            record_system(profile, row)
            row.update(info)
            hot, reason = decision(row, hot)
            require(reason is None, reason)
            if completed:
                break
        checkpoint()
        result = subprocess.CompletedProcess([task], process.returncode, output, errors)
        result.audit_limits = profile
        return result
    finally:
        cleanup_failed = False
        if job:
            try:
                record_job(profile, windows.accounting(job))
            except (OSError, ValueError, subprocess.SubprocessError):
                profile["pre_cleanup_accounting_unavailable"] = True
        try:
            if job:
                cleanup_failed = not bool(windows.k.TerminateJobObject(job, 1))
            if process and process.poll() is None:
                process.kill()
            if process:
                process.wait(timeout=2)
        except (OSError, ValueError, subprocess.SubprocessError):
            cleanup_failed = True
        try:
            if capture:
                capture.close()
            elif process:
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
            if job:
                deadline = time.monotonic()+2
                while True:
                    info = windows.accounting(job)
                    record_job(profile, info)
                    if info["active_processes"] == 0:
                        profile["owned_tree_empty"] = True
                        break
                    require(time.monotonic() < deadline, "audit_tool_cleanup_timeout")
                    time.sleep(0.05)
        except (OSError, ValueError, subprocess.SubprocessError):
            cleanup_failed = True
        finally:
            if job:
                cleanup_failed = not bool(windows.k.CloseHandle(job)) or cleanup_failed
            cleanup_failed = not bool(windows.k.ReleaseMutex(mutex)) or cleanup_failed
            cleanup_failed = not bool(windows.k.CloseHandle(mutex)) or cleanup_failed
        profile["cleanup_confirmed"] = not cleanup_failed
        require(not cleanup_failed, "audit_tool_cleanup_not_confirmed")


if __name__ == "__main__":
    try:
        require(len(sys.argv) == 3 and sys.argv[1] == "--owned-worker" and sys.argv[2] in TASKS
            and Path.cwd().resolve() == ROOT, "audit_tool_worker_scope")
        sys.exit(worker(sys.argv[2]))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) else "audit_tool_worker_failure"
        code = code if re.fullmatch(r"audit_tool_[a-z_]+|[A-Z_]+", code) else "audit_tool_worker_failure"
        print("P149_AUDIT_ERROR:"+code, file=sys.stderr)
        sys.exit(2)
