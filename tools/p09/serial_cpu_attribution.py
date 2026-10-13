"""Fixed PDH counters collected by the existing observer, never a sidecar.

Original K32 resource decisions are unchanged. PDH intervals are approximately,
not exactly, aligned; contributor observation is not filesystem/causal proof.
English counter paths, two samples, per-counter status and PID binding checked.
No wildcards, process listing/commands, subprocess, thread, retries or OS writes.
"""
import ctypes
from ctypes import wintypes as w
import math
import os
import threading
import time

SELF="tools/p09/serial_cpu_attribution.py"
TEST="tools/p09/tests/test_serial_cpu_attribution.py"
FMT_DOUBLE=0x200;FMT_LONG=0x100;NOCAP100=0x8000
MAX_SAMPLE_SECONDS=.05
MAX_TOTAL_SAMPLE_SECONDS=2.0
PATHS={
    "MsMpEng_cpu":r"\Process(MsMpEng)\% Processor Time",
    "MsMpEng_pid":r"\Process(MsMpEng)\ID Process",
    "System_cpu":r"\Process(System)\% Processor Time",
    "System_pid":r"\Process(System)\ID Process",
    "total_cpu":r"\Processor(_Total)\% Processor Time",
    "DPC_cpu":r"\Processor(_Total)\% DPC Time",
    "interrupt_cpu":r"\Processor(_Total)\% Interrupt Time"}


def require(ok,code):
    if not ok:raise ValueError("SERIAL_CPU_ATTRIBUTION_"+code)


class ValueUnion(ctypes.Union):
    _fields_=[("longValue",w.LONG),("doubleValue",ctypes.c_double),("largeValue",ctypes.c_int64)]


class Value(ctypes.Structure):
    _anonymous_=("value",)
    _fields_=[("CStatus",w.DWORD),("value",ValueUnion)]


class PDH:
    def __init__(self):
        require(os.name=="nt","WINDOWS_ONLY")
        self.dll=ctypes.WinDLL("pdh",use_last_error=True)
        for name,args in (("PdhOpenQueryW",[w.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(w.HANDLE)]),
            ("PdhAddEnglishCounterW",[w.HANDLE,w.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(w.HANDLE)]),
            ("PdhCollectQueryData",[w.HANDLE]),
            ("PdhGetFormattedCounterValue",[w.HANDLE,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.POINTER(Value)]),
            ("PdhCloseQuery",[w.HANDLE])):
            fn=getattr(self.dll,name);fn.argtypes=args;fn.restype=w.DWORD
    def open(self):
        handle=w.HANDLE();status=self.dll.PdhOpenQueryW(None,0,ctypes.byref(handle))
        return status,handle.value
    def add(self,query,path):
        handle=w.HANDLE();status=self.dll.PdhAddEnglishCounterW(query,path,0,ctypes.byref(handle))
        return status,handle.value
    def collect(self,query):return self.dll.PdhCollectQueryData(query)
    def value(self,handle,is_pid):
        result=Value();format=FMT_LONG if is_pid else FMT_DOUBLE|NOCAP100
        status=self.dll.PdhGetFormattedCounterValue(handle,format,None,ctypes.byref(result))
        return status,result.CStatus,result.longValue if is_pid else result.doubleValue
    def close(self,query):return self.dll.PdhCloseQuery(query)


