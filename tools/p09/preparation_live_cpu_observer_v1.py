"""Read-only same-run attribution for one explicitly identified preparation PID.

Independent diagnostic process, never a verifier dependency or controller.
No launch/kill, privilege changes, process commands/paths, or OS writes.
Original verifier resource decisions and source checks remain untouched.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ctypes
import hashlib
import json
import math
import os
import re
import sys
import time

SELF="tools/p09/preparation_live_cpu_observer_v1.py"
TEST="tools/p09/tests/test_preparation_live_cpu_observer_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
MAX_SECONDS=240
MAX_SAMPLES=240
MAX_OBSERVER_WORK_SECONDS=5.0


def require(ok,label):
    if not ok:raise ValueError("PREPARATION_LIVE_OBSERVER_"+label)


def target_request(raw,own_pid):
    require(type(raw) is str and 0<len(raw)<=128,"BOUNDED_TARGET_REQUEST")
    value=json.loads(raw)
    require(type(value) is dict and set(value)=={"pid","creation_time_100ns"},"CLOSED_TARGET_REQUEST")
    require(type(value["pid"]) is int and 0<value["pid"]<=0xffffffff and value["pid"]!=own_pid,"EXPLICIT_OTHER_PID")
    require(type(value["creation_time_100ns"]) is int and 0<value["creation_time_100ns"]<2**64,"EXPECTED_CREATION_IDENTITY")
    return value


def share(before,after,pid):
    previous=before["rows"].get(pid);current=after["rows"].get(pid)
    if previous is None or current is None or previous[0]!=current[0] or previous[2]!=current[2] or current[1]<previous[1]:return None
    delta=[b-a for a,b in zip(before["system"],after["system"])];denominator=delta[1]+delta[2]
    require(len(delta)==3 and denominator>0 and all(type(v) is int and v>=0 for v in delta),"VALID_SYSTEM_INTERVAL")
    return round(100*(current[1]-previous[1])/denominator,6)


def compact(before,after,groups,fixed,stage_pid,observer_pid,elapsed):
    values=fixed.get("values") if fixed.get("available") is True else None
    def counter(name):
        if type(values) is not dict:return None
        value=values.get(name)
        if type(value) is dict:return value.get("machine_cpu_percent") if value.get("pid_stable") is True else None
        return value
    return dict(elapsed_seconds=round(elapsed,6),system_CPU=groups["system_cpu_percent"],
        stage_CPU=share(before,after,stage_pid),observer_CPU=share(before,after,observer_pid),
        Defender_CPU=counter("MsMpEng"),System_CPU=counter("System"),DPC_CPU=counter("DPC_cpu"),interrupt_CPU=counter("interrupt_cpu"),
        process_groups=[[r["label"],r["machine_cpu_percent"]] for r in groups["top_cpu_groups"]],
        inaccessible_processes=groups["inaccessible_processes"],new_or_reused_PIDs=groups["newly_seen_or_reused_PIDs"],
        process_snapshot_seconds=groups["scan_seconds"],fixed_counter_seconds=fixed.get("added_wall_seconds"),
        fixed_counter_available=fixed.get("available") is True)


def watch(alive,snapshot,compare,probe,stage_pid,observer_pid,*,clock=time.monotonic,pause=time.sleep):
    started=clock();previous=snapshot();work=previous["scan_seconds"];rows=[]
    reason="TARGET_TERMINAL";terminal=False
    while True:
        if not alive():terminal=True;break
        if len(rows)>=MAX_SAMPLES or clock()-started>=MAX_SECONDS:reason="OBSERVATION_BOUND_REACHED";break
        pause(min(1.,max(0.,MAX_SECONDS-(clock()-started))))
        try:
            current=snapshot();fixed=probe.sample()
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
            return dict(samples=rows,sample_count=len(rows),stop_reason="SAMPLING_FAILURE",target_terminal_observed=False,
                observer_work_seconds=work,elapsed_seconds=clock()-started,observer_error=error_code(error))
        work+=current["scan_seconds"]+fixed.get("added_wall_seconds",0.)
        require(math.isfinite(work) and work>=0,"FINITE_OBSERVER_COST")
        if work>MAX_OBSERVER_WORK_SECONDS:reason="OBSERVER_WORK_BUDGET_REACHED";break
        groups=compare(previous,current)
        rows.append(compact(previous,current,groups,fixed,stage_pid,observer_pid,clock()-started));previous=current
    return dict(samples=rows,sample_count=len(rows),stop_reason=reason,target_terminal_observed=terminal,
        observer_work_seconds=work,elapsed_seconds=clock()-started)


def error_code(error):
    value=error.args[0] if error.args else None
    return value if type(value) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,159}",value) else type(error).__name__


class TrackedPDH:
    """Close a partially constructed Probe's query without losing its handle."""
    def __init__(self,native):self.native=native;self.handles=set()
    def __getattr__(self,name):return getattr(self.native,name)
    def open(self):
        status,handle=self.native.open()
        if status==0 and handle:self.handles.add(handle)
        return status,handle
    def close(self,handle):
        status=self.native.close(handle)
        if status==0:self.handles.discard(handle)
        return status
    def close_partial(self):
        for handle in tuple(self.handles):self.close(handle)
        return not self.handles


