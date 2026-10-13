"""Owned Windows waiting-worker launcher; never a SQL/container qualification.

검증 대상은 Job 할당/상한 readback/GO 직전 checkpoint 이후에만 시작한다.
stdin의 GO 줄은 단일 byte read로 소비해 SQL payload를 미리 읽지 않는다.
"""
import ctypes
import copy
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time

from conservative_maintenance import ROOT, POLICY, require

TOKEN = "P149_SQL_JOB_GO"
MAX_ARGUMENT_BYTES = 24000


class OwnedSQLJobFailure(ValueError):
    """Ownership/resource/cleanup faults must not become optional observation failures."""


def owned_failure(error):
    code = str(error) if isinstance(error, ValueError) else "OWNED_SQL_OPERATION_FAILED"
    if not re.fullmatch(r"OWNED_[A-Z_]+|STOP_[A-Z_]+|DEFERRED_ALREADY_SATURATED_SYSTEM|resource_stop|adapter_total_time_limit", code):
        code = "OWNED_SQL_OPERATION_FAILED"
    result = OwnedSQLJobFailure(code)
    if hasattr(error, "owned_sql_job_profile"):
        result.owned_sql_job_profile = error.owned_sql_job_profile
    return result


def record_owned_jobs(receipt, profiles):
    rows = receipt.setdefault("owned_host_job_profiles", [])
    require(isinstance(rows, list) and len(rows)+len(profiles) <= 512, "OWNED_SQL_RECEIPT_PROFILE_BUDGET")
    rows.extend(profiles)


def factory_require(ok, code):
    if not ok:
        raise OwnedSQLJobFailure(code)


class ObservedOwnedSQLJobProcess(OwnedSQLJobFailure):
    pass


def validate_arguments(args, allowed_executables, cwd):
    require(isinstance(args, (list, tuple)) and 1 <= len(args) <= 64
        and all(isinstance(arg, str) and "\0" not in arg for arg in args), "OWNED_SQL_ARGUMENT_SCOPE")
    try:
        require(sum(len(arg.encode("utf-16-le")) for arg in args) <= MAX_ARGUMENT_BYTES,
            "OWNED_SQL_ARGUMENT_BUDGET")
    except UnicodeError:
        raise ValueError("OWNED_SQL_ARGUMENT_ENCODING") from None
    require(isinstance(allowed_executables, (list, tuple)) and 1 <= len(allowed_executables) <= 4
        and all(isinstance(name, str) for name in allowed_executables),
        "OWNED_SQL_EXECUTABLE_SCOPE")
    executable = Path(args[0])
    require(executable.is_absolute() and executable.is_file() and not executable.is_symlink()
        and not executable.is_junction() and executable.resolve() in
        {Path(name).resolve() for name in allowed_executables}, "OWNED_SQL_EXECUTABLE_NOT_ALLOWLISTED")
    require(Path(cwd).resolve() == ROOT.resolve(), "OWNED_SQL_WRONG_ROOT")