class Probe:
    def __init__(self,processors,*,api=None,clock=time.monotonic,identity=lambda:(os.getpid(),threading.get_ident())):
        require(type(processors) is int and 1<=processors<=64,"PROCESSORS")
        self.processors=processors;self.clock=clock;self.identity=identity;self.owner=identity()
        self.api=api or PDH();self.query=None;self.counters={};self.status={}
        self.collects=0;self.samples=0;self.maximum_latency=0.;self.total_latency=0.
        self.last=None;self.previous_pid={};self.disabled_reason=None;self.cleanup=True
        self.setup_seconds=0.;self.close_attempts=0
        start=clock()
        status,handle=self.api.open()
        if status or not handle:self.disabled_reason="QUERY_UNAVAILABLE";return
        self.query=handle;self.cleanup=False
        try:
            for name,path in PATHS.items():
                status,counter=self.api.add(handle,path)
                self.status[name]=status
                if status==0 and counter:self.counters[name]=counter
            if not self.counters:self.disabled_reason="COUNTERS_UNAVAILABLE";self.close();return
            status=self.api.collect(handle);self.collects+=1;self.last=clock()
            if status:self.disabled_reason="BASELINE_UNAVAILABLE"
            else:
                for name in ("MsMpEng_pid","System_pid"):
                    value=self.read(name)
                    if value is not None:self.previous_pid[name]=value
        finally:self.setup_seconds=clock()-start
    def read(self,name):
        handle=self.counters.get(name)
        if handle is None:return None
        status,cstatus,value=self.api.value(handle,name.endswith("_pid"))
        self.status[name]=dict(return_status=int(status),counter_status=int(cstatus))
        if status!=0 or cstatus not in (0,1):return None
        if name.endswith("_pid"):
            return value if type(value) is int and 0<value<=0xffffffff else None
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:return None
        machine=value/self.processors if name in ("MsMpEng_cpu","System_cpu") else value
        return machine if machine<=100 else None
    def sample(self):
        require(self.identity()==self.owner,"SAME_ORIGINAL_OBSERVER_OWNER")
        if self.query is None or self.disabled_reason:
            return dict(available=False,reason=self.disabled_reason or "CLOSED",values=None)
        start=self.clock();previous=self.last
        status=self.api.collect(self.query);self.collects+=1;self.last=self.clock();self.samples+=1
        result=dict(available=status==0,collect_status=int(status),values={})
        if status==0:
            for name in ("MsMpEng","System"):
                pid=self.read(name+"_pid");cpu=self.read(name+"_cpu")
                bound=pid is not None and pid==self.previous_pid.get(name+"_pid")
                if name=="System":bound=bound and pid==4
                result["values"][name]=dict(pid=pid,pid_stable=bound,machine_cpu_percent=cpu if bound else None)
                if pid is not None:self.previous_pid[name+"_pid"]=pid
            for name in ("total_cpu","DPC_cpu","interrupt_cpu"):result["values"][name]=self.read(name)
        duration=self.clock()-start;require(math.isfinite(duration) and duration>=0,"CLOCK")
        self.maximum_latency=max(self.maximum_latency,duration);self.total_latency+=duration
        result.update(added_wall_seconds=duration,interval_seconds=None if previous is None else self.last-previous,
            identical_to_original_K32_interval=False,first_counter_sample_used_as_rate=False,
            raw_process_commands_or_paths_recorded=False,causal_trigger_attribution_established=False)
        if duration>MAX_SAMPLE_SECONDS or self.total_latency>MAX_TOTAL_SAMPLE_SECONDS:
            self.disabled_reason="MEASUREMENT_COST_BUDGET_EXCEEDED";self.close()
            result["available"]=False;result["reason"]=self.disabled_reason;result["values"]=None
        return result
    def close(self):
        if self.query is not None:
            self.close_attempts+=1
            if self.api.close(self.query)!=0:self.cleanup=False;return False
            self.query=None;self.counters.clear();self.cleanup=True
        return self.cleanup
    def summary(self):
        return dict(fixed_counter_count=len(PATHS),wildcard_or_process_inventory=False,
            collect_calls=self.collects,samples=self.samples,setup_seconds=self.setup_seconds,
            maximum_added_sample_seconds=self.maximum_latency,total_added_sample_seconds=self.total_latency,
            maximum_sample_budget_seconds=MAX_SAMPLE_SECONDS,total_added_sample_budget_seconds=MAX_TOTAL_SAMPLE_SECONDS,
            disabled_reason=self.disabled_reason,query_remaining=self.query is not None,cleanup_confirmed=self.cleanup,
            close_attempts=self.close_attempts,counter_status=dict(self.status),
            original_K32_CPU_RAM_decisions_replaced=False,second_sampler_thread_or_process=False,
            extra_PDH_queries_added_to_original_observer=True,interval_alignment_exact=False,
            security_sandbox_or_CPU_freeze_improvement_claimed=False)
