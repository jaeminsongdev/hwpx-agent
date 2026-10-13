"""One explicit diagnostic query, not a replacement for qualified guards.

MEMORYSTATUSEX page-file fields can reflect a process limit. GetPerformanceInfo
CommitTotal/CommitLimit are system-wide pages. Never rewrite past measurements
or silently relax original decisions. One synchronous call cannot guarantee a
hard time bound; a late result is unavailable for comparison.
"""
import ctypes
import math
import time


class PerformanceInformation(ctypes.Structure):
    _fields_ = [('cb', ctypes.c_uint32)] + [
        (name, ctypes.c_size_t) for name in (
            'CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal',
            'PhysicalAvailable', 'SystemCache', 'KernelTotal', 'KernelPaged',
            'KernelNonpaged', 'PageSize')
    ] + [(name, ctypes.c_uint32) for name in ('HandleCount', 'ProcessCount', 'ThreadCount')]


def once(kernel, clock=time.monotonic, budget_seconds=.05):
    if budget_seconds != .05:
        raise ValueError('GLOBAL_COMMIT_DIAGNOSTIC_FIXED_BUDGET')
    fn = kernel.K32GetPerformanceInfo
    fn.argtypes = [ctypes.POINTER(PerformanceInformation), ctypes.c_uint32]
    fn.restype = ctypes.c_int
    info = PerformanceInformation()
    info.cb = ctypes.sizeof(info)
    start = clock()
    ok = bool(fn(ctypes.byref(info), info.cb))
    elapsed = clock() - start
    out = dict(available=False, query_calls=1, elapsed_seconds=elapsed,
               nominal_budget_seconds=budget_seconds, hard_OS_call_preemption=False,
               replaces_original_resource_decisions=False,
               past_failure_same_interval=False)
    if not ok:
        out['reason'] = 'GLOBAL_PERFORMANCE_QUERY_FAILED'
    elif not math.isfinite(elapsed) or elapsed < 0 or elapsed > budget_seconds:
        out['reason'] = 'DIAGNOSTIC_COST_BUDGET_EXCEEDED'
    elif (info.cb != ctypes.sizeof(info) or info.CommitLimit <= 0
          or info.CommitTotal > info.CommitLimit or info.PageSize <= 0
          or info.PhysicalTotal <= 0 or info.PhysicalAvailable > info.PhysicalTotal):
        out['reason'] = 'GLOBAL_PERFORMANCE_VALUES_INVALID'
    else:
        out.update(available=True, reason=None,
                   system_commit_used_percent=100 * info.CommitTotal / info.CommitLimit,
                   system_commit_used_bytes=info.CommitTotal * info.PageSize,
                   system_commit_limit_bytes=info.CommitLimit * info.PageSize,
                   available_physical_percent=100 * info.PhysicalAvailable / info.PhysicalTotal)
    return out
