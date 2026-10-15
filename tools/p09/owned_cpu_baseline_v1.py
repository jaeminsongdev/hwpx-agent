"""Measured cold owner epoch for diagnostic Guards, not a resource sample.

No change to inherited sampling/decisions, clocks, limits, deadline or cleanup.
Do not seed an active guard or substitute any constant for measured CPU time.
"""
import math
import time

SELF="tools/p09/owned_cpu_baseline_v1.py"


def require(ok,label):
    if not ok:raise ValueError("OWNED_CPU_BASELINE_"+label)


def guard_type(original,*,wall=time.monotonic,cpu=time.process_time):
    require(type(original) is type and callable(wall) and callable(cpu),"ORIGINAL_GUARD_AND_CLOCKS")
    class Guard(original):
        def __init__(self):
            super().__init__()
            require(self.cpu is None and type(self.last) in (int,float) and self.last==0
                and type(self.samples) is list and not self.samples,"COLD_UNSAMPLED_OWNER_ONLY")
            stamp=wall();counter=cpu();after=wall()
            require(all(type(v) in (int,float) and math.isfinite(v) for v in (stamp,counter,after))
                and stamp>0 and counter>=0 and 0<=after-stamp<=.05,"MEASURED_CLOSE_CLOCK_PAIR")
            self.last=stamp;self.cpu=counter
            self.owned_CPU_baseline=dict(measured=True,wall_epoch=stamp,CPU_epoch=counter,
                clock_pair_skew_seconds=after-stamp,original_samples_added=0,
                original_check_deadline_guards_and_cleanup_unchanged=True)
    return Guard
