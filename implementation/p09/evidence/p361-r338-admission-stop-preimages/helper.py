"""Bounded acquisition timing: original reserve and CreateFileW stay intact.

Install explicitly on one newly owned Native instance, never its class/default
module. No path/handle/error values, per-input traces, extra OS queries, threads,
closes or resource decisions. Preserve ctypes last-error around every clock.
An unavailable clock is unknown, not zero and never masks the original error.
"""
import ctypes
import math
import os
import threading
import time

SELF = "tools/p09/native_open_phase_timing_v1.py"
TEST = "tools/p09/tests/test_native_open_phase_timing_v1.py"


def require(ok, label):
    if not ok:
        raise ValueError("NATIVE_PHASE_TIMING_" + label)


class Timing:
    def __init__(self, acquisition, clock=time.monotonic,
                 identity=lambda: (os.getpid(), threading.get_ident())):
        self.acquisition = acquisition
        self.clock = clock
        self.identity = identity
        self.owner = identity()
        self.rows = {name: dict(started=0, completed=0, failed=0, measured=0,
                    unknown=0, elapsed_total_seconds=0.0, elapsed_max_seconds=None)
                     for name in ("original_reserve_including_checkpoints", "original_CreateFileW")}

    def now(self):
        saved = ctypes.get_last_error()
        try:
            value = self.clock()
            return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None
        except Exception:
            return None
        finally:
            ctypes.set_last_error(saved)

    def call(self, name, original, *args):
        # The original acquisition diagnostic defines the active phase. Borrowed
        # streams, access probes outside that phase and cleanup delegate directly.
        if self.acquisition.current is None:
            return original(*args)
        require(self.identity() == self.owner, "SAME_ACQUISITION_OWNER")
        row = self.rows[name]; row["started"] += 1
        started = self.now(); completed = False
        try:
            result = original(*args); completed = True; return result
        finally:
            ended = self.now(); row["completed" if completed else "failed"] += 1
            duration = None if started is None or ended is None or ended < started else ended - started
            if duration is None:
                row["unknown"] += 1
            else:
                row["measured"] += 1; row["elapsed_total_seconds"] += duration
                previous = row["elapsed_max_seconds"]
                row["elapsed_max_seconds"] = duration if previous is None else max(previous, duration)

    def summary(self):
        return dict(operations={name: dict(row) for name, row in self.rows.items()},
                    reserve_includes_original_checkpoint_and_sleep=True,
                    CreateFileW_excludes_original_reserve=True,
                    paths_handles_or_error_values_recorded=False, bounded_aggregate_only=True,
                    new_OS_queries_threads_or_resource_samples=False,
                    original_native_or_pacer_code_replaced=False,
                    original_ctypes_last_error_preserved=True,
                    CPU_cause_or_PC_freeze_resolution_proven=False)


class Pacer:
    def __init__(self, original, timing):
        object.__setattr__(self, "original", original)
        object.__setattr__(self, "timing", timing)

    def __getattr__(self, name):
        return getattr(self.original, name)

    def __setattr__(self, name, value):
        setattr(self.original, name, value)

    def reserve(self):
        return self.timing.call("original_reserve_including_checkpoints", self.original.reserve)


class Kernel:
    def __init__(self, original, timing):
        self.original = original
        self.timing = timing

    def __getattr__(self, name):
        return getattr(self.original, name)

    def CreateFileW(self, *args):
        return self.timing.call("original_CreateFileW", self.original.CreateFileW, *args)


def connect(native, acquisition, *, clock=time.monotonic,
            identity=lambda: (os.getpid(), threading.get_ident())):
    require(not hasattr(native, "acquisition_phase_timing"), "ONE_INSTALLATION")
    require(hasattr(acquisition, "current") and acquisition.current is None,
            "INSTALL_BEFORE_ACQUISITION")
    require(callable(native.pacer.reserve) and callable(native.k.CreateFileW), "ORIGINAL_CALLABLES")
    timing = Timing(acquisition, clock, identity)
    pacer, kernel = native.pacer, native.k
    native.pacer = Pacer(pacer, timing)
    native.k = Kernel(kernel, timing)
    native.acquisition_phase_timing = timing
    return timing, dict(original_pacer=pacer, original_kernel=kernel,
                        original_native_instance=native, default_class_or_module_mutated=False,
                        cleanup_or_close_wrapped=False, GO_or_product_qualified=False)
