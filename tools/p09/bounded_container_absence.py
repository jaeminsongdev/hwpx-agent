"""Read-only, bounded Docker absence batches. No create/exec/remove or raw log files."""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from bounded_process_progress import BoundedProcessCapture, LIMIT
from conservative_maintenance import ROOT, Windows, decision, require

TIMEOUT_SECONDS = 10
MAX_REFERENCES = 32
REFERENCE = re.compile(r"(?:[0-9a-f]{64}|hwpx-p14[68]-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})")


def references_checked(references):
    require(isinstance(references, (list, tuple)) and 1 <= len(references) <= MAX_REFERENCES,
        "absence_reference_scope")
    require(all(isinstance(value, str) and REFERENCE.fullmatch(value) for value in references)
        and len(set(references)) == len(references), "absence_reference_scope")
    return list(references)


def inspect_arguments(docker, references):
    require(isinstance(docker, str) and Path(docker).is_absolute()
        and Path(docker).name.lower() == "docker.exe", "absence_executable_scope")
    # Generic inspect matches any Docker object, as before; do not narrow to --type container.
    return [docker, "inspect", "--format", "{{.Id}}", *references_checked(references)]


def validate_absence(returncode, stdout, stderr, references, error_code):
    references = references_checked(references)
    require(isinstance(returncode, int) and not isinstance(returncode, bool) and returncode != 0
        and isinstance(stdout, str) and stdout == "" and isinstance(stderr, str)
        and len(stderr.encode("utf-8")) <= LIMIT, error_code)
    found = []
    for line in stderr.splitlines():
        match = re.fullmatch(r"Error: No such (?:object|container): (.+)", line, re.IGNORECASE)
        require(match is not None, error_code)
        found.append(match[1])
    require(len(found) == len(references) and len(set(found)) == len(found)
        and set(found) == set(references), error_code)
    return [{"reference": reference, "absent": True} for reference in references]


def worker():
    windows = Windows()
    require(sys.stdin.readline(32) == "P149_ABSENCE_GO\n", "absence_worker_not_authorized")
    member = w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(), None, ctypes.byref(member))
        and member.value, "absence_worker_not_in_job")
    request = sys.stdin.readline(4097)
    require(len(request) <= 4096 and request.endswith("\n"), "absence_request_budget")
    request = json.loads(request)
    require(isinstance(request, dict) and set(request) == {"docker", "references"}, "absence_request_scope")
    args = inspect_arguments(request["docker"], request["references"])
    executable = Path(args[0])
    require(executable.is_file() and not executable.is_symlink() and not executable.is_junction(),
        "absence_executable_missing_or_link")
    return subprocess.call(args, cwd=ROOT, stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)


def observed_sample(windows):
    for attempt in range(6):
        try:
            return windows.sample()
        except ValueError as error:
            if str(error) != "CPU_SAMPLE_INTERVAL_MISSING" or attempt == 5:
                raise
            time.sleep(0.02)


def inspect_absence(docker, references, checkpoint, error_code):
    """Start Docker only after assigning the waiting worker to an aggregate-limited Job."""
    references = references_checked(references)
    inspect_arguments(docker, references)
    request = json.dumps({"docker": docker, "references": references}, ensure_ascii=True) + "\n"
    require(len(request) <= 4096, "absence_request_budget")
    checkpoint()
    windows = Windows()
    hot, reason = decision(observed_sample(windows), 0)
    require(reason is None, reason)
    ctypes.set_last_error(0)
    mutex = windows.k.CreateMutexW(None, True, "Local\\HwpxAgentP149ContainerAbsence")
    duplicate = ctypes.get_last_error() == 183
    require(mutex, "absence_lock_failed")
    if duplicate:
        windows.k.CloseHandle(mutex)
        raise ValueError("absence_already_running")
    job = process = capture = None
    try:
        job = windows.job()
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--owned-worker"],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        require(windows.k.AssignProcessToJobObject(job, int(process._handle)), "absence_job_assignment_failed")
        # No Docker command can start before this assignment and checkpoint.
        checkpoint()
        hot, reason = decision(observed_sample(windows), hot)
        require(reason is None, reason)
        process.stdin.write(("P149_ABSENCE_GO\n" + request).encode("ascii"))
        process.stdin.flush()
        capture = BoundedProcessCapture(process)
        deadline = time.monotonic() + TIMEOUT_SECONDS
        while True:
            checkpoint()
            require(time.monotonic() < deadline, "absence_command_timeout")
            try:
                output, errors = capture.communicate(timeout=min(0.25, deadline-time.monotonic()))
                completed = True
            except subprocess.TimeoutExpired:
                # Check overflow immediately, even if the child is still running.
                capture.progress()
                completed = False
            info = windows.accounting(job)
            row = observed_sample(windows)
            row.update(info)
            hot, reason = decision(row, hot)
            require(reason is None, reason)
            if completed:
                break
        checkpoint()
        return validate_absence(process.returncode, output, errors, references, error_code)
    finally:
        # Only this owned worker/Job is terminated. Docker daemon and containers are untouched.
        cleanup_failed = False
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
                deadline = time.monotonic() + 2
                while windows.accounting(job)["active_processes"]:
                    require(time.monotonic() < deadline, "absence_cleanup_timeout")
                    time.sleep(0.05)
        except (OSError, ValueError, subprocess.SubprocessError):
            cleanup_failed = True
        finally:
            if job:
                cleanup_failed = not bool(windows.k.CloseHandle(job)) or cleanup_failed
            cleanup_failed = not bool(windows.k.ReleaseMutex(mutex)) or cleanup_failed
            cleanup_failed = not bool(windows.k.CloseHandle(mutex)) or cleanup_failed
        require(not cleanup_failed, "absence_cleanup_not_confirmed")


if __name__ == "__main__":
    try:
        require(sys.argv[1:] == ["--owned-worker"] and Path.cwd().resolve() == ROOT,
            "absence_worker_scope")
        sys.exit(worker())
    except (OSError, ValueError, subprocess.SubprocessError):
        # No exception content, command line, path or raw diagnostics are printed.
        sys.exit(2)
