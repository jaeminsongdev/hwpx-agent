"""P149 opt-in single-worker Windows verification. Never launches SQL/native work.

The worker waits for parent Job Object assignment before launching Cargo. Closing
the job kills only this owned tree, not unrelated apps. No raw output is persisted.
"""
import argparse
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from audit_evidence_io import AuditEvidenceReader

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "target/p09-149-conservative"
POLICY = {"profile": "P149_OWNED_WORKLOAD_V4_PARTITIONED_TEST_CODEGEN", "logical_cpu_limit": 1,
    "priority": "BelowNormal", "cargo_jobs": 1, "test_threads": 1,
    "sample_seconds": 0.5, "start_ram_min_percent": 10,
    "start_consecutive_samples": 2, "admission_max_seconds": 3,
    "emergency_cpu_percent": 98, "emergency_cpu_consecutive_samples": 4,
    "stop_ram_min_percent": 8, "stop_commit_used_percent": 95,
    "job_memory_limit_percent": 8, "job_memory_stop_percent": 7,
    "test_debug_info": "line-tables-only", "dev_debug_info": "line-tables-only", "test_opt_level": 0,
    "test_codegen_units": 16,
    "debug_assertions": True, "overflow_checks": True,
    "output_limit_bytes_per_stream": 32768}
TASKS = {
    # Metadata first: type-check library + changed integration test without linking/running its EXE.
    # Dependencies/build scripts/proc macros may still execute; this is not a zero-work dry run.
    "domain-check": ["check", "-p", "domain-ir", "--lib", "--test", "document_graph"],
    "domain-tests": ["test", "-p", "domain-ir", "--test", "document_graph"],
    "formula-tests": ["test", "-p", "hwpx-package", "--test", "document_import_formula_evaluation"],
    "comment-tests": ["test", "-p", "hwpx-agent-cli", "--test", "comment_operation"],
    "product-check": ["check", "-p", "hwpx-agent-cli", "--lib"],
}
SOURCES = ["Cargo.toml", "Cargo.lock", "crates/domain-ir/src/document_graph.rs",
    "crates/domain-ir/tests/document_graph.rs",
    "crates/hwpx-package/src/document_import/fields/semantics/evaluation/source.rs",
    "crates/product-cli/src/comment_operation.rs",
    "crates/product-cli/src/comment_operation/rich_bodies.rs",
    "tools/p09/conservative_maintenance.py", "tools/p09/bounded_process_progress.py",
    "crates/product-cli/src/form_stored_provider/comments.rs",
    "crates/product-cli/src/form_stored_provider/comments/rich_bodies.rs",
    "crates/hwpx-package/src/document_import/structure/review/locations.rs",
    "crates/product-cli/src/form_value_operation/full_document.rs",
    "tools/p09/tests/test_conservative_maintenance.py", "tools/p09/audit_evidence_io.py",
    "tools/p09/tests/test_maintenance_completion.py", "tools/p09/verify_maintenance_completion_light.py",
    "crates/domain-ir/Cargo.toml", "crates/hwpx-package/Cargo.toml",
    "crates/hwpx-package/tests/document_import_formula_evaluation.rs",
    "crates/hwpx-package/tests/support/document_import_formula_evaluation_fixture.rs",
    "crates/hwpx-package/tests/support/document_import_settings_inputs.rs",
    "crates/hwpx-package/tests/support/document_import_field_fixture.rs",
    "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json",
    "crates/product-cli/Cargo.toml", "crates/product-cli/src/lib.rs",
    "crates/product-cli/tests/comment_operation.rs", "crates/product-cli/tests/comment_operation/rich_bodies.rs"]

# Closed diagnostics only: never retain dependency names outside this reviewed set,
# versions, paths, command lines, or arbitrary text emitted by Cargo/build scripts.
CARGO_DIAGNOSTIC_PACKAGES = frozenset({"domain-ir", "hwpx-package", "hwpx-agent-cli",
    "serde", "serde_core", "serde_derive", "serde_json", "thiserror", "thiserror-impl",
    "sha2", "digest", "crypto-common", "block-buffer", "unicode-normalization"})