def main():
    import argparse
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as resources
    host=resources.Windows()  # One CPU/BelowNormal before project helper imports.
    import process_cpu_attribution as process
    import serial_cpu_attribution as fixed
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage",choices=("preflight","qualify"),required=True)
    parser.add_argument("--attempt",type=int,required=True);parser.add_argument("--record",type=int,required=True)
    parser.add_argument("--arm",action="store_true",required=True)
    args=parser.parse_args()
    require(1<=args.attempt<=(16 if args.stage=="preflight" else 8) and 1<=args.record<=8,"FINITE_PREPARATION_CONTEXT")
    output=PREFIX+f"{args.stage}{args.attempt:03}-live-cpu-observer{args.record:03}.v1.json"
    require(not(resources.ROOT/output).exists(),"EXCLUSIVE_DIAGNOSTIC_RECORD")
    pins=[]
    for name in (SELF,TEST,"tools/p09/conservative_maintenance.py",process.SELF,process.TEST,fixed.SELF,fixed.TEST,publisher.SELF):
        path=resources.ROOT/name;require(path.is_file() and not path.is_symlink() and not path.is_junction(),"DIRECT_DIAGNOSTIC_SOURCE")
        with path.open("rb") as stream:data=stream.read(65537)
        require(0<len(data)<=65536,"BOUNDED_DIAGNOSTIC_SOURCE")
        pins.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    print(json.dumps(dict(state="ARMED_READ_ONLY_OBSERVER",observer_pid=os.getpid(),stage=args.stage,attempt=args.attempt)),flush=True)
    request=target_request(sys.stdin.readline(129),os.getpid())
    k=host.k;k.GetProcessTimes.argtypes=[ctypes.c_void_p]*5;k.GetProcessTimes.restype=ctypes.c_int
    k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.WaitForSingleObject.restype=ctypes.c_uint32
    handle=None;probe=None;api=None;started=time.monotonic()
    row=dict(state="FAILED_SAME_RUN_PREPARATION_DIAGNOSTIC",stage=args.stage,attempt=args.attempt,target=request,source_pins=pins,
        original_verifier_changed=False,verifier_process_launched_or_terminated=False,raw_process_commands_or_paths_recorded=False,
        product_or_Native_executed=False,GO_authorized=False,accepted_count_delta=0,cause_or_PC_freeze_resolution_established=False,
        process_CPU_intervals_atomic_or_identical_to_original_Guard=False,all_system_CPU_attributed=False)
    try:
        handle=k.OpenProcess(0x1000|0x100000,False,request["pid"]);require(bool(handle),"TARGET_QUERY_AND_SYNCHRONIZE_HANDLE")
        times=[ctypes.c_uint64() for _ in range(4)]
        require(k.GetProcessTimes(handle,*(ctypes.byref(v) for v in times)),"TARGET_CREATION_READ")
        require(times[0].value==request["creation_time_100ns"],"NO_PID_REUSE_OR_OTHER_TARGET")
        def alive():
            value=k.WaitForSingleObject(handle,0);require(value in (0,258),"TARGET_WAIT_STATUS")
            return value==258
        require(alive(),"TARGET_LIVE_AT_ATTACH")
        api=TrackedPDH(fixed.PDH());probe=fixed.Probe(host.processors,api=api)
        sampler=process.ProcessCPU(k,host.times)
        result=watch(alive,sampler.snapshot,process.compare,probe,request["pid"],os.getpid())
        row.update(result,state="RECORDED_SAME_RUN_PREPARATION_CPU_NOT_CAUSAL_OR_RUNTIME_QUALIFICATION")
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:row["error_code"]=error_code(error)
    finally:
        counter_closed=(True if api is None else api.close_partial()) if probe is None else probe.close()
        handle_closed=True if handle is None else bool(k.CloseHandle(handle))
        row.update(cleanup_confirmed=counter_closed and handle_closed,elapsed_seconds=time.monotonic()-started,
            fixed_probe_summary=None if probe is None else probe.summary())
    if not row["cleanup_confirmed"]:row.update(state="FAILED_SAME_RUN_OBSERVER_CLEANUP",error_code="OBSERVER_HANDLES_NOT_CLOSED")
    api=NS(require=require,exact=lambda actual,expected,label:require(actual==expected,label))
    pin=publisher.publish(resources.ROOT,output,row,api)
    print(json.dumps(dict(state=row["state"],pin=pin,sample_count=row.get("sample_count"),stop_reason=row.get("stop_reason"),
        target_terminal_observed=row.get("target_terminal_observed"),cleanup_confirmed=row["cleanup_confirmed"],error_code=row.get("error_code"))))
    return 0 if row["state"].startswith("RECORDED_") else 1


if __name__=="__main__":raise SystemExit(main())
