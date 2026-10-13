"""Read-only exact whole prepare probe, no acceptance publication or replay."""
import ctypes
import json
from pathlib import Path
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

SELF="tools/p09/probe_case158_envelope_prepare_r339.py"
ROOT=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run005.v1.json",
    bytes=4404465,sha256="34db0892a40886196a3307ba21decfdcb7ecdede4e6e02feb48422636a54ded4")


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,product_or_Native_reexecuted=False,
             queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        import current_envelope_acceptance_prepare_v1 as adapter
        pins=[q.pin(path) for path in (adapter.SELF,SELF,"tools/p09/flat_current_queue_envelope_runtime_v25.py")]
        import flat_current_queue_envelope_runtime_v25 as m
        m.base.configure(158);g.check()
        row,listing,evidence,proof=adapter.prepare(q,ROOT,m)
        q.finish();g.check(force=True)
        out.update(state="PASS_CURRENT_ENVELOPE_FULL_READ_ONLY_PREPARE_NOT_QUEUE_ACCEPTANCE",
            runtime_pin=ROOT,new_code_pins=pins[:2],source_pins=pins,oracle_proof=proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
                            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
