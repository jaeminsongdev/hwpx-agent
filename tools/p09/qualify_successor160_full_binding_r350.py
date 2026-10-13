"""Whole actual160 binding only, original guard75 and no Native/product."""
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
import successor_current_binding_v2 as binding

SELF="tools/p09/qualify_successor160_full_binding_r350.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        current160_product_or_Native_executed=False,prior159_replayed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (SELF,binding.SELF,pressure.SELF,pressure.TEST)]
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;m.base.configure(160);current=m.base.CONFIG
        complete,rust,graph,live,proof=binding.bind(q,controller)
        a.require(m.base.CONFIG is current,"CURRENT160_CONFIG_NOT_TEMPORARILY_SWAPPED")
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL160_FULL_BINDING_PRIVATE159_WHOLE_ORACLE_NOT_CONTROLLER_PREFLIGHT_NATIVE_OR_GO",
            source_pins=pins,complete_scope_count=len(complete),rust_source_count=len(rust),
            source_pairs=len(live.descriptors()),manifest_pin=dict(live.manifest_pin),
            default_current160_CONFIG_mutated=False,binding_proof=proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
