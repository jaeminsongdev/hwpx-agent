"""Bounded caller counters for two large historical receipts; no payload log."""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
p=k.GetCurrentProcess()
if not (k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import terminal_metadata_pressure_v1 as pressure
import trace_adopted26_metadata_reads_r361 as trace
SELF="tools/p09/trace_run003_large_callers_r365.py"
TRACKED={"implementation/p09/evidence/p09-361-case158-current-runtime-run005.v1.json",
    "implementation/p09/evidence/p09-361-case159-current-runtime-run001.v1.json"}
class Reader(trace.Reader):
    def __init__(self,*args):
        super().__init__(*args);self.callers={}
    def _read(self,name,parse=False):
        pin,raw=super()._read(name,parse=parse)
        if name in TRACKED:
            frame=sys._getframe(1);stack=[]
            for _ in range(7):
                if frame is None:break
                stack.append((Path(frame.f_code.co_filename).name,frame.f_code.co_name,frame.f_lineno))
                frame=frame.f_back
            key=(name,tuple(stack));del frame
            a.require(key in self.callers or len(self.callers)<64,"BOUNDED_LARGE_CALLER_METADATA")
            row=self.callers.setdefault(key,dict(path=name,stack=stack,calls=0,bytes=0))
            row["calls"]+=1;row["bytes"]+=pin["bytes"]
        return pin,raw
def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=Reader(a.c.ROOT,g.check);q.pin(SELF)
        import flat_current_queue_envelope_runtime_v31 as c
        m=c.M;m.base.configure(160);c._env["_execution_requested"]=True
        required,rust=m.binding(q)
        before=trace.summary(q);callers=list(q.callers.values())
        q.finish();g.check(force=True)
        out.update(state="PASS_RUN003_ACTUAL_BINDING_LARGE_CALLERS_NOT_NATIVE_OR_QUEUE",
            source_pins=[q.snapshots[x] for x in (SELF,m.SELF,m.TEST,trace.SELF,pressure.SELF,pressure.TEST)],
            tracked_callers_before_final=callers,binding_reads_before_final=before,
            full_scope_count=len(required),rust_source_count=len(rust),source_pairs=29,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            diagnostic_SELF_not_in_actual_runtime_scope=True,counts_only_no_payload_or_extra_sampler=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-10:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            partial_completed_read_summary=trace.summary(q) if q is not None else None)
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