def require(ok, code):
    if not ok:
        raise ValueError(code)


def cargo_announcement_snapshot(capture):
    # This is the last COMPLETE Cargo-style stderr announcement, not proof of the
    # current rustc crate/LLVM/link stage. No extra process or filesystem read.
    with capture.lock:
        raw = bytes(capture.buffers["stderr"])
    require(len(raw) <= POLICY["output_limit_bytes_per_stream"], "CARGO_DIAGNOSTIC_BUFFER_LIMIT")
    latest = None
    for line in raw.split(b"\n")[:-1]:
        match = re.fullmatch(rb"\s*(Compiling|Checking) ([A-Za-z0-9_-]{1,64}) "
            rb"v[0-9][A-Za-z0-9.+_-]{0,63}(?: \([^\r\n]*\))?\r?", line)
        if match:
            package = match[2].decode("ascii")
            latest = {"stage": match[1].decode("ascii").lower(),
                "package": package if package in CARGO_DIAGNOSTIC_PACKAGES else None}
        elif re.fullmatch(rb"\s*Finished [^\r\n]+\r?", line):
            latest = {"stage": "build_finished", "package": None}
    return {"source": "last_complete_cargo_style_stderr_announcement",
        "process_or_compiler_phase_attribution_verified": False, "announcement": latest}


def decision(row, hot):
    cpu, ram, commit = row["system_cpu_percent"], row["available_ram_percent"], row["commit_used_percent"]
    require(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        and 0 <= v <= 100 for v in (cpu, ram, commit)),
        "STOP_RESOURCE_OBSERVATION_INVALID")
    hot = hot + 1 if cpu >= POLICY["emergency_cpu_percent"] else 0
    if ram < POLICY["stop_ram_min_percent"]:
        return hot, "STOP_LOW_AVAILABLE_RAM"
    if commit >= POLICY["stop_commit_used_percent"]:
        return hot, "STOP_SYSTEM_COMMIT_PRESSURE"
    if hot >= POLICY["emergency_cpu_consecutive_samples"]:
        return hot, "STOP_SUSTAINED_SYSTEM_CPU"
    owned = row.get("peak_job_private_percent", 0)
    require(isinstance(owned, (int, float)) and not isinstance(owned, bool)
        and math.isfinite(owned) and 0 <= owned <= 100, "STOP_RESOURCE_OBSERVATION_INVALID")
    if owned >= POLICY["job_memory_stop_percent"]:
        return hot, "STOP_OWNED_JOB_MEMORY_BUDGET"
    return hot, None


def admitted_count(row, count):
    # Normal background CPU load does not block a small owned job.
    return count + 1 if row["available_ram_percent"] >= POLICY["start_ram_min_percent"] else 0


class Memory(ctypes.Structure):
    _fields_ = [("length", w.DWORD), ("load", w.DWORD)] + [(n, ctypes.c_uint64) for n in
        ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]


class SystemInfo(ctypes.Structure):
    _fields_ = [("architecture", w.WORD), ("reserved", w.WORD), ("page_size", w.DWORD),
        ("minimum_address", ctypes.c_void_p), ("maximum_address", ctypes.c_void_p),
        ("active_mask", ctypes.c_size_t), ("processors", w.DWORD), ("processor_type", w.DWORD),
        ("allocation_granularity", w.DWORD), ("processor_level", w.WORD), ("processor_revision", w.WORD)]


class BasicLimit(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64), ("flags", w.DWORD),
        ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t), ("active_limit", w.DWORD),
        ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("read_ops", "write_ops", "other_ops", "read", "write", "other")]


class ExtendedLimit(ctypes.Structure):
    _fields_ = [("basic", BasicLimit), ("io", IoCounters), ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t), ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int64) for n in ("user", "kernel", "period_user", "period_kernel")] + [
        (n, w.DWORD) for n in ("page_faults", "total_processes", "active_processes", "terminated_processes")]


class CpuRate(ctypes.Structure):
    _fields_ = [("flags", w.DWORD), ("rate", w.DWORD)]


