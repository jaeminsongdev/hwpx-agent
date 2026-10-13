"""Fresh final light-review sample at the original distinct .5-second slot.

Original Guard methods/sampler/hard decisions remain; only force sampling that
would reuse a too-short interval waits in bounded .05-second guarded steps.
No new sampler/query/thread, CPU startup threshold or source/limit relaxation.
"""
import math
import time

SELF="tools/p09/distinct_final_sample_guard_v1.py"
TEST="tools/p09/tests/test_distinct_final_sample_guard_v1.py"
INTERVAL=.5

def require(ok,code):
    if not ok:raise ValueError("DISTINCT_FINAL_SAMPLE_"+code)

def guard_type(original,clock=time.monotonic,sleep=time.sleep):
    require(type(original) is type and callable(clock) and callable(sleep),"ORIGINAL_GUARD_CLOCK_SLEEP")
    class Guard(original):
        def check(self,force=False):
            require(type(force) is bool,"EXACT_FORCE_FLAG")
            if not force or not self.samples:return original.check(self,force=force)
            before=len(self.samples);target=self.last+INTERVAL;last_clock=None;attempts=0
            while True:
                attempts+=1;require(attempts<=64,"WAIT_CLOCK_NOT_ADVANCING")
                # Keep original deadline/CPU/RAM logic and existing cadence.
                original.check(self,force=False)
                if len(self.samples)>before:return
                now=clock()
                require(type(now) in (int,float) and math.isfinite(now)
                    and (last_clock is None or now>=last_clock),"MONOTONIC_WAIT_CLOCK")
                last_clock=now
                remaining=target-now
                if remaining<=0:return original.check(self,force=True)
                sleep(min(.05,remaining))
    return Guard
