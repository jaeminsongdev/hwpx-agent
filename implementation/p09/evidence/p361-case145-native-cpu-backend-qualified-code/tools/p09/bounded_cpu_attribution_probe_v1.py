"""Bounded idle CPU attribution; never runs a product/preflight/acceptance.

기존 sole sampler/guard/affinity/mutex를 유지한다. Toolhelp process snapshot와
GetProcessTimes를 동일 스레드에서 2초 간격으로 최대 17회만 조회한다.
Command line, path, user, memory contents are never queried. No WMI/PDH/helper.
"""
import ctypes
from ctypes import wintypes as w
import json
import math
import os
import time

import flat_current_queue_direct_view_runtime_v4 as runtime
import terminal_metadata_pressure_v1 as pressure
import read_only_acceptance_pressure_probe_v1 as diagnostics

SELF = "tools/p09/bounded_cpu_attribution_probe_v1.py"
TEST = "tools/p09/tests/test_bounded_cpu_attribution_probe_v1.py"
MAX_PROCESSES = 512
MAX_OBSERVATIONS = 17
ROLES = frozenset(("git.exe", "python.exe", "python3.exe", "codex.exe", "chatgpt.exe",
                  "msmpeng.exe", "compattelrunner.exe", "vmmemwsl", "vmmem", "system",
                  "radeonsoftware.exe", "node.exe", "rustc.exe", "cargo.exe", "powershell.exe",
                  "pwsh.exe", "wmiprvse.exe"))


def require(ok, code):
    if not ok:
        raise ValueError("CPU_ATTRIBUTION_" + code)


def role(name):
    return name.lower() if type(name) is str and name.lower() in ROLES else "other"


class Entry(ctypes.Structure):
    _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("pid", w.DWORD),
                ("heap", ctypes.c_size_t), ("module", w.DWORD), ("threads", w.DWORD),
                ("parent", w.DWORD), ("priority", w.LONG), ("flags", w.DWORD),
                ("name", w.WCHAR * 260)]