class ProcessList(ctypes.Structure):
    _fields_ = [("assigned", w.DWORD), ("count", w.DWORD), ("pids", ctypes.c_size_t * 64)]


class ProcessMemory(ctypes.Structure):
    _fields_ = [("size", w.DWORD), ("faults", w.DWORD)] + [(n, ctypes.c_size_t) for n in
        ("peak_ws", "ws", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]


class Windows:
    def __init__(self):
        require(os.name == "nt", "WINDOWS_ONLY")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, args, result in [
            ("GetCurrentProcess", [], w.HANDLE), ("SetPriorityClass", [w.HANDLE, w.DWORD], w.BOOL),
            ("SetProcessAffinityMask", [w.HANDLE, ctypes.c_size_t], w.BOOL),
            ("GetProcessAffinityMask", [w.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)], w.BOOL),
            ("GetPriorityClass", [w.HANDLE], w.DWORD), ("GetSystemTimes", [ctypes.c_void_p] * 3, w.BOOL),
            ("GetSystemInfo", [ctypes.POINTER(SystemInfo)], None),
            ("GlobalMemoryStatusEx", [ctypes.POINTER(Memory)], w.BOOL),
            ("CreateJobObjectW", [ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            ("SetInformationJobObject", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            ("QueryInformationJobObject", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            ("AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL),
            ("IsProcessInJob", [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
            ("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL),
            ("OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE), ("CloseHandle", [w.HANDLE], w.BOOL),
            ("K32GetProcessMemoryInfo", [w.HANDLE, ctypes.POINTER(ProcessMemory), w.DWORD], w.BOOL),
            ("QueryFullProcessImageNameW", [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)], w.BOOL),
            ("CreateMutexW", [ctypes.c_void_p, w.BOOL, w.LPCWSTR], w.HANDLE),
            ("ReleaseMutex", [w.HANDLE], w.BOOL),
        ]:
            fn = getattr(self.k, name)
            fn.argtypes, fn.restype = args, result
        handle = self.k.GetCurrentProcess()
        allowed, system = ctypes.c_size_t(), ctypes.c_size_t()
        require(self.k.GetProcessAffinityMask(handle, ctypes.byref(allowed), ctypes.byref(system)), "AFFINITY_READ_FAILED")
        self.mask = allowed.value & -allowed.value
        require(self.mask != 0 and self.k.SetProcessAffinityMask(handle, self.mask)
            and self.k.SetPriorityClass(handle, 0x4000), "RESOURCE_LIMIT_NOT_APPLIED")
        self.last = self.times()
        self.processors = os.cpu_count()
        require(isinstance(self.processors, int) and 1 <= self.processors <= 64, "PROCESSOR_GROUP_UNSUPPORTED")
        mem = Memory()
        mem.length = ctypes.sizeof(mem)
        require(self.k.GlobalMemoryStatusEx(ctypes.byref(mem)) and mem.total > 0, "RAM_SAMPLE_FAILED")
        self.total_ram = mem.total
        system = SystemInfo()
        self.k.GetSystemInfo(ctypes.byref(system))
        require(system.page_size > 0, "SYSTEM_PAGE_SIZE_INVALID")
        self.memory_limit = (self.total_ram * POLICY["job_memory_limit_percent"] // 100
            // system.page_size * system.page_size)
        self.cpu_rate = max(1, 10000 * POLICY["logical_cpu_limit"] // self.processors)

    def times(self):
        values = [ctypes.c_uint64() for _ in range(3)]
        require(self.k.GetSystemTimes(*(ctypes.byref(v) for v in values)), "CPU_SAMPLE_FAILED")
        return tuple(v.value for v in values)

    def sample(self):
        mem = Memory()
        mem.length = ctypes.sizeof(mem)
        require(self.k.GlobalMemoryStatusEx(ctypes.byref(mem)), "RAM_SAMPLE_FAILED")
        require(mem.total == self.total_ram and mem.page_total > 0
            and mem.available <= mem.total and mem.page_available <= mem.page_total, "RAM_SAMPLE_INVALID")
        now = self.times()
        idle = now[0] - self.last[0]
        total = now[1] + now[2] - self.last[1] - self.last[2]
        self.last = now
        require(total > 0, "CPU_SAMPLE_INTERVAL_MISSING")
        return {"time_utc": datetime.now(timezone.utc).isoformat(),
            "system_cpu_percent": round(100 * (total - idle) / total, 2),
            "available_ram_mib": round(mem.available / 1048576, 2),
            "total_ram_mib": round(mem.total / 1048576, 2),
            "available_ram_percent": 100 * mem.available / mem.total,
            "commit_used_percent": 100 * (mem.page_total - mem.page_available) / mem.page_total}

    def job(self):
        handle = self.k.CreateJobObjectW(None, None)
        require(handle, "OWNED_JOB_CREATE_FAILED")
        limits = ExtendedLimit()
        # No breakaway; inherited one-CPU/priority limits plus aggregate private-memory ceiling.
        limits.basic.flags = 0x2000 | 0x200 | 0x10 | 0x20 | 0x8
        limits.basic.active_limit = 16
        limits.basic.affinity, limits.basic.priority = self.mask, 0x4000
        limits.job_memory = self.memory_limit
        if not self.k.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.k.CloseHandle(handle)
            raise ValueError("OWNED_JOB_LIMIT_FAILED")
        rate = CpuRate(0x1 | 0x4, self.cpu_rate)  # ENABLE | HARD_CAP, aggregate job CPU quota.
        if not self.k.SetInformationJobObject(handle, 15, ctypes.byref(rate), ctypes.sizeof(rate)):
            self.k.CloseHandle(handle)
            raise ValueError("OWNED_JOB_CPU_RATE_FAILED")
        return handle

    def verify_job_limits(self, job):
        limits, rate = ExtendedLimit(), CpuRate()
        require(self.k.QueryInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits), None)
            and self.k.QueryInformationJobObject(job, 15, ctypes.byref(rate), ctypes.sizeof(rate), None),
            "OWNED_LIMIT_READBACK_FAILED")
        require(limits.job_memory == self.memory_limit and limits.basic.affinity == self.mask
            and limits.basic.priority == 0x4000 and limits.basic.active_limit == 16
            and limits.basic.flags & 0x2238 == 0x2238 and limits.basic.flags & 0x1800 == 0
            and rate.flags == 5 and rate.rate == self.cpu_rate, "OWNED_LIMIT_READBACK_MISMATCH")
        return {"verified": True, "job_private_limit_mib": limits.job_memory / 1048576,
            "cpu_hard_cap_machine_percent": rate.rate / 100, "affinity_mask": limits.basic.affinity,
            "priority_class": limits.basic.priority, "active_process_limit": limits.basic.active_limit,
            "kill_on_close": True, "breakaway_disabled": True}

    def accounting(self, job):
        info = Accounting()
        require(self.k.QueryInformationJobObject(job, 1, ctypes.byref(info), ctypes.sizeof(info), None), "JOB_OBSERVATION_FAILED")
        limits = ExtendedLimit()
        require(self.k.QueryInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits), None), "JOB_MEMORY_OBSERVATION_FAILED")
        return {"active_processes": info.active_processes,
            "job_cpu_seconds": round((info.user + info.kernel) / 10_000_000, 3),
            "peak_job_private_mib": round(limits.peak_job_memory / 1048576, 2),
            "peak_job_private_percent": 100 * limits.peak_job_memory / self.total_ram,
            "owned_processes": self.owned_processes(job)}

    def owned_processes(self, job):
        listing = ProcessList()
        require(self.k.QueryInformationJobObject(job, 3, ctypes.byref(listing), ctypes.sizeof(listing), None)
            and listing.count <= 64, "OWNED_PROCESS_LIST_FAILED")
        result = []
        for pid in listing.pids[:listing.count]:
            handle = self.k.OpenProcess(0x410, False, pid)
            if not handle:
                continue  # May have exited since the Job snapshot, never count as zero RAM.
            try:
                member = w.BOOL()
                if not self.k.IsProcessInJob(handle, job, ctypes.byref(member)) or not member.value:
                    continue
                image, length = ctypes.create_unicode_buffer(32768), w.DWORD(32768)
                memory = ProcessMemory()
                memory.size = ctypes.sizeof(memory)
                observed = bool(self.k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length))
                    and self.k.K32GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.size))
                role = Path(image.value).name.lower() if observed else "unavailable"
                if role not in {"rustc.exe", "cargo.exe", "python.exe", "python3.exe", "conhost.exe"}:
                    role = "other-owned" if observed else role
                row = {"pid": int(pid), "role": role, "memory_observed": observed}
                if observed:
                    row.update(working_set_mib=round(memory.ws / 1048576, 2), private_mib=round(memory.private / 1048576, 2))
                result.append(row)
            finally:
                self.k.CloseHandle(handle)
        return result


def worker(task):
    windows = Windows()
    require(sys.stdin.readline() == "P149_GO\n", "WORKER_NOT_AUTHORIZED")
    member = w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(), None, ctypes.byref(member)) and member.value,
        "WORKER_NOT_IN_JOB")
    cargo = shutil.which("cargo")
    require(cargo, "CARGO_UNAVAILABLE")
    args = [cargo, *TASKS[task], "--locked", "--offline", "--jobs", "1", "--color=never", "--target-dir", str(TARGET)]
    if task.endswith("tests"):
        args += ["--", "--test-threads=1"]
    env = dict(os.environ, CARGO_BUILD_JOBS="1", CARGO_PROFILE_TEST_OPT_LEVEL=str(POLICY["test_opt_level"]),
        CARGO_PROFILE_DEV_DEBUG=POLICY["dev_debug_info"],
        CARGO_PROFILE_DEV_DEBUG_ASSERTIONS="true", CARGO_PROFILE_DEV_OVERFLOW_CHECKS="true",
        CARGO_PROFILE_DEV_CODEGEN_UNITS="1",
        CARGO_PROFILE_TEST_DEBUG=POLICY["test_debug_info"],
        CARGO_PROFILE_TEST_DEBUG_ASSERTIONS="true", CARGO_PROFILE_TEST_OVERFLOW_CHECKS="true",
        CARGO_PROFILE_TEST_CODEGEN_UNITS=str(POLICY["test_codegen_units"]),
        RUST_TEST_THREADS="1", RUSTUP_AUTO_INSTALL="0")
    return subprocess.call(args, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)


def pins(checkpoint=None):
    reader = AuditEvidenceReader(ROOT, (lambda: None) if checkpoint is None else checkpoint)
    try:
        return [reader.pin(name) for name in SOURCES]
    except ValueError as error:
        if str(error) == "sql_source_link_or_missing":
            raise ValueError("SOURCE_LINK_OR_MISSING") from None
        raise


def run(task, receipt, maximum_seconds):
    from bounded_process_progress import BoundedProcessCapture
    windows = Windows()  # Apply limits BEFORE admission and source hashing.
    ctypes.set_last_error(0)
    mutex = windows.k.CreateMutexW(None, True, "Local\\HwpxAgentP149ConservativeMaintenance")
    duplicate = ctypes.get_last_error() == 183
    require(mutex, "MAINTENANCE_LOCK_FAILED")
    if duplicate:
        windows.k.CloseHandle(mutex)
        raise ValueError("MAINTENANCE_ALREADY_RUNNING")
    job = process = capture = None
    result = {"schema_version": "hwpx-agent.p09-conservative-maintenance/v1", "task": task,
        "policy": POLICY, "maximum_seconds": maximum_seconds, "state": "NOT_RUN",
        "heavy_work_started": False, "samples": [], "source_freeze": [],
        "product_complete": False, "P09_gate": "OPEN", "native_or_SQL_run": False,
        "owned_tree_empty": False, "cleanup_confirmed": False,
        "worker_created": False, "job_assigned": False, "writer_authorized": False,
        "operation_phase": "admission", "exit_code": None, "stop_reason": None,
        "last_cargo_announcement": None, "cargo_announcement_at_cleanup": None,
        "resolved_owned_limits": {"total_ram_mib": round(windows.total_ram / 1048576, 2),
            "job_private_memory_limit_mib": round(windows.memory_limit / 1048576, 2),
            "machine_logical_processors": windows.processors,
            "job_cpu_hard_cap_machine_percent": windows.cpu_rate / 100}}
    started = time.monotonic()
    hot = count = 0
    last_observation = started
    def observe(force=True):
        nonlocal hot, last_observation
        now = time.monotonic()
        if not force and now-last_observation < POLICY["sample_seconds"]:
            return
        for attempt in range(6):
            try:
                row = dict(windows.sample())
                break
            except ValueError as error:
                if str(error) != "CPU_SAMPLE_INTERVAL_MISSING" or attempt == 5:
                    raise
                time.sleep(0.02)
        if job:
            row.update(windows.accounting(job))
            previous = next((s for s in reversed(result["samples"]) if "job_cpu_seconds" in s), None)
            row["job_elapsed_seconds"] = time.monotonic()-started
            if previous:
                wall = row["job_elapsed_seconds"]-previous["job_elapsed_seconds"]
                require(wall > 0, "STOP_RESOURCE_OBSERVATION_INVALID")
                row["owned_job_cpu_machine_percent"] = max(0,
                    100*(row["job_cpu_seconds"]-previous["job_cpu_seconds"])/wall/windows.processors)
        if capture:
            row["cargo_announcement"] = cargo_announcement_snapshot(capture)
            result["last_cargo_announcement"] = row["cargo_announcement"]
        result["samples"].append(row)
        last_observation = time.monotonic()
        hot, reason = decision(row, hot)
        require(not reason, reason)
        return row
    try:
        while time.monotonic() - started < POLICY["admission_max_seconds"]:
            time.sleep(POLICY["sample_seconds"])
            row = observe()
            require(row["system_cpu_percent"] < POLICY["emergency_cpu_percent"], "DEFERRED_ALREADY_SATURATED_SYSTEM")
            count = admitted_count(row, count)
            if count >= POLICY["start_consecutive_samples"]:
                break
        require(count >= POLICY["start_consecutive_samples"], "DEFERRED_STABLE_RESOURCE_WINDOW")
        result["operation_phase"] = "source_freeze"
        result["source_freeze"] = pins(lambda: observe(False))
        result["operation_phase"] = "job_creation"
        job = windows.job()
        result["owned_limits_readback"] = windows.verify_job_limits(job)
        result["operation_phase"] = "waiting_worker"
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--owned-worker", "--task", task],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
        result["worker_created"] = True
        handle = windows.k.OpenProcess(0x101, False, process.pid)  # SET_QUOTA | TERMINATE
        try:
            require(handle and windows.k.AssignProcessToJobObject(job, handle), "OWNED_JOB_ASSIGN_FAILED")
            result["job_assigned"] = True
        finally:
            if handle:
                require(windows.k.CloseHandle(handle), "OWNED_PROCESS_HANDLE_CLOSE_FAILED")
        result["operation_phase"] = "pre_go"
        observe()
        process.stdin.write(b"P149_GO\n")
        process.stdin.flush()
        result["writer_authorized"] = True
        capture = BoundedProcessCapture(process)  # Closes input and bounds each output pipe.
        result["heavy_work_started"] = True
        result["operation_phase"] = "running"
        deadline = time.monotonic() + maximum_seconds
        while True:
            require(time.monotonic() < deadline, "STOP_DURATION_LIMIT")
            try:
                output, errors = capture.communicate(timeout=min(POLICY["sample_seconds"],
                    max(0.001, deadline-time.monotonic())))
                completed = True
            except subprocess.TimeoutExpired:
                capture.progress()
                completed = False
            observe()
            require(time.monotonic() < deadline, "STOP_DURATION_LIMIT")
            if completed:
                break
        result["exit_code"] = process.returncode
        result["compiler_error_codes"] = sorted(set(re.findall(r"(?m)^error\[(E[0-9]{4})\]:", errors)))[:32]
        locations = re.findall(r"(?m)^\s*-->\s*(crates/[A-Za-z0-9_/-]+\.rs):([0-9]+):([0-9]+)",
            errors.replace("\\", "/"))
        result["compiler_diagnostic_locations"] = [{"path": path, "line": int(line), "column": int(column)}
            for path, line, column in locations[:32]]
        require(process.returncode == 0, "OWNED_COMMAND_FAILED")
        result["operation_phase"] = "final_source_freeze"
        require(result["source_freeze"] == pins(lambda: observe(False)), "SOURCE_DRIFT_AFTER_RUN")
        observe()
        if task.endswith("tests"):
            matches = re.findall(r"test result: ok\. (\d+) passed; 0 failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;", output)
            require(len(matches) == 1 and int(matches[0][0]) > 0 and int(matches[0][1]) == 0, "TEST_SUMMARY_NOT_ACCEPTED")
            result["tests_passed"] = int(matches[0][0])
        result["state"] = "PASS_SCOPED_NOT_GATE"
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Never persist exception text from tools/paths/output; only our closed error codes.
        code = str(error) if isinstance(error, ValueError) else "OWNED_RUNNER_FAILURE"
        result["stop_reason"] = code if re.fullmatch(r"[A-Z_]+", code or "") else "OWNED_RUNNER_FAILURE"
        result["state"] = "STOPPED_NOT_ACCEPTED" if result["heavy_work_started"] else "DEFERRED_NOT_STARTED"
    finally:
        cleanup_failed = False
        try:
            if job:
                cleanup_failed = not bool(windows.k.TerminateJobObject(job, 1))
            if process:
                if process.poll() is None:
                    process.kill()  # Exact owned waiting worker, including failed assignment.
                process.wait(timeout=5)
        except (ValueError, OSError, subprocess.SubprocessError):
            cleanup_failed = True
        try:
            if capture:
                capture.close()
                result["cargo_announcement_at_cleanup"] = cargo_announcement_snapshot(capture)
            elif process:
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
            if job:
                deadline = time.monotonic() + 5
                while True:
                    info = windows.accounting(job)
                    result["job_final"] = info
                    if info["active_processes"] == 0:
                        result["owned_tree_empty"] = True
                        break
                    require(time.monotonic() < deadline, "OWNED_CLEANUP_TIMEOUT")
                    time.sleep(0.1)
            else:
                result["owned_tree_empty"] = process is None or process.poll() is not None
        except (ValueError, OSError, subprocess.SubprocessError):
            cleanup_failed = True
        finally:
            if job:
                cleanup_failed = not bool(windows.k.CloseHandle(job)) or cleanup_failed
            cleanup_failed = not bool(windows.k.ReleaseMutex(mutex)) or cleanup_failed
            cleanup_failed = not bool(windows.k.CloseHandle(mutex)) or cleanup_failed
        result["cleanup_confirmed"] = not cleanup_failed
        if cleanup_failed:
            result["stop_reason"] = "OWNED_CLEANUP_NOT_CONFIRMED"
            result["state"] = "STOPPED_NOT_ACCEPTED"
        result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        with receipt.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        print(json.dumps({k: result.get(k) for k in ("state", "task", "stop_reason", "tests_passed", "elapsed_seconds", "owned_tree_empty")}))
    return 0 if result["state"] == "PASS_SCOPED_NOT_GATE" else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=TASKS, required=True)
    parser.add_argument("--receipt")
    parser.add_argument("--maximum-seconds", type=int, default=180)
    parser.add_argument("--owned-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    require(Path.cwd().resolve() == ROOT, "WRONG_REPOSITORY")
    if args.owned_worker:
        return worker(args.task)
    require(args.receipt is not None and 30 <= args.maximum_seconds <= 300, "RUN_SCOPE_INVALID")
    receipt = (ROOT / args.receipt).resolve()
    require(receipt.parent == ROOT / "implementation/p09/evidence"
        and re.fullmatch(r"p09-149-maintenance-run[0-9]{2}\.v1\.json", receipt.name)
        and not receipt.exists(), "FRESH_RECEIPT_REQUIRED")
    return run(args.task, receipt, args.maximum_seconds)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError):
        print("P149_NOT_STARTED_SCOPE_OR_RESOURCE_SETUP_FAILURE")
        sys.exit(2)
