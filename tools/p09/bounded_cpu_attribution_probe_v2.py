"""Bounded snapshot successor: check budget DURING enumeration, reuse scratch.

50ms remains, no hard preemption guarantee for a single OS call. Over-budget
partial rows explicitly unavailable; snapshot/process handles close normally.
No PDH/WMI/command lines/paths/extra global-CPU sampler/thread/process.
"""
import ctypes
import time

import bounded_cpu_attribution_probe_v1 as prior

SELF="tools/p09/bounded_cpu_attribution_probe_v2.py"
TEST="tools/p09/tests/test_bounded_cpu_attribution_probe_v2.py"
MAX_CAPTURE_SECONDS=.05
Entry=prior.Entry
compare=prior.compare
role=prior.role


class Snapshot(prior.Snapshot):
    def capture(self,*,clock=time.monotonic):
        started=clock()
        exhausted=lambda:clock()-started>=MAX_CAPTURE_SECONDS
        handle=self.k.CreateToolhelp32Snapshot(2,0)
        prior.require(handle not in (None,0,ctypes.c_void_p(-1).value),"SNAPSHOT_CREATE")
        rows,seen,unavailable={},0,0
        entry=Entry();entry.size=ctypes.sizeof(entry)
        values=[ctypes.c_uint64() for _ in range(4)]
        pointers=tuple(ctypes.byref(value) for value in values)
        budget_exceeded=False;more=True
        try:
            if exhausted():
                budget_exceeded=True
            else:
                ctypes.set_last_error(0)
                more=self.k.Process32FirstW(handle,ctypes.byref(entry))
                while more and seen<prior.MAX_PROCESSES:
                    if exhausted():
                        budget_exceeded=True;break
                    seen+=1;pid=int(entry.pid)
                    process=self.k.OpenProcess(0x1000,False,pid)
                    if process:
                        try:
                            if exhausted():
                                budget_exceeded=True
                            else:
                                for value in values:value.value=0
                                if self.k.GetProcessTimes(process,*pointers):
                                    rows[pid]=dict(pid=pid,parent=int(entry.parent),role=role(entry.name),
                                      creation=values[0].value,ticks=values[2].value+values[3].value)
                                else:unavailable+=1
                        finally:
                            prior.require(self.k.CloseHandle(process),"PROCESS_HANDLE_CLOSE")
                    else:unavailable+=1
                    if budget_exceeded or exhausted():
                        budget_exceeded=True;break
                    ctypes.set_last_error(0)
                    more=self.k.Process32NextW(handle,ctypes.byref(entry))
                if not more:
                    prior.require(ctypes.get_last_error()==18,"ENUMERATION_FAILED")
        finally:
            prior.require(self.k.CloseHandle(handle),"SNAPSHOT_CLOSE")
        ended=clock()
        budget_exceeded=budget_exceeded or ended-started>MAX_CAPTURE_SECONDS
        # Never offer partial observations as a completed baseline.
        if budget_exceeded:rows={}
        return dict(time_monotonic=ended,rows=rows,enumerated=seen,unavailable=unavailable,
         truncated=bool(more),collection_seconds=ended-started,measurement_budget_exceeded=budget_exceeded,
         partial_rows_discarded=budget_exceeded,clock_includes_snapshot_create_and_all_closes=True,
         process_time_scratch_allocations=1,OS_call_hard_preemption_guaranteed=False)
