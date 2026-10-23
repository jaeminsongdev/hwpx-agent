"""Private owned-Hancom Job admission. No launcher, COM creation or CLI.

The future native host must supply its original sampler and fresh source reader.
Readonly preparation Jobs retain their original kill-on-close behavior; this
separate native Job never kills a permission-prompt session on close or timeout.
"""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import math
import re

import conservative_maintenance as c

SELF = 'tools/p09/crossref_native_host_limits.py'
EXECUTABLE = r'C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
EXECUTABLE_SHA = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
EXECUTABLE_BYTES = 2321432
# Keep a combined eight-percent budget: native seven, host/readonly children one.
# The host's one-percent Job is NOT installed by this module.
NATIVE_SHARE, HOST_SHARE = 7, 1
FLAGS = 0x200 | 0x10 | 0x20 | 0x8  # Job memory, affinity, priority, active count; no kill/time/breakaway.
IDENTITY_KEYS = {'process_id', 'session_id', 'created_at_utc',
    'executable_sha256', 'window_handle_binds_exact_process'}


def require(ok, code):
    if not ok:
        raise ValueError('XREF_NATIVE_LIMITS_' + code)


def creation_ticks(value):
    """Lossless .NET round-trip UTC -> Windows 100ns FILETIME (no float rounding)."""
    require(type(value) is str, 'UTC_TYPE')
    match = re.fullmatch(r'(20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})\.([0-9]{7})Z', value)
    require(match is not None, 'UTC_FORMAT')
    try:
        point = datetime.strptime(match[1], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError('XREF_NATIVE_LIMITS_UTC_VALUE') from None
    delta = point - datetime(1601, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 10000000 + int(match[2])


def validate_identity(identity, window_handle):
    require(type(identity) is dict and identity.keys() == IDENTITY_KEYS, 'IDENTITY_SCHEMA')
    require(type(identity['process_id']) is int and 0 < identity['process_id'] <= 0xffffffff
        and type(identity['session_id']) is int and 0 <= identity['session_id'] <= 0xffffffff
        and identity['executable_sha256'] == EXECUTABLE_SHA
        and identity['window_handle_binds_exact_process'] is True, 'IDENTITY_VALUES')
    require(type(window_handle) is int and -(2**31) <= window_handle < 2**31 and window_handle != 0,
        'WINDOW_HANDLE')
    return creation_ticks(identity['created_at_utc'])


def validate_plan(windows):
    require(type(windows.processors) is int and 1 <= windows.processors <= 64
        and type(windows.mask) is int and windows.mask > 0 and windows.mask & (windows.mask-1) == 0,
        'ORIGINAL_CPU_SHAPE')
    require(c.POLICY['logical_cpu_limit'] == 1 and c.POLICY['priority'] == 'BelowNormal'
        and c.POLICY['job_memory_limit_percent'] == 8 and c.POLICY['job_memory_stop_percent'] == 7
        and c.POLICY['stop_commit_used_percent'] == 95, 'ORIGINAL_PROTECTED_POLICY')
    require(windows.cpu_rate == max(1, 10000 // windows.processors)
        and type(windows.memory_limit) is int and windows.memory_limit > 0
        and 0 <= windows.total_ram * 8 // 100 - windows.memory_limit < 65536, 'ORIGINAL_LIMIT_VALUES')
    limit = windows.memory_limit * NATIVE_SHARE // (NATIVE_SHARE + HOST_SHARE) // 65536 * 65536
    require(limit > 0, 'PARTITIONED_MEMORY_BUDGET')
    return dict(flags=FLAGS, memory_limit=limit, affinity=windows.mask,
        priority=0x4000, active_limit=16, cpu_rate=windows.cpu_rate)


def combined_private_budget(memory_limit, preexisting_bytes, job_peak_percent, total_ram):
    require(type(memory_limit) is int and memory_limit > 0 and type(preexisting_bytes) is int
        and preexisting_bytes >= 0 and type(total_ram) is int and total_ram > 0
        and type(job_peak_percent) in (int, float) and math.isfinite(job_peak_percent)
        and 0 <= job_peak_percent <= 100, 'PRIVATE_BUDGET_VALUES')
    # AssignProcessToJobObject does not examine allocations predating assignment.
    # Adding the pre-assignment snapshot may double-count memory, never discount it.
    combined = preexisting_bytes + job_peak_percent * total_ram / 100
    require(combined < memory_limit * 7 / 8, 'STOP_PARTITIONED_PRIVATE_MEMORY')
    return combined


class NativeOwnerJob:
    """Admit only a real owned target handle, then require graceful exit to close.

    No TerminateJobObject/TerminateProcess, force-kill fallback or prompt timer.
    Failure after assignment leaves the Job available for verified owner cleanup.
    Caller must retain this object, run original Close-P58Owner, then close it.
    """
    def __init__(self, windows, checkpoint, fresh_executable_pin):
        require(type(windows) is c.Windows and callable(checkpoint) and callable(fresh_executable_pin),
            'ORIGINAL_WINDOWS_AND_HOST_CALLBACKS')
        self.windows, self.checkpoint, self.fresh_executable_pin = windows, checkpoint, fresh_executable_pin
        self.plan = validate_plan(windows)
        self.job = None
        self.closed = False
        self.admission_attempted = False
        self.admission_failed = False
        self.identity = None
        self.profile = dict(native_process_assigned=False, limits_readback=None, cleanup_confirmed=False,
            pre_assignment_private_bytes=0,
            kill_on_close=False, forced_termination_invoked=False, host_one_percent_job_installed=False,
            native_runtime_qualified=False, native_execution_authorized=False, p09_complete=False)
        self.k = windows.k
        self.k.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
        self.k.GetProcessTimes.restype = w.BOOL
        self.k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        self.k.GetExitCodeProcess.restype = w.BOOL
        self.k.ProcessIdToSessionId.argtypes = [w.DWORD, ctypes.POINTER(w.DWORD)]
        self.k.ProcessIdToSessionId.restype = w.BOOL
        self.u = ctypes.WinDLL('user32', use_last_error=True)
        self.u.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
        self.u.GetWindowThreadProcessId.restype = w.DWORD
        checkpoint()
        self.job = self.k.CreateJobObjectW(None, None)
        require(bool(self.job), 'CREATE_JOB')
        try:
            limits = c.ExtendedLimit()
            limits.basic.flags = self.plan['flags']
            limits.basic.affinity, limits.basic.priority = self.plan['affinity'], self.plan['priority']
            limits.basic.active_limit, limits.job_memory = self.plan['active_limit'], self.plan['memory_limit']
            require(self.k.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)), 'SET_LIMITS')
            rate = c.CpuRate(5, self.plan['cpu_rate'])
            require(self.k.SetInformationJobObject(self.job, 15, ctypes.byref(rate), ctypes.sizeof(rate)), 'SET_CPU_RATE')
            self.profile['limits_readback'] = self.readback()
        except BaseException:
            self.close()  # No process has been assigned by this constructor.
            raise

    def readback(self):
        require(self.job is not None and not self.closed, 'JOB_CLOSED')
        limits, rate = c.ExtendedLimit(), c.CpuRate()
        require(self.k.QueryInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits), None)
            and self.k.QueryInformationJobObject(self.job, 15, ctypes.byref(rate), ctypes.sizeof(rate), None), 'READBACK')
        require(limits.basic.flags == self.plan['flags'] and limits.job_memory == self.plan['memory_limit']
            and limits.basic.affinity == self.plan['affinity'] and limits.basic.priority == self.plan['priority']
            and limits.basic.active_limit == self.plan['active_limit'] and rate.flags == 5
            and rate.rate == self.plan['cpu_rate'], 'READBACK_MISMATCH')
        return dict(verified=True, job_private_limit_mib=limits.job_memory/1048576,
            cpu_hard_cap_machine_percent=rate.rate/100, affinity_mask=limits.basic.affinity,
            priority_class=limits.basic.priority, active_process_limit=limits.basic.active_limit,
            kill_on_close=False, breakaway_disabled=True, time_limit_installed=False)

    def _observe_identity(self, handle, identity, window_handle, expected_ticks):
        image, size = ctypes.create_unicode_buffer(32768), w.DWORD(32768)
        require(self.k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size))
            and image.value.casefold() == EXECUTABLE.casefold(), 'PROCESS_IMAGE')
        times = [w.FILETIME() for _ in range(4)]
        require(self.k.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)), 'PROCESS_BIRTH_QUERY')
        ticks = times[0].dwLowDateTime | times[0].dwHighDateTime << 32
        session, code, window_pid = w.DWORD(), w.DWORD(), w.DWORD()
        require(ticks == expected_ticks and self.k.GetExitCodeProcess(handle, ctypes.byref(code))
            and code.value == 259 and self.k.ProcessIdToSessionId(identity['process_id'], ctypes.byref(session))
            and session.value == identity['session_id'], 'PROCESS_IDENTITY')
        require(self.u.GetWindowThreadProcessId(w.HWND(window_handle & 0xffffffff), ctypes.byref(window_pid))
            and window_pid.value == identity['process_id'], 'LIVE_WINDOW_PID')

    def _private_bytes(self, handle):
        memory = c.ProcessMemory()
        memory.size = ctypes.sizeof(memory)
        require(self.k.K32GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.size), 'PROCESS_PRIVATE_MEMORY')
        return int(memory.private)

    def admit(self, identity, window_handle):
        require(not self.closed and not self.admission_attempted, 'NO_ADMISSION_RETRY')
        self.admission_attempted = True
        handle = None
        try:
            ticks = validate_identity(identity, window_handle)
            self.checkpoint()
            # Query + SET_QUOTA + TERMINATE are required by AssignProcessToJobObject.
            # Obtaining TERMINATE access never authorizes or invokes termination.
            handle = self.k.OpenProcess(0x1000 | 0x400 | 0x100 | 0x1, False, identity['process_id'])
            require(bool(handle), 'OPEN_EXACT_PROCESS')
            self._observe_identity(handle, identity, window_handle, ticks)
            pin = self.fresh_executable_pin()
            require(type(pin) is dict and pin.get('sha256') == EXECUTABLE_SHA
                and type(pin.get('bytes')) is int and pin['bytes'] == EXECUTABLE_BYTES, 'FRESH_EXECUTABLE_PIN')
            require(self.windows.accounting(self.job)['active_processes'] == 0, 'EMPTY_JOB_BEFORE_ADMIT')
            self.readback()
            self.checkpoint()
            self._observe_identity(handle, identity, window_handle, ticks)
            preexisting = self._private_bytes(handle)
            combined_private_budget(self.plan['memory_limit'], preexisting, 0, self.windows.total_ram)
            self.profile['pre_assignment_private_bytes'] = preexisting
            require(self.k.AssignProcessToJobObject(self.job, handle), 'ASSIGN_EXACT_PROCESS')
            self.profile['native_process_assigned'] = True
            self.identity = dict(identity)
            member = w.BOOL()
            require(self.k.IsProcessInJob(handle, self.job, ctypes.byref(member)) and member.value, 'MEMBERSHIP')
            allowed, system = ctypes.c_size_t(), ctypes.c_size_t()
            require(self.k.GetProcessAffinityMask(handle, ctypes.byref(allowed), ctypes.byref(system))
                and allowed.value == self.plan['affinity']
                and self.k.GetPriorityClass(handle) == self.plan['priority'], 'PROCESS_LIMIT_READBACK')
            self._observe_identity(handle, identity, window_handle, ticks)
            combined_private_budget(self.plan['memory_limit'], self._private_bytes(handle), 0, self.windows.total_ram)
            self.observe()
            return dict(self.profile['limits_readback'])
        except BaseException:
            self.admission_failed = True
            raise
        finally:
            if handle:
                require(self.k.CloseHandle(handle), 'PROCESS_HANDLE_CLOSE')

    def observe(self):
        require(not self.closed and self.job is not None, 'JOB_CLOSED')
        self.checkpoint()  # Original sole sampler; no preparation-only CPU replacement.
        info = self.windows.accounting(self.job)
        self.profile['last_job_accounting'] = info
        # The MiB display field is rounded; use the original unrounded percentage.
        combined_private_budget(self.plan['memory_limit'], self.profile.get('pre_assignment_private_bytes', 0),
            info['peak_job_private_percent'], self.windows.total_ram)
        return info

    def close(self):
        if self.closed:
            require(self.profile['cleanup_confirmed'], 'PREVIOUS_CLOSE_FAILED')
            return
        if self.job is not None:
            # Cleanup is deliberately not guarded by pressure/deadline checks.
            info = self.windows.accounting(self.job)
            self.profile['last_job_accounting'] = info
            require(info['active_processes'] == 0, 'OWNED_PROCESS_STILL_ALIVE_NO_FORCE_CLOSE')
            require(self.k.CloseHandle(self.job), 'JOB_HANDLE_CLOSE')
            self.job = None
        self.closed = True
        self.profile['cleanup_confirmed'] = True