class Snapshot:
    def __init__(self):
        require(os.name == "nt", "WINDOWS_ONLY")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, args, result in (
            ("CreateToolhelp32Snapshot", [w.DWORD, w.DWORD], w.HANDLE),
            ("Process32FirstW", [w.HANDLE, ctypes.POINTER(Entry)], w.BOOL),
            ("Process32NextW", [w.HANDLE, ctypes.POINTER(Entry)], w.BOOL),
            ("OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            ("GetProcessTimes", [w.HANDLE] + [ctypes.POINTER(ctypes.c_uint64)] * 4, w.BOOL),
            ("CloseHandle", [w.HANDLE], w.BOOL),
        ):
            fn = getattr(self.k, name)
            fn.argtypes, fn.restype = args, result

    def capture(self):
        handle = self.k.CreateToolhelp32Snapshot(2, 0)
        require(handle not in (None, 0, ctypes.c_void_p(-1).value), "SNAPSHOT_CREATE")
        rows, seen, unavailable = {}, 0, 0
        entry = Entry(); entry.size = ctypes.sizeof(entry)
        started = time.monotonic()
        try:
            ctypes.set_last_error(0)
            more = self.k.Process32FirstW(handle, ctypes.byref(entry))
            while more and seen < MAX_PROCESSES:
                seen += 1
                pid = int(entry.pid)
                process = self.k.OpenProcess(0x1000, False, pid)  # query limited only
                if process:
                    try:
                        values = [ctypes.c_uint64() for _ in range(4)]
                        if self.k.GetProcessTimes(process, *(ctypes.byref(v) for v in values)):
                            rows[pid] = dict(pid=pid, parent=int(entry.parent), role=role(entry.name),
                                             creation=values[0].value, ticks=values[2].value + values[3].value)
                        else:
                            unavailable += 1
                    finally:
                        require(self.k.CloseHandle(process), "PROCESS_HANDLE_CLOSE")
                else:
                    unavailable += 1
                ctypes.set_last_error(0)
                more = self.k.Process32NextW(handle, ctypes.byref(entry))
            truncated = bool(more)
            if not more:
                require(ctypes.get_last_error() == 18, "ENUMERATION_FAILED")
        finally:
            require(self.k.CloseHandle(handle), "SNAPSHOT_CLOSE")
        return dict(time_monotonic=time.monotonic(), rows=rows, enumerated=seen,
                    unavailable=unavailable, truncated=truncated,
                    collection_seconds=time.monotonic() - started)


def compare(previous, current, processors):
    require(type(processors) is int and 1 <= processors <= 64, "PROCESSORS")
    wall = current["time_monotonic"] - previous["time_monotonic"]
    require(math.isfinite(wall) and wall > 0, "WALL_INTERVAL")
    rows, new, negative = [], 0, 0
    for pid, row in current["rows"].items():
        old = previous["rows"].get(pid)
        if old is None or old["creation"] != row["creation"]:
            new += 1
            continue  # Do not invent a baseline for new/reused PIDs.
        delta = row["ticks"] - old["ticks"]
        if delta < 0:
            negative += 1
            continue
        rows.append(dict(pid=pid, parent=row["parent"], role=row["role"],
                         machine_CPU_percent=100 * delta / 10000000 / wall / processors))
    rows.sort(key=lambda r: r["machine_CPU_percent"], reverse=True)
    return dict(window_seconds=wall, top_processes=rows[:8],
                matched_processes=len(rows), matched_machine_CPU_sum=sum(r["machine_CPU_percent"] for r in rows),
                new_or_reused_pid_no_baseline=new, negative_delta_unresolved=negative,
                unavailable_current=current["unavailable"], process_list_truncated=current["truncated"],
                complete_system_CPU_attribution=False,
                reason="Protected/exited/new processes and kernel work may be unavailable; windows differ")


def run():
    g = pressure.guard_type(runtime.a.Guard)(); observations = []; prior = None
    out = dict(state="FAILED_BOUNDED_IDLE_CPU_ATTRIBUTION_NOT_PRODUCT", product_or_Native_or_preflight_or_acceptance_executed=False,
               extra_system_CPU_sampler=False, extra_thread_or_process_or_WMI_or_PDH=False,
               command_line_or_path_or_secret_collected=False, accepted_count_delta=0,
               P09_gate="OPEN", P10_started=False, PC_freeze_resolved=False)
    snapshot = Snapshot(); started = time.monotonic(); next_query = started
    def observe():
        nonlocal prior
        require(len(observations) < MAX_OBSERVATIONS, "OBSERVATION_BOUND")
        current = snapshot.capture()
        row = dict(system_sample=dict(g.samples[-1]), enumerated=current["enumerated"],
                   unavailable=current["unavailable"], truncated=current["truncated"],
                   collection_seconds=current["collection_seconds"])
        if prior is not None:
            row["process_deltas"] = compare(prior, current, g.windows.processors)
        observations.append(row); prior = current
    try:
        g.acquire()
        observe(); next_query = time.monotonic() + 2
        while time.monotonic() - started < 32:
            time.sleep(.5)
            try:
                g.check(force=True)
            except ValueError:
                if len(observations) < MAX_OBSERVATIONS:
                    observe()  # one closed stop-time snapshot, then no more work
                raise
            if time.monotonic() >= next_query:
                observe(); next_query = time.monotonic() + 2
        out["state"] = "OBSERVED_BOUNDED_IDLE_CPU_WINDOW_NOT_PRODUCT_OR_ROOT_CAUSE_PROOF"
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        out["error_code"] = diagnostics.closed_error(error)
    finally:
        g.close()
        out.update(observations=observations, cleanup_confirmed=g.cleanup,
                   elapsed_seconds=time.monotonic() - started,
                   all_entrypoint_warning_guard=pressure.summary(g),
                   resource_diagnostics=diagnostics.resource_diagnostics(g, runtime.c.decision))
    return out


if __name__ == "__main__":
    row = run(); print(json.dumps(row))
    raise SystemExit(0 if row["state"].startswith("OBSERVED_") and row["cleanup_confirmed"] else 2)