class OwnedSQLJobProcess:
    """Popen-like pipes and lifecycle, with explicitly checked own-tree teardown.

    Caller drains bounded pipes, polls observe(), and always calls close().
    Docker daemon/WSL/container processes are not members of this host Job.
    """
    def __init__(self, args, *, windows, allowed_executables, cwd, checkpoint, env=None):
        validate_arguments(args, allowed_executables, cwd)
        require(callable(checkpoint), "OWNED_SQL_CHECKPOINT_REQUIRED")
        launcher_args = [sys.executable, str(Path(__file__).resolve()), "--worker",
            json.dumps(list(args), ensure_ascii=False)]
        require(len(subprocess.list2cmdline(launcher_args).encode("utf-16-le")) <= 60000,
            "OWNED_SQL_LAUNCHER_ARGUMENT_BUDGET")
        self.windows, self.checkpoint = windows, checkpoint
        self.job, self.process, self.closed = None, None, False
        self.profile = {"worker_created": False, "job_assigned": False, "limits_readback": None,
            "target_authorized": False, "last_job_accounting": None,
            "owned_tree_empty": None, "cleanup_confirmed": False, "job_handle_closed": False}
        try:
            checkpoint()
            self.job = windows.job()
            self.profile["limits_readback"] = windows.verify_job_limits(self.job)
            require(self.profile["limits_readback"]["verified"], "OWNED_SQL_LIMITS_NOT_VERIFIED")
            self.process = subprocess.Popen(launcher_args, cwd=cwd, env=env, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            self.profile["worker_created"] = True
            require(windows.k.AssignProcessToJobObject(self.job, int(self.process._handle)), "OWNED_SQL_ASSIGN_FAILED")
            member = ctypes.c_int()
            require(windows.k.IsProcessInJob(int(self.process._handle), self.job, ctypes.byref(member))
                and member.value, "OWNED_SQL_MEMBERSHIP_NOT_VERIFIED")
            self.profile["job_assigned"] = True
            checkpoint()
            self.observe()
            require(self.process.stdin.write(TOKEN + "\n") == len(TOKEN)+1, "OWNED_SQL_GO_WRITE_FAILED")
            self.process.stdin.flush()
            self.profile["target_authorized"] = True
        except BaseException as error:
            try:
                self.close()
            except BaseException as cleanup_error:
                cleanup_error.owned_sql_job_profile = dict(self.profile)
                raise cleanup_error from None
            else:
                error.owned_sql_job_profile = dict(self.profile)
            raise

    @property
    def stdin(self):
        return self.process.stdin

    @property
    def stdout(self):
        return self.process.stdout

    @property
    def stderr(self):
        return self.process.stderr

    @property
    def pid(self):
        return self.process.pid

    @property
    def _handle(self):
        return self.process._handle

    @property
    def returncode(self):
        return self.process.returncode

    def poll(self):
        return self.process.poll()

    def wait(self, timeout=None):
        return self.process.wait(timeout=timeout)

    def observe(self):
        self.checkpoint()
        require(self.job is not None and not self.closed, "OWNED_SQL_JOB_CLOSED")
        info = self.windows.accounting(self.job)
        self.profile["last_job_accounting"] = info
        peak = info["peak_job_private_percent"]
        require(isinstance(peak, (int, float)) and not isinstance(peak, bool)
            and 0 <= peak <= 100, "OWNED_SQL_JOB_OBSERVATION_INVALID")
        require(peak < POLICY["job_memory_stop_percent"], "STOP_OWNED_JOB_MEMORY_BUDGET")
        return info

    def kill(self):
        require(self.job is not None and not self.closed
            and self.windows.k.TerminateJobObject(self.job, 1), "OWNED_SQL_TERMINATE_FAILED")

    def close(self):
        if self.closed:
            require(self.profile["cleanup_confirmed"], "OWNED_SQL_PREVIOUS_CLEANUP_FAILED")
            return
        failures = []
        try:
            if self.job is not None:
                if not self.windows.k.TerminateJobObject(self.job, 1):
                    failures.append("OWNED_SQL_TERMINATE_FAILED")
            if self.process is not None:
                try:
                    # Assignment may have failed; only the exact waiting worker is killed here.
                    if self.process.poll() is None:
                        self.process.kill()
                    self.process.wait(timeout=2)
                except (OSError, subprocess.SubprocessError):
                    failures.append("OWNED_SQL_WORKER_WAIT_FAILED")
                for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                    try:
                        stream.close()
                    except (OSError, ValueError):
                        failures.append("OWNED_SQL_PIPE_CLOSE_FAILED")
            if self.job is not None:
                try:
                    deadline = time.monotonic() + 2
                    info = self.windows.accounting(self.job)
                    while info["active_processes"] and time.monotonic() < deadline:
                        time.sleep(0.02)
                        info = self.windows.accounting(self.job)
                    self.profile["last_job_accounting"] = info
                    self.profile["owned_tree_empty"] = info["active_processes"] == 0
                    if not self.profile["owned_tree_empty"]:
                        failures.append("OWNED_SQL_TREE_NOT_EMPTY")
                except (OSError, ValueError):
                    failures.append("OWNED_SQL_CLEANUP_OBSERVATION_FAILED")
            else:
                self.profile["owned_tree_empty"] = self.process is None
        finally:
            if self.job is not None:
                self.profile["job_handle_closed"] = bool(self.windows.k.CloseHandle(self.job))
                if not self.profile["job_handle_closed"]:
                    failures.append("OWNED_SQL_JOB_CLOSE_FAILED")
            else:
                self.profile["job_handle_closed"] = True
            self.closed = True
            self.profile["cleanup_confirmed"] = not failures and self.profile["owned_tree_empty"] is True
        require(self.profile["cleanup_confirmed"], failures[0] if failures else "OWNED_SQL_CLEANUP_FAILED")


class ObservedOwnedSQLJobProcess(OwnedSQLJobProcess):
    def observe(self):
        try:
            return super().observe()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise owned_failure(error) from None

    def close(self):
        try:
            return super().close()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise owned_failure(error) from None


class OwnedSQLJobFactory:
    """Primary7% plus one simultaneous observation1%; same one-CPU affinity."""
    def __init__(self, *, windows, allowed_executables, checkpoint, record):
        factory_require(callable(checkpoint) and callable(record), "OWNED_SQL_FACTORY_CALLBACK_SCOPE")
        self.windows, self.allowed_executables = windows, allowed_executables
        self.checkpoint, self.record = checkpoint, record
        self.processes, self.closed, self.failure = [], False, None

    def __call__(self, args, *, cwd, stdin, stdout, stderr, text, encoding, errors, creationflags, env=None):
        factory_require(not self.closed and stdin == stdout == stderr == subprocess.PIPE
            and text is True and encoding == "utf-8" and errors == "replace"
            and creationflags == subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS,
            "OWNED_SQL_FACTORY_PIPE_SCOPE")
        factory_require(len(self.processes) < 32, "OWNED_SQL_FACTORY_PROCESS_BUDGET")
        factory_require(not any(not child.closed for child in self.processes[1:]), "OWNED_SQL_OBSERVATION_OVERLAP")
        windows = copy.copy(self.windows)
        share = 7 if not self.processes else 1
        windows.memory_limit = self.windows.memory_limit * share // 8 // 65536 * 65536
        factory_require(windows.memory_limit > 0, "OWNED_SQL_FACTORY_MEMORY_BUDGET")
        try:
            child = ObservedOwnedSQLJobProcess(args, windows=windows, allowed_executables=self.allowed_executables,
                cwd=cwd, checkpoint=self.checkpoint, env=env)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            if hasattr(error, "owned_sql_job_profile"):
                try:
                    self.record([dict(error.owned_sql_job_profile)])
                except (OSError, ValueError) as record_error:
                    raise owned_failure(record_error) from None
            raise owned_failure(error) from None
        self.processes.append(child)
        return child

    def close(self):
        if self.closed:
            if self.failure is not None:
                raise self.failure
            return
        failure = None
        for child in reversed(self.processes):
            try:
                child.close()
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                failure = failure or owned_failure(error)
        self.closed = True
        try:
            self.record([dict(child.profile) for child in self.processes])
        except (OSError, ValueError) as error:
            failure = failure or owned_failure(error)
        if failure is not None:
            self.failure = failure
            raise failure


def worker(args):
    require(os.name == "nt" and isinstance(args, list) and 1 <= len(args) <= 64
        and all(isinstance(arg, str) and "\0" not in arg for arg in args), "OWNED_SQL_WORKER_SCOPE")
    # Do not use sys.stdin.readline(): buffered read-ahead would steal SQL stdin bytes.
    line = bytearray()
    for _ in range(len(TOKEN)+2):
        byte = os.read(sys.stdin.fileno(), 1)
        require(byte, "OWNED_SQL_WORKER_NOT_AUTHORIZED")
        line.extend(byte)
        if byte == b"\n":
            break
    require(bytes(line) in {(TOKEN+"\n").encode(), (TOKEN+"\r\n").encode()},
        "OWNED_SQL_WORKER_NOT_AUTHORIZED")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    kernel.IsProcessInJob.restype = ctypes.c_int
    member = ctypes.c_int()
    require(kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(member)) and member.value,
        "OWNED_SQL_WORKER_OUTSIDE_JOB")
    child = subprocess.Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    return child.wait()


if __name__ == "__main__":
    try:
        require(len(sys.argv) == 3 and sys.argv[1] == "--worker", "OWNED_SQL_WORKER_ARGUMENTS")
        raise SystemExit(worker(json.loads(sys.argv[2])))
    except (OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit(125) from None
